#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一网络请求处理模块
功能：提供安全、可靠的网络请求功能，包括重试机制、错误处理和缓存支持
"""

import requests
import time
import asyncio
import aiohttp
from typing import Optional, Dict, List, Any
from urllib3.exceptions import InsecureRequestWarning
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入日志配置
from .logging_config import get_logger, log_exception, log_performance
# 导入配置管理
from .config import get_config

# 禁用不安全请求警告
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# 获取日志记录器
logger = get_logger(__name__)

# 从配置中获取网络配置
NETWORK_CONFIG = get_config('network', {
    'timeout': 10,
    'max_retries': 3,
    'request_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36'
    }
})

# 默认请求头
DEFAULT_HEADERS = NETWORK_CONFIG.get('request_headers', {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36'
})

# 安全请求配置
SAFE_REQUEST_CONFIG = {
    'verify': True,  # 验证SSL证书
    'timeout': NETWORK_CONFIG.get('timeout', 10),
    'headers': DEFAULT_HEADERS.copy(),
    'allow_redirects': True,
    'max_redirects': 5
}

def fetch_content(url: str, retries: Optional[int] = None, timeout: Optional[int] = None, headers: Optional[Dict] = None, verify: bool = True) -> Optional[str]:
    """
    统一的网络请求函数，包含重试机制
    
    参数:
        url: 要请求的URL
        retries: 重试次数（默认从配置获取）
        timeout: 超时时间（秒，默认从配置获取）
        headers: 自定义请求头
        verify: 是否验证SSL证书
        
    返回:
        Optional[str]: 请求成功返回响应内容，失败返回None
    """
    # 从配置获取默认值
    if retries is None:
        retries = NETWORK_CONFIG.get('max_retries', 3)
    if timeout is None:
        timeout = NETWORK_CONFIG.get('timeout', 10)
    if headers is None:
        headers = DEFAULT_HEADERS.copy()
    
    # 针对特定域名的特殊处理
    if 'ghfast.top' in url:
        # 对ghfast.top域名设置更短的超时和更少的重试次数
        timeout = 5
        retries = 1
    
    config = {
        'headers': headers,
        'timeout': timeout,
        'verify': verify,
        'allow_redirects': True
    }
    
    for attempt in range(retries):
        try:
            start_time = time.time()
            response = requests.get(url, **config)
            response.raise_for_status()  # 抛出HTTP错误
            response.encoding = 'utf-8'  # 确保使用UTF-8编码
            
            # 计算请求耗时
            elapsed_time = time.time() - start_time
            logger.debug(f"请求成功 {url} (尝试 {attempt+1}/{retries})，耗时: {elapsed_time:.2f}秒")
            
            # 记录性能信息
            log_performance(logger, "网络请求", elapsed_time, url=url, attempt=attempt+1, status_code=response.status_code)
            
            return response.text
            
        except requests.exceptions.Timeout:
            logger.error(f"请求超时 {url} (尝试 {attempt+1}/{retries})")
            
            # 指数退避
            if attempt < retries - 1:
                backoff_time = 2 ** attempt
                logger.info(f"等待 {backoff_time}秒后重试...")
                time.sleep(backoff_time)
        
        except requests.exceptions.ConnectionError:
            logger.error(f"连接错误 {url} (尝试 {attempt+1}/{retries})")
            
            # 指数退避
            if attempt < retries - 1:
                backoff_time = 2 ** attempt
                logger.info(f"等待 {backoff_time}秒后重试...")
                time.sleep(backoff_time)
        
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            logger.error(f"HTTP错误 {status_code} {url} (尝试 {attempt+1}/{retries}): {e}")
            
            # 对于4xx错误，通常不需要重试
            if attempt < retries - 1 and status_code >= 500:
                backoff_time = 2 ** attempt
                logger.info(f"等待 {backoff_time}秒后重试...")
                time.sleep(backoff_time)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败 {url} (尝试 {attempt+1}/{retries}): {e}")
            
            # 指数退避
            if attempt < retries - 1:
                backoff_time = 2 ** attempt
                logger.info(f"等待 {backoff_time}秒后重试...")
                time.sleep(backoff_time)
        
        except Exception as e:
            log_exception(logger, f"请求发生未知错误 {url} (尝试 {attempt+1}/{retries})")
            
            # 指数退避
            if attempt < retries - 1:
                backoff_time = 2 ** attempt
                logger.info(f"等待 {backoff_time}秒后重试...")
                time.sleep(backoff_time)
    
    logger.error(f"所有重试都失败了 {url}")
    return None

def fetch_multiple(urls: List[str], max_workers: int = 10, **kwargs) -> Dict[str, Optional[str]]:
    """
    并发请求多个URL（多线程版本）
    
    参数:
        urls: 要请求的URL列表
        max_workers: 最大并发数
        **kwargs: 传递给fetch_content的参数
        
    返回:
        字典，键为URL，值为请求结果
    """
    results = {}
    
    start_time = time.time()
    logger.info(f"开始并发请求 {len(urls)} 个URL，最大并发数: {max_workers}")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有请求
        future_to_url = {
            executor.submit(fetch_content, url, **kwargs): url for url in urls
        }
        
        # 处理结果
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results[url] = future.result()
            except Exception as e:
                logger.error(f"并发请求失败 {url}: {e}")
                results[url] = None
    
    elapsed_time = time.time() - start_time
    logger.info(f"并发请求完成，耗时: {elapsed_time:.2f}秒")
    log_performance(logger, "多线程并发请求", elapsed_time, url_count=len(urls), max_workers=max_workers)
    
    return results

async def async_fetch_content(url: str, session: aiohttp.ClientSession, **kwargs) -> Optional[str]:
    """
    异步获取单个URL内容
    
    参数:
        url: 要请求的URL
        session: aiohttp会话对象
        **kwargs: 请求参数
        
    返回:
        URL内容，如果请求失败则返回None
    """
    retries = kwargs.get('retries', 3)
    timeout = kwargs.get('timeout', 10)
    headers = kwargs.get('headers', DEFAULT_HEADERS)
    verify = kwargs.get('verify', False)
    
    for attempt in range(retries):
        try:
            start_time = time.time()
            async with session.get(url, headers=headers, timeout=timeout, ssl=verify) as response:
                response.raise_for_status()
                content = await response.text(encoding='utf-8')
                
                elapsed_time = time.time() - start_time
                logger.debug(f"异步请求成功 {url} (尝试 {attempt+1}/{retries})，耗时: {elapsed_time:.2f}秒")
                
                return content
                
        except asyncio.TimeoutError:
            logger.error(f"异步请求超时 {url} (尝试 {attempt+1}/{retries})")
            
        except aiohttp.ClientError as e:
            logger.error(f"异步请求失败 {url} (尝试 {attempt+1}/{retries}): {e}")
            
        except Exception as e:
            log_exception(logger, f"异步请求发生未知错误 {url} (尝试 {attempt+1}/{retries})")
            
        # 指数退避
        if attempt < retries - 1:
            backoff_time = 2 ** attempt
            logger.info(f"等待 {backoff_time}秒后重试...")
            await asyncio.sleep(backoff_time)
    
    logger.error(f"所有重试都失败了 {url}")
    return None

async def async_fetch_multiple(urls: List[str], max_concurrency: int = 10, **kwargs) -> Dict[str, Optional[str]]:
    """
    并发请求多个URL（异步版本）
    
    参数:
        urls: 要请求的URL列表
        max_concurrency: 最大并发数
        **kwargs: 传递给async_fetch_content的参数
        
    返回:
        字典，键为URL，值为请求结果
    """
    results = {}
    
    start_time = time.time()
    logger.info(f"开始异步并发请求 {len(urls)} 个URL，最大并发数: {max_concurrency}")
    
    # 创建aiohttp会话
    connector = aiohttp.TCPConnector(limit=max_concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        # 创建所有任务
        tasks = [async_fetch_content(url, session, **kwargs) for url in urls]
        
        # 等待所有任务完成
        results_list = await asyncio.gather(*tasks)
        
        # 整理结果
        for url, result in zip(urls, results_list):
            results[url] = result
    
    elapsed_time = time.time() - start_time
    logger.info(f"异步并发请求完成，耗时: {elapsed_time:.2f}秒")
    log_performance(logger, "异步并发请求", elapsed_time, url_count=len(urls), max_concurrency=max_concurrency)
    
    return results

def fetch_multiple_async(urls: List[str], max_concurrency: int = 10, **kwargs) -> Dict[str, Optional[str]]:
    """
    并发请求多个URL（异步版本的同步接口）
    
    参数:
        urls: 要请求的URL列表
        max_concurrency: 最大并发数
        **kwargs: 传递给async_fetch_content的参数
        
    返回:
        字典，键为URL，值为请求结果
    """
    return asyncio.run(async_fetch_multiple(urls, max_concurrency, **kwargs))

def check_url_availability(url: str, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    检查URL的可用性
    
    参数:
        url: 要检查的URL
        timeout: 超时时间（秒，默认从配置获取）
        
    返回:
        Dict[str, Any]: 包含可用性信息的字典
    """
    # 从配置获取默认超时时间
    if timeout is None:
        timeout = NETWORK_CONFIG.get('timeout', 5)
    result = {
        'url': url,
        'available': False,
        'response_time': None,
        'status_code': None,
        'content_type': None,
        'error': None
    }
    
    try:
        start_time = time.time()
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        result['response_time'] = time.time() - start_time
        result['status_code'] = response.status_code
        result['content_type'] = response.headers.get('Content-Type', '')
        
        # 检查是否为有效的HTTP响应
        if 200 <= response.status_code < 400:
            result['available'] = True
            
    except requests.RequestException as e:
        result['error'] = str(e)
    
    return result

def is_streaming_url(url: str, timeout: int = 5) -> bool:
    """
    检查URL是否为流媒体URL
    
    参数:
        url: 要检查的URL
        timeout: 超时时间（秒）
        
    返回:
        如果是流媒体URL返回True，否则返回False
    """
    result = check_url_availability(url, timeout)
    
    if not result['available']:
        return False
    
    # 检查Content-Type
    content_type = result['content_type'].lower()
    streaming_content_types = [
        'video/', 'audio/', 'application/vnd.apple.mpegurl',
        'application/x-mpegurl', 'application/dash+xml'
    ]
    
    return any(media_type in content_type for media_type in streaming_content_types)

if __name__ == "__main__":
    # 测试网络请求功能
    logging.basicConfig(level=logging.DEBUG)
    
    test_urls = [
        'https://iptv-org.github.io/iptv/countries/cn.m3u',
        'https://example.com'
    ]
    
    print("测试单个URL请求:")
    for url in test_urls:
        content = fetch_content(url, retries=2)
        if content:
            print(f"  {url}: 成功获取，长度: {len(content)}字符")
        else:
            print(f"  {url}: 获取失败")
    
    print("\n测试并发请求:")
    results = fetch_multiple(test_urls, max_workers=5)
    for url, content in results.items():
        if content:
            print(f"  {url}: 成功获取，长度: {len(content)}字符")
        else:
            print(f"  {url}: 获取失败")
    
    print("\n测试流媒体URL检查:")
    for url in test_urls:
        is_streaming = is_streaming_url(url)
        print(f"  {url}: {'是' if is_streaming else '不是'}流媒体URL")