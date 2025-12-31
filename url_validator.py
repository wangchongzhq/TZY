# -*- coding: utf-8 -*-
"""统一的URL验证模块"""

import re
import requests
from typing import Optional, Tuple
from urllib.parse import urlparse
from urllib3.util.retry import Retry


# URL正则表达式
URL_REGEX = re.compile(
    r'^((?:http|https|rtmp|rtsp|udp|rtp)://)?'  # 协议
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 域名...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...或者IP
    r'(?::\d+)?'  # 可选的端口
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


# 全局会话对象
session = requests.Session()

# 设置重试策略
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    backoff_factor=1,
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
http_adapter = requests.adapters.HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=50,
    pool_maxsize=50
)
session.mount("http://", http_adapter)
session.mount("https://", http_adapter)


def is_valid_url_format(url: str) -> bool:
    """
    检查URL格式是否正确
    
    Args:
        url: 要检查的URL
        
    Returns:
        bool: URL格式是否正确
    """
    if not url or not isinstance(url, str):
        return False
    return URL_REGEX.match(url.strip()) is not None


def is_http_url(url: str) -> bool:
    """
    检查是否为HTTP/HTTPS URL
    
    Args:
        url: 要检查的URL
        
    Returns:
        bool: 是否为HTTP/HTTPS URL
    """
    return url.startswith(('http://', 'https://'))


def is_streaming_url(url: str) -> bool:
    """
    检查是否为流媒体URL
    
    Args:
        url: 要检查的URL
        
    Returns:
        bool: 是否为流媒体URL
    """
    streaming_protocols = ['http://', 'https://', 'rtmp://', 'rtsp://', 'udp://', 'rtp://']
    return any(url.startswith(protocol) for protocol in streaming_protocols)


def check_url_status(url: str, timeout: int = 5, retries: int = 1) -> Tuple[bool, Optional[str]]:
    """
    检查URL可访问状态
    
    Args:
        url: 要检查的URL
        timeout: 超时时间（秒）
        retries: 重试次数
        
    Returns:
        Tuple[bool, Optional[str]]: (是否可访问, 错误信息)
    """
    if not is_valid_url_format(url):
        return False, "URL格式错误"
    
    # 对于非HTTP/HTTPS协议的URL，直接返回True
    if not is_http_url(url):
        return True, None
    
    for attempt in range(retries + 1):
        try:
            # 使用HEAD请求以避免下载整个文件
            response = session.head(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={'Range': 'bytes=0-0'}  # 只请求文件的第一个字节
            )
            
            if response.status_code < 400:
                return True, None
            else:
                error_msg = f"HTTP {response.status_code}"
                if attempt < retries:
                    continue
                return False, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = "请求超时"
            if attempt < retries:
                continue
            return False, error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "连接失败"
            if attempt < retries:
                continue
            return False, error_msg
        except requests.exceptions.SSLError:
            error_msg = "SSL证书错误"
            if attempt < retries:
                continue
            return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"请求错误: {str(e)}"
            if attempt < retries:
                continue
            return False, error_msg
    
    return False, "未知错误"


def check_url(url: str, timeout: int = 5, retries: int = 1) -> bool:
    """
    简化的URL检查函数，向后兼容
    
    Args:
        url: 要检查的URL
        timeout: 超时时间（秒）
        retries: 重试次数
        
    Returns:
        bool: URL是否可访问
    """
    is_accessible, _ = check_url_status(url, timeout, retries)
    return is_accessible


def normalize_url(url: str) -> str:
    """
    规范化URL（去除末尾的斜杠等）
    
    Args:
        url: 原始URL
        
    Returns:
        str: 规范化后的URL
    """
    if not url:
        return url
    
    # 去除末尾的斜杠（除了协议部分）
    parsed = urlparse(url)
    normalized = parsed._replace(
        path=parsed.path.rstrip('/') if parsed.path != '/' else '/',
        query=parsed.query.rstrip('&') if parsed.query else ''
    ).geturl()
    
    return normalized


def get_domain_from_url(url: str) -> Optional[str]:
    """
    从URL中提取域名
    
    Args:
        url: 输入的URL
        
    Returns:
        Optional[str]: 域名，如果提取失败则返回None
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return None