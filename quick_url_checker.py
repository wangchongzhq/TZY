#!/usr/bin/env python3
"""
轻量级URL快速检测模块
借鉴validator的有效性验证方法，设计高效的URL预筛选和检测机制
"""

import re
import time
import requests
import socket
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FuturesTimeoutError
import logging

logger = logging.getLogger(__name__)

# 预编译正则表达式提高性能
URL_REGEX = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

# 无效域名模式
INVALID_DOMAINS = [
    'example.com', 'test.com', 'localhost', '127.0.0.1',
    '192.168.', '10.', '172.', '169.254.',  # 私有IP
    '0.0.0.0', '255.255.255.255'  # 特殊地址
]

# 高风险URL模式（容易无效或不可靠）
RISKY_PATTERNS = [
    r'\.tk$', r'\.ml$', r'\.cf$',  # 免费域名
    r'timeout', r'error', r'fail',  # 错误相关
    r'\${2,}',  # 多个美元符号
    r'undefined', r'null',  # 编程错误
    r'localhost', r'127\.0\.0\.1'  # 本地地址
]

# 可信域名白名单（降低检测严格度）
TRUSTED_DOMAINS = [
    'cctv.cn', 'cctv.com', 'cctv.net.cn',
    'hnrtv.com', 'sdrtv.com', 'jsrtv.com', 'zjrtv.com',
    'btv.org.cn', 'jstv.cn', 'gdrtv.com', 'xjrtv.com',
    'tianjinweishi.com', 'ahapp.tv', 'hunantv.com', 'lntv.cn', 'hljtv.cn',
    'jilinweishi.com', 'nmtv.cn', 'nxtv.cn', 'sxrtv.cn', 'sxtv.cn',
    'gsrtv.cn', 'qhrtv.cn', 'xjrtv.cn', 'xzrtv.com', 'xjtv.com.cn'
]

# HTTP状态码白名单（认为是有效的）
# 注：移除304(Not Modified)，HEAD请求不应返回304，对HEAD返回304视作异常
VALID_STATUS_CODES = {200, 201, 202, 203, 204, 206, 301, 302, 303, 307, 308}

# 危险的URL模式（跳过检测）
DANGEROUS_PATTERNS = [
    r'<script', r'javascript:', r'vbscript:',  # XSS
    r'file://', r'ftp://',  # 非HTTP协议
    r'\${.*}', r'\(.*\)',  # 模板变量
]

def classify_stream_chunk(chunk):
    """分类GET读到的流首字节。
    策略：识别已知可播封装 + 明确拒绝错误页，其余无法识别但非错误页的一律放行，
    避免用格式白名单误杀 FLV/fMP4 等合法直播封装。
    返回 (is_valid, reason)
    """
    if not chunk:
        return False, "响应体为空"

    # m3u8：容忍前导 BOM/空白/换行
    if chunk.lstrip(b'\xef\xbb\xbf \t\r\n').startswith(b'#EXTM3U'):
        return True, "m3u8流(#EXTM3U头)"

    # FLV: "FLV" + 版本号(0x01)
    if len(chunk) >= 4 and chunk[:3] == b'FLV' and chunk[3] == 0x01:
        return True, "FLV流"

    # fMP4: [4字节size]["ftyp"/"styp"/"moov"等box类型]
    if len(chunk) >= 8 and chunk[4:8] in (
        b'ftyp', b'styp', b'moov', b'moof', b'mdat', b'free', b'skip'
    ):
        return True, "fMP4流"

    # MPEG-TS: 0x47 同步字节
    if chunk[0] == 0x47:
        return True, "MPEG-TS流(0x47同步字节)"

    # 其他高位二进制(可能是未知二进制封装)
    if chunk[0] >= 0x80:
        return True, "二进制流"

    # 以下为 ASCII 可打印内容：只明确拒绝错误页/错误JSON，其余放行
    head = chunk[:512].lower()
    if b'<html' in head or b'<!doctype' in head or b'<?xml' in head:
        return False, "返回HTML/XML错误页"
    if b'<error' in head or b'<message' in head or b'<rescode' in head:
        return False, "返回错误标记"
    # 合法流首字节不会是 { 或 [，可安全判定 JSON 错误响应
    if chunk[:1] in (b'{', b'[') and (
        b'error' in head or b'"code":404' in head or b'404' in head
        or b'fail' in head or b'denied' in head
    ):
        return False, "返回JSON错误响应"
    if b'404 not found' in head or b'not found' in head \
       or b'access denied' in head or b'forbidden' in head or b'bad request' in head:
        return False, "返回文本错误页"

    # 非明确错误页：放行(宁可保留少量不可播，也不误杀未知封装的有效流)
    return True, "可访问内容(未识别封装,放行)"


class QuickURLChecker:
    """轻量级URL快速检测器"""
    
    def __init__(self, timeout=2, max_workers=32, enable_dns_check=True,
                 total_timeout=None, get_read_timeout=1.5):
        self.timeout = timeout
        self.max_workers = max_workers
        self.enable_dns_check = enable_dns_check
        # 批量检测的墙钟总预算(秒)，None表示不限；防止慢流拖尾撑爆CI job超时
        self.total_timeout = total_timeout
        # GET读取流首字节的read超时(秒)，独立于connect超时，收紧以抑制慢直播流拖尾
        self.get_read_timeout = min(get_read_timeout, timeout)
        
        # 创建优化的Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Range': 'bytes=0-0'  # 只请求第一个字节，减少流量
        })
        
        # 配置连接池
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max_workers,
            pool_maxsize=max_workers,
            max_retries=0  # 不自动重试，手动控制
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 预编译正则表达式
        self._compile_patterns()
    
    def _compile_patterns(self):
        """预编译所有正则表达式模式"""
        self.risky_regex = [re.compile(pattern, re.IGNORECASE) for pattern in RISKY_PATTERNS]
        self.dangerous_regex = [re.compile(pattern, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS]
        self.trusted_regex = [re.compile(f'.*{domain}.*') for domain in TRUSTED_DOMAINS]
    
    def quick_filter(self, url):
        """快速预筛选URL"""
        if not url or not isinstance(url, str):
            return False, "URL为空或格式错误"
        
        url = url.strip()
        if not url:
            return False, "URL为空"
        
        # 基本格式检查
        if not URL_REGEX.match(url):
            return False, "URL格式不正确"
        
        # 检查危险模式
        for pattern in self.dangerous_regex:
            if pattern.search(url):
                return False, f"发现危险模式: {pattern.pattern}"
        
        # 提取域名
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
        except Exception:
            return False, "URL解析失败"
        
        # 检查无效域名
        for invalid in INVALID_DOMAINS:
            if domain.startswith(invalid) or invalid in domain:
                return False, f"包含无效域名: {invalid}"
        
        # 检查风险模式
        for pattern in self.risky_regex:
            if pattern.search(url):
                return False, f"包含风险模式: {pattern.pattern}"
        
        # DNS预检查（可选）
        if self.enable_dns_check:
            try:
                socket.gethostbyname(parsed.hostname)
            except (socket.gaierror, socket.herror):
                return False, "DNS解析失败"
        
        return True, "预筛选通过"
    
    def check_http_url(self, url):
        """检测HTTP/HTTPS URL - 直接GET读取流首字节验证

        废弃HEAD：直播CDN对HEAD兼容性差(常返回403/404/405但GET正常出流)，
        且无论HEAD成败都需GET验证内容，故直接GET一次拿到状态码+内容，更准且不增加请求。
        """
        try:
            resp = self.session.get(
                url,
                timeout=(self.timeout, self.get_read_timeout),
                stream=True,
                headers={'Range': 'bytes=0-1023'},
                allow_redirects=True
            )

            if resp.status_code not in VALID_STATUS_CODES:
                return False, f"HTTP {resp.status_code}"

            chunk = next(resp.iter_content(chunk_size=1024), b'')
            resp.close()
            return classify_stream_chunk(chunk)

        except requests.exceptions.Timeout:
            return False, "连接超时"
        except requests.exceptions.ConnectionError:
            return False, "连接错误"
        except requests.exceptions.TooManyRedirects:
            return False, "重定向过多"
        except requests.exceptions.RequestException as e:
            return False, f"请求错误: {str(e)[:50]}"
        except Exception as e:
            return False, f"未知错误: {str(e)[:30]}"
    
    def is_trusted_domain(self, url):
        """检查是否为可信域名"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            for trusted_pattern in self.trusted_regex:
                if trusted_pattern.search(domain):
                    return True
            return False
        except Exception:
            return False
    
    def check_url(self, url):
        """检测单个URL"""
        # 快速预筛选
        is_valid, reason = self.quick_filter(url)
        if not is_valid:
            return {
                'url': url,
                'valid': False,
                'reason': reason,
                'method': 'prefilter'
            }
        
        # 对于可信域名，使用更宽松的检测
        # 注：不再跳过流内容验证，可信域名下具体频道URL仍可能失效
        if self.is_trusted_domain(url):
            # 可信域名放宽超时到一半，但仍走完整HTTP+流内容验证
            try:
                is_valid, reason = self.check_http_url(url)
                return {
                    'url': url,
                    'valid': is_valid,
                    'reason': f'可信域名-{reason}',
                    'method': 'trusted_http_verify'
                }
            except Exception as e:
                return {
                    'url': url,
                    'valid': False,
                    'reason': f'可信域名检测异常: {str(e)[:30]}',
                    'method': 'trusted_error'
                }
        
        # 标准HTTP检测
        if url.startswith(('http://', 'https://')):
            is_valid, reason = self.check_http_url(url)
            return {
                'url': url,
                'valid': is_valid,
                'reason': reason,
                'method': 'http_check'
            }
        else:
            # 非HTTP协议直接返回有效（无法通过HTTP检测）
            return {
                'url': url,
                'valid': True,
                'reason': '非HTTP协议',
                'method': 'protocol_skip'
            }
    
    def batch_check(self, urls, show_progress=True):
        """批量检测URL

        若设置 total_timeout，则采用墙钟总预算：超时后未完成的URL一律标记为无效，
        保证检测阶段有界返回，避免慢流拖尾撑爆CI job超时。
        """
        total = len(urls)
        results = [None] * total

        logger.info(f"开始批量检测 {total} 个URL...")
        start_time = time.time()
        deadline = (start_time + self.total_timeout) if self.total_timeout else None
        timed_out = False

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务，记录 future -> 输入索引(保证结果严格按输入顺序返回)
            future_to_idx = {
                executor.submit(self.check_url, url): idx
                for idx, url in enumerate(urls)
            }

            remaining = (deadline - time.time()) if deadline else None
            done_count = 0
            try:
                for future in as_completed(future_to_idx, timeout=remaining):
                    idx = future_to_idx[future]
                    try:
                        results[idx] = future.result()
                    except Exception as e:
                        results[idx] = {
                            'url': urls[idx],
                            'valid': False,
                            'reason': f"检测异常: {str(e)[:30]}",
                            'method': 'error'
                        }
                    done_count += 1
                    if show_progress and done_count % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = done_count / elapsed if elapsed > 0 else 0
                        logger.info(f"进度: {done_count}/{total} ({done_count/total*100:.1f}%) - 速率: {rate:.1f} URL/s")
            except FuturesTimeoutError:
                timed_out = True

            # 总预算耗尽：未完成任务标记无效(单任务仍有requests timeout兜底，shutdown不会久挂)
            pending_count = 0
            if timed_out:
                for f, idx in future_to_idx.items():
                    if not f.done():
                        f.cancel()
                        results[idx] = {
                            'url': urls[idx],
                            'valid': False,
                            'reason': '超出批量检测总预算',
                            'method': 'batch_timeout'
                        }
                        pending_count += 1
                logger.warning(
                    f"批量检测达到总预算 {self.total_timeout}s，"
                    f"{pending_count}/{total} 个URL未完成，已标记无效"
                )

        elapsed = time.time() - start_time
        valid_count = sum(1 for r in results if r and r['valid'])
        pct = valid_count/total*100 if total else 0
        logger.info(f"检测完成: {total} 个URL，{valid_count} 个有效 ({pct:.1f}%)，耗时: {elapsed:.2f}秒")

        return results

def create_quick_checker(timeout=2, max_workers=32, enable_dns_check=True,
                         total_timeout=None, get_read_timeout=1.5):
    """创建快速检测器实例"""
    return QuickURLChecker(
        timeout=timeout,
        max_workers=max_workers,
        enable_dns_check=enable_dns_check,
        total_timeout=total_timeout,
        get_read_timeout=get_read_timeout
    )

def quick_check_urls(urls, timeout=2, max_workers=32, enable_dns_check=True,
                     total_timeout=None):
    """快速检测URL列表的便捷函数"""
    checker = create_quick_checker(timeout, max_workers, enable_dns_check,
                                   total_timeout=total_timeout)
    return checker.batch_check(urls)

if __name__ == "__main__":
    # 测试代码
    import sys
    
    test_urls = [
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/404", 
        "https://httpbin.org/delay/1",
        "invalid_url",
        "https://www.cctv.cn",
        "http://example.com/test.m3u8"
    ]
    
    print("=== 快速URL检测测试 ===")
    results = quick_check_urls(test_urls, timeout=3)
    
    for result in results:
        status = "✅" if result['valid'] else "❌"
        print(f"{status} {result['url']} - {result['reason']}")