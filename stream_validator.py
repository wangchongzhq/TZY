#!/usr/bin/env python3
"""
流媒体URL增强验证模块
统一为 IPTV.py 与 IPTVTXT.py 提供URL可访问性 + 流可播放性验证。

设计原则:
1. HTTP/HTTPS: HEAD 失败 → 回退 GET + stream=True 读取前若干字节验证
   - m3u8: 检测 #EXTM3U
   - TS: 检测 0x47 同步字节
   - HTML 错误页: 排除
2. UDP/RTMP/RTP: 端口可达性测试 (TCP socket connect 等价)
3. retries 参数真正生效
4. 可选 ffprobe 深度验证 (作为高级验证层)
5. 黑名单关键词可由配置注入，使用词边界正则避免误杀合法域名
"""

import re
import socket
import logging
import subprocess
import shutil
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# 请求头
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Range': 'bytes=0-1023',  # 只请求前1KB，验证流内容
}

# 状态码白名单 (移除 304，HEAD 不应返回 304)
VALID_STATUS_CODES = {200, 201, 202, 203, 204, 206, 301, 302, 303, 307, 308}

# 无效域名/风险模式
INVALID_DOMAINS = [
    '127.0.0.1', 'localhost', 'example.com', 'test.com',
    '0.0.0.0', '255.255.255.255',
]

PRIVATE_IP_PREFIXES = ('10.', '192.168.', '172.16.', '172.17.', '172.18.',
                       '172.19.', '172.20.', '172.21.', '172.22.',
                       '172.23.', '172.24.', '172.25.', '172.26.',
                       '172.27.', '172.28.', '172.29.', '172.30.',
                       '172.31.', '169.254.')

# 快速预过滤：明显无效的URL子串
INVALID_SUBSTR_PATTERNS = [
    'deadlink', 'expired', 'notfound', 'suspended', 'blocked',
    'undefined', 'null',  # 编程错误
]

# 默认黑名单关键词 (可由 config 注入覆盖)
DEFAULT_BLACKLIST_KEYWORDS = ['freetv', 'migu', 'catvod', 'mgtv']
# 默认黑名单协议
DEFAULT_BLACKLIST_PROTOCOLS = ['rtsp://']
# 默认黑名单独立词 (使用词边界，避免误杀 livestream)
DEFAULT_BLACKLIST_WORDS = ['stream', 'streaming']

# 编译后的词边界正则
_BLACKLIST_WORD_RE = re.compile(
    r'(?<![a-z])(?:' + '|'.join(DEFAULT_BLACKLIST_WORDS) + r')(?![a-z])',
    re.IGNORECASE
)

# 流类型识别
M3U8_MAGIC = b'#EXTM3U'
TS_SYNC_BYTE = 0x47


def _is_private_ip(hostname):
    """判断 hostname 是否为私有/本地IP"""
    if not hostname:
        return False
    host = hostname.lower()
    if host in INVALID_DOMAINS:
        return True
    if host.startswith(PRIVATE_IP_PREFIXES):
        return True
    if host.endswith('.local') or host.endswith('.internal'):
        return True
    return False


def _prefilter_url(url):
    """快速预过滤URL，返回 (is_valid, reason)"""
    if not url or not isinstance(url, str):
        return False, "URL为空或格式错误"
    url = url.strip()
    if not url:
        return False, "URL为空"
    if url.startswith('#'):
        return False, "URL为注释"
    if '://' not in url and not url.startswith('//'):
        return False, "URL缺少协议"

    url_lower = url.lower()
    for pat in INVALID_SUBSTR_PATTERNS:
        if pat in url_lower:
            return False, f"包含无效标识: {pat}"

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
    except Exception:
        return False, "URL解析失败"

    if not hostname:
        return False, "URL缺少主机名"

    if _is_private_ip(hostname):
        return False, "私有/本地地址"

    return True, "预筛选通过"


def _verify_stream_content(chunk):
    """验证读取到的字节是否为有效的流数据
    返回 (is_valid, reason)
    """
    if not chunk:
        return False, "响应为空"

    # m3u8 文本流
    if chunk.startswith(M3U8_MAGIC):
        return True, "m3u8流(#EXTM3U头)"

    # TS 流: 同步字节 0x47 每 188 字节出现
    if chunk[0] == TS_SYNC_BYTE:
        return True, "MPEG-TS流(0x47同步字节)"

    # 非 ASCII 二进制 → 可能是 TS / FLV 等二进制流，宽松放行
    if chunk[0] >= 0x80:
        return True, "二进制流"

    # 检测 HTML 错误页
    head = chunk[:256].lower()
    if b'<html' in head or b'<!doctype' in head:
        return False, "返回HTML错误页"
    if b'<error' in head or b'404' in head or b'not found' in head:
        return False, "返回错误页内容"

    # 其他文本但非 m3u8 → 不可播放
    return False, "响应非流媒体内容"


def _check_http_url(url, session, timeout, retries):
    """HTTP/HTTPS URL 检测: HEAD 失败回退 GET + 读取字节验证"""
    last_err = None
    for attempt in range(retries + 1):
        try:
            # 1. HEAD 请求快速验证
            resp = session.head(url, timeout=timeout, allow_redirects=True)
            if resp.status_code in VALID_STATUS_CODES:
                # HEAD 成功，但仍需 GET 验证流内容(防HTML错误页)
                pass
            elif resp.status_code in (405, 501):
                # 方法不允许 → 直接走 GET
                resp = session.get(
                    url, timeout=timeout, stream=True,
                    headers=DEFAULT_HEADERS, allow_redirects=True
                )
                if resp.status_code not in VALID_STATUS_CODES:
                    return False, f"HTTP {resp.status_code}"
            else:
                last_err = f"HTTP {resp.status_code}"
                if attempt < retries:
                    continue
                return False, last_err

            # 2. GET 流验证(读取前1KB)
            get_resp = session.get(
                url, timeout=timeout, stream=True,
                headers=DEFAULT_HEADERS, allow_redirects=True
            )
            if get_resp.status_code not in VALID_STATUS_CODES:
                return False, f"GET HTTP {get_resp.status_code}"

            chunk = next(get_resp.iter_content(chunk_size=1024), b'')
            get_resp.close()
            return _verify_stream_content(chunk)

        except requests.exceptions.Timeout:
            last_err = "超时"
            if attempt < retries:
                continue
        except requests.exceptions.SSLError:
            last_err = "SSL错误"
            if attempt < retries:
                continue
        except requests.exceptions.ConnectionError:
            last_err = "连接错误"
            if attempt < retries:
                continue
        except requests.exceptions.RequestException as e:
            last_err = f"请求错误: {str(e)[:40]}"
            if attempt < retries:
                continue
        except Exception as e:
            last_err = f"未知错误: {str(e)[:30]}"
            if attempt < retries:
                continue

    return False, last_err or "检测失败"


def _check_udp_rtmp_url(url, timeout):
    """UDP/RTMP/RTP 协议: 端口可达性测试"""
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "URL解析失败"

    if not parsed.hostname or not parsed.port:
        return False, "缺少主机名或端口"

    proto = parsed.scheme.lower()
    # UDP 协议走 UDP socket
    if proto == 'udp':
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(timeout)
                s.connect((parsed.hostname, parsed.port))
            return True, "UDP端口可达"
        except socket.timeout:
            return False, "UDP端口超时"
        except OSError as e:
            return False, f"UDP端口错误: {e}"
    # RTMP/RTP 走 TCP 探测 (实际RTMP是基于TCP的，RTP常用UDP但TCP探测可达性作为粗筛)
    else:
        try:
            with socket.create_connection(
                (parsed.hostname, parsed.port), timeout=timeout
            ) as s:
                pass
            return True, f"{proto.upper()}端口可达"
        except socket.timeout:
            return False, f"{proto.upper()}端口超时"
        except OSError as e:
            return False, f"{proto.upper()}端口错误: {e}"


def _ffprobe_available():
    """检查系统是否安装ffprobe"""
    return shutil.which('ffprobe') is not None


def ffprobe_check(url, timeout=10):
    """使用ffprobe进行真正的流可播放性验证
    返回 (is_valid, reason)
    """
    if not _ffprobe_available():
        return False, "ffprobe未安装"

    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_streams', '-show_format',
            '-of', 'csv=p=0', '-read_size', '8192',
            '-timeout', str(int(timeout * 1000000)),  # 微秒
            url
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout + 5
        )
        if result.returncode == 0 and result.stdout.strip():
            return True, "ffprobe验证通过"
        return False, f"ffprobe失败: {result.stderr[:60]}"
    except subprocess.TimeoutExpired:
        return False, "ffprobe超时"
    except Exception as e:
        return False, f"ffprobe异常: {str(e)[:30]}"


def is_url_blacklisted(url, custom_keywords=None, custom_protocols=None,
                       custom_words=None):
    """统一黑名单匹配(替代 IPTV.py / IPTVTXT.py 中重复实现)

    Args:
        url: 待检测URL
        custom_keywords: 自定义关键词列表 (子串匹配)
        custom_protocols: 自定义协议黑名单 (如 ['rtsp://'])
        custom_words: 自定义独立词列表 (词边界匹配)
    Returns: True 表示在黑名单中(应跳过)
    """
    if not url:
        return True
    url_lower = url.lower()

    keywords = custom_keywords if custom_keywords is not None else DEFAULT_BLACKLIST_KEYWORDS
    protocols = custom_protocols if custom_protocols is not None else DEFAULT_BLACKLIST_PROTOCOLS

    for proto in protocols:
        if proto in url_lower:
            return True
    for kw in keywords:
        if kw and kw in url_lower:
            return True

    if custom_words is not None:
        word_re = re.compile(
            r'(?<![a-z])(?:' + '|'.join(custom_words) + r')(?![a-z])',
            re.IGNORECASE
        )
    else:
        word_re = _BLACKLIST_WORD_RE
    if word_re.search(url_lower):
        return True

    return False


def enhanced_check_url(url, timeout=2, retries=1, session=None,
                       use_ffprobe=False, ffprobe_timeout=10):
    """增强版URL验证(替代 check_url)

    与原 check_url 接口兼容，但增加流内容验证与重试机制。
    返回 bool
    """
    # 1. 预过滤
    is_valid, _ = _prefilter_url(url)
    if not is_valid:
        return False

    # 2. 协议分发
    if url.startswith(('http://', 'https://')):
        if session is None:
            session = requests.Session()
            session.headers.update(DEFAULT_HEADERS)
        ok, _ = _check_http_url(url, session, timeout, retries)
        if not ok and use_ffprobe:
            # HTTP 检测失败时尝试 ffprobe 深度验证(可能源对 HEAD/GET 不友好)
            ok, _ = ffprobe_check(url, ffprobe_timeout)
            if ok:
                return True
            return False
        return ok

    # 非HTTP协议
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme.lower() not in ('udp', 'rtmp', 'rtp'):
        return False

    ok, _ = _check_udp_rtmp_url(url, timeout)
    if not ok and use_ffprobe:
        ok, _ = ffprobe_check(url, ffprobe_timeout)
    return ok


def check_url_detail(url, timeout=2, retries=1, session=None,
                     use_ffprobe=False, ffprobe_timeout=10):
    """返回详细信息的版本 (用于日志/调试)
    返回 dict: {'valid': bool, 'reason': str, 'method': str}
    """
    is_valid, reason = _prefilter_url(url)
    if not is_valid:
        return {'valid': False, 'reason': reason, 'method': 'prefilter'}

    if url.startswith(('http://', 'https://')):
        if session is None:
            session = requests.Session()
            session.headers.update(DEFAULT_HEADERS)
        ok, detail = _check_http_url(url, session, timeout, retries)
        if not ok and use_ffprobe:
            ok2, detail2 = ffprobe_check(url, ffprobe_timeout)
            if ok2:
                return {'valid': True, 'reason': detail2, 'method': 'ffprobe'}
            return {'valid': False, 'reason': detail2, 'method': 'ffprobe_fallback'}
        return {'valid': ok, 'reason': detail, 'method': 'http_get_verify'}

    try:
        parsed = urlparse(url)
    except Exception:
        return {'valid': False, 'reason': 'URL解析失败', 'method': 'parse_error'}

    if parsed.scheme.lower() not in ('udp', 'rtmp', 'rtp'):
        return {'valid': False, 'reason': f"不支持协议: {parsed.scheme}",
                'method': 'protocol_skip'}

    ok, detail = _check_udp_rtmp_url(url, timeout)
    if not ok and use_ffprobe:
        ok2, detail2 = ffprobe_check(url, ffprobe_timeout)
        if ok2:
            return {'valid': True, 'reason': detail2, 'method': 'ffprobe'}
        return {'valid': False, 'reason': detail2, 'method': 'ffprobe_fallback'}
    return {'valid': ok, 'reason': detail, 'method': 'port_reachability'}


def batch_check_detail(urls, timeout=2, retries=1, max_workers=32,
                        use_ffprobe=False, session=None, show_progress=False):
    """批量检测，返回详细结果列表"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time as _time

    results = []
    total = len(urls)
    start = _time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(
                check_url_detail, url, timeout, retries, session, use_ffprobe
            ): url for url in urls
        }
        for i, future in enumerate(as_completed(future_to_url), 1):
            try:
                results.append(future.result())
            except Exception as e:
                results.append({
                    'valid': False,
                    'reason': f"检测异常: {str(e)[:30]}",
                    'method': 'error',
                    'url': future_to_url[future]
                })
            if show_progress and i % 100 == 0:
                elapsed = _time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                logger.info(f"进度: {i}/{total} - {rate:.1f} URL/s")
    return results
