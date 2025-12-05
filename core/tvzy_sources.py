#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVZY数据源管理模块
功能：管理TVZY的数据源配置和获取
"""

import logging
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入核心模块
from .network import fetch_content
from .parser import parse_content, ChannelInfo
from .config import get_config
from .logging_config import get_logger, log_exception, log_performance

# 获取日志记录器
logger = get_logger(__name__)

# 从配置获取参数
NETWORK_CONFIG = get_config('network', {})
MAX_WORKERS = get_config('network.max_workers', 10)
TIMEOUT = get_config('network.timeout', 10)
ALLOWED_DOMAINS = get_config('network.allowed_domains', [])

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 数据源列表
def get_github_sources() -> List[str]:
    """
    获取GitHub数据源列表
    
    返回:
        List[str]: 数据源URL列表
    """
    return get_config('sources.github_sources', [
        # 有效的中国电视频道源
        "http://tv.html-5.me/i/9390107.txt",
        "https://ghfast.top/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt",
        "https://ghfast.top/raw.githubusercontent.com/ffmking/tv1/main/888.txt",
        "https://ghfast.top/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt",
        "https://freetv.fun/test_channels_new.txt",
        "https://ghfast.top/https://github.com/kimwang1978/collect-txt/blob/main/bbxx.txt",
        "https://cdn.jsdelivr.net/gh/Guovin/iptv-api@gd/output/result.txt",
        "https://gitee.com/xiao-ping2/iptv-api/raw/master/output/xp_result.txt",
        # 其他稳定的IPTV源
        "https://ghfast.top/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u",
        "https://ghfast.top/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/hk.m3u",
        "https://ghfast.top/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tw.m3u",
        # 优质高清源
        "https://ghfast.top/https://raw.githubusercontent.com/LongLiveTheKing/web-data/master/data/ip.txt",
        "https://ghfast.top/https://raw.githubusercontent.com/HeJiawen01/IPTV/main/IPTV.m3u",
        "https://ghfast.top/https://raw.githubusercontent.com/XIU2/CloudflareSpeedTest/master/ip.txt",
        "https://ghfast.top/https://raw.githubusercontent.com/chenjie/ip.txt/master/ip.txt",
        "https://ghfast.top/https://raw.githubusercontent.com/chnadsl/IPTV/main/IPTV.m3u"
    ])

# 从URL中提取域名
def extract_domain(url: str) -> Optional[str]:
    """
    从URL中提取域名
    
    参数:
        url: 要提取域名的URL
    
    返回:
        Optional[str]: 提取的域名，如果提取失败返回None
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except Exception as e:
        logger.error(f"从URL {url} 提取域名失败: {e}")
        return None

# 检查URL是否在允许的域名列表中
def is_allowed_domain(url: str) -> bool:
    """
    检查URL是否在允许的域名列表中
    
    参数:
        url: 要检查的URL
    
    返回:
        bool: 如果URL在允许的域名列表中返回True，否则返回False
    """
    if not ALLOWED_DOMAINS:
        return True  # 如果允许的域名列表为空，则允许所有域名
    
    domain = extract_domain(url)
    if not domain:
        return False
    
    for allowed_domain in ALLOWED_DOMAINS:
        if allowed_domain in domain:
            return True
    
    return False

# 从单一数据源获取频道信息
def get_channels_from_source(source: str) -> List[ChannelInfo]:
    """
    从单一数据源获取频道信息
    
    参数:
        source: 数据源URL
    
    返回:
        List[ChannelInfo]: 从数据源获取的频道信息列表
    """
    channels = []
    
    try:
        # 获取数据源内容
        content = fetch_content(source, timeout=TIMEOUT, headers=HEADERS)
        if not content:
            logger.warning(f"无法获取数据源内容: {source}")
            return channels
        
        logger.info(f"从数据源 {source} 获取到内容，长度: {len(content)} 字符")
        
        # 使用统一解析接口解析内容
        source_channels = parse_content(content)
        
        # 过滤掉不在允许域名列表中的频道
        for channel in source_channels:
            if is_allowed_domain(channel.url):
                channel.source = source  # 添加数据源信息
                channels.append(channel)
        
        logger.info(f"从数据源 {source} 成功提取 {len(channels)} 个频道")
    except Exception as e:
        logger.error(f"处理数据源时出错: {source}, 错误: {e}")
        log_exception(logger, f"处理数据源时出错: {source}")
    
    return channels

# 从多个数据源获取频道信息
def get_channels_from_sources(sources: Optional[List[str]] = None, max_workers: int = MAX_WORKERS) -> List[ChannelInfo]:
    """
    从多个数据源获取频道信息
    
    参数:
        sources: 数据源URL列表，如果为None则使用默认列表
        max_workers: 最大并发数
    
    返回:
        List[ChannelInfo]: 从所有数据源获取的频道信息列表
    """
    all_channels = []
    
    # 如果没有提供数据源列表，则使用默认列表
    if sources is None:
        sources = get_github_sources()
    
    logger.info(f"开始从 {len(sources)} 个数据源获取频道信息")
    
    # 使用多线程获取频道信息
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_source = {executor.submit(get_channels_from_source, source): source for source in sources}
        
        # 处理任务结果
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                channels = future.result()
                logger.info(f"从数据源 {source} 获取到 {len(channels)} 个频道")
                all_channels.extend(channels)
            except Exception as e:
                logger.error(f"从数据源 {source} 获取频道时出错: {e}")
                log_exception(logger, f"从数据源 {source} 获取频道时出错")
    
    logger.info(f"总共获取到 {len(all_channels)} 个频道")
    return all_channels

if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试获取数据源列表
    sources = get_github_sources()
    print(f"数据源列表包含 {len(sources)} 个URL")
    for source in sources[:5]:
        print(f"  {source}")
    
    # 测试从单一数据源获取频道
    print("\n测试从单一数据源获取频道:")
    if sources:
        channels = get_channels_from_source(sources[0])
        print(f"  从 {sources[0]} 获取到 {len(channels)} 个频道")
        for channel in channels[:5]:
            print(f"    {channel}")
    
    # 测试从多个数据源获取频道
    print("\n测试从多个数据源获取频道:")
    channels = get_channels_from_sources(sources[:3], max_workers=3)
    print(f"  从 {len(sources[:3])} 个数据源获取到 {len(channels)} 个频道")
