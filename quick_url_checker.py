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
    'hnrtv.com', 'sdrtv.com', 'jsrtv.com', 'zjrtv.com', 'jsrtv.com',
    'btv.org.cn', 'jstv.cn', 'hnrtv.com', 'gdrtv.com', 'xjrtv.com',
    'tianjinweishi.com', 'ahapp.tv', 'hunantv.com', 'lntv.cn', 'hljtv.cn',
    'jilinweishi.com', 'nmtv.cn', 'nxtv.cn', 'sxrtv.cn', 'sxtv.cn',
    'gsrtv.cn', 'qhrtv.cn', 'xjrtv.cn', 'xzrtv.com', 'xjtv.com.cn'
]

# HTTP状态码白名单（认为是有效的）
VALID_STATUS_CODES = {200, 201, 202, 203, 204, 206, 301, 302, 303, 304, 307, 308}

# 危险的URL模式（跳过检测）
DANGEROUS_PATTERNS = [
    r'<script', r'javascript:', r'vbscript:',  # XSS
    r'file://', r'ftp://',  # 非HTTP协议
    r'\${.*}', r'\(.*\)',  # 模板变量
]

class QuickURLChecker:
    """轻量级URL快速检测器"""
    
    def __init__(self, timeout=2, max_workers=32, enable_dns_check=True):
        self.timeout = timeout
        self.max_workers = max_workers
        self.enable_dns_check = enable_dns_check
        
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
        """检测HTTP/HTTPS URL"""
        try:
            # 尝试HEAD请求
            response = self.session.head(
                url, 
                timeout=self.timeout, 
                allow_redirects=True
            )
            
            # 检查状态码
            if response.status_code in VALID_STATUS_CODES:
                return True, f"HTTP {response.status_code}"
            
            # 如果HEAD失败，尝试GET请求（限制响应大小）
            if response.status_code in (405, 501):  # 方法不允许
                response = self.session.get(
                    url, 
                    timeout=self.timeout,
                    stream=True,
                    headers={'Range': 'bytes=0-1023'}  # 只获取1KB
                )
                
                if response.status_code in VALID_STATUS_CODES:
                    return True, f"HTTP GET {response.status_code}"
            
            return False, f"HTTP状态码: {response.status_code}"
            
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
        if self.is_trusted_domain(url):
            # 可信域名只做基础检测
            try:
                response = self.session.head(url, timeout=self.timeout//2, allow_redirects=True)
                if response.status_code < 400:
                    return {
                        'url': url,
                        'valid': True,
                        'reason': '可信域名快速通过',
                        'method': 'trusted_fast'
                    }
            except Exception:
                pass
        
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
        """批量检测URL"""
        results = []
        total = len(urls)
        
        logger.info(f"开始批量检测 {total} 个URL...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(self.check_url, url): url 
                for url in urls
            }
            
            # 处理结果
            for i, future in enumerate(as_completed(future_to_url), 1):
                try:
                    result = future.result()
                    results.append(result)
                    
                    if show_progress and i % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = i / elapsed if elapsed > 0 else 0
                        logger.info(f"进度: {i}/{total} ({i/total*100:.1f}%) - 速率: {rate:.1f} URL/s")
                        
                except Exception as e:
                    url = future_to_url[future]
                    results.append({
                        'url': url,
                        'valid': False,
                        'reason': f"检测异常: {str(e)[:30]}",
                        'method': 'error'
                    })
        
        elapsed = time.time() - start_time
        valid_count = sum(1 for r in results if r['valid'])
        logger.info(f"检测完成: {total} 个URL，{valid_count} 个有效 ({valid_count/total*100:.1f}%)，耗时: {elapsed:.2f}秒")
        
        return results

def create_quick_checker(timeout=2, max_workers=32, enable_dns_check=True):
    """创建快速检测器实例"""
    return QuickURLChecker(
        timeout=timeout,
        max_workers=max_workers,
        enable_dns_check=enable_dns_check
    )

def quick_check_urls(urls, timeout=2, max_workers=32, enable_dns_check=True):
    """快速检测URL列表的便捷函数"""
    checker = create_quick_checker(timeout, max_workers, enable_dns_check)
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