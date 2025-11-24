#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版直播源获取脚本
"""

import os
import re
from urllib.request import urlopen, Request
import ssl
import logging

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('live_source.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# 禁用SSL验证
ssl._create_default_https_context = ssl._create_unverified_context

# 基本直播源URL（选择一个可能可靠的源）
SIMPLE_LIVE_SOURCES = [
    'https://tonkiang.us/playlist.m3u'
]

def get_simple_content(url):
    """简化版获取内容函数"""
    try:
        logger.info(f"获取: {url}")
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='replace')
            logger.info(f"成功获取内容长度: {len(content)} 字符")
            return content
    except Exception as e:
        logger.error(f"获取失败: {str(e)}")
        return None

def extract_simple_channels(content):
    """简化版提取频道函数"""
    channels = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if line.startswith('#EXTINF'):
            # 提取频道名称
            name_match = re.search(r',([^,]+)$', line)
            if name_match and i + 1 < len(lines) and lines[i + 1].startswith(('http://', 'https://')):
                name = name_match.group(1).strip()
                url = lines[i + 1].strip()
                channels.append((name, url))
    
    logger.info(f"提取到 {len(channels)} 个频道")
    return channels

def write_cgq_file(channels):
    """写入CGQ.TXT文件"""
    with open('CGQ.TXT', 'w', encoding='utf-8') as f:
        # 写入分类
        f.write("央视频道,#genre#\n")
        
        # 简单分类并写入频道
        for name, url in channels[:20]:  # 限制输出20个频道用于测试
            if any(keyword in name for keyword in ['CCTV', '央视', '新闻', '体育']):
                f.write(f"{name}\n{url}\n")
        
        # 写入其他分类
        f.write("\n卫视频道,#genre#\n")
        for name, url in channels[20:40]:
            if any(keyword in name for keyword in ['卫视', '浙江', '江苏', '湖南', '东方']):
                f.write(f"{name}\n{url}\n")
    
    logger.info(f"已写入 CGQ.TXT 文件")

def main():
    logger.info("开始获取直播源...")
    
    # 尝试获取内容
    content = None
    for url in SIMPLE_LIVE_SOURCES:
        content = get_simple_content(url)
        if content:
            break
    
    # 如果没有获取到网络内容，创建示例内容
    if not content:
        logger.warning("无法获取网络内容，创建示例内容...")
        content = """#EXTINF:-1,CCTV-1 综合
https://example.com/cctv1.m3u8
#EXTINF:-1,CCTV-2 财经
https://example.com/cctv2.m3u8
#EXTINF:-1,CCTV-3 综艺
https://example.com/cctv3.m3u8
#EXTINF:-1,CCTV-4 中文国际
https://example.com/cctv4.m3u8
#EXTINF:-1,CCTV-5 体育
https://example.com/cctv5.m3u8
#EXTINF:-1,CCTV-5+ 体育赛事
https://example.com/cctv5plus.m3u8
#EXTINF:-1,CCTV-6 电影
https://example.com/cctv6.m3u8
#EXTINF:-1,CCTV-7 国防军事
https://example.com/cctv7.m3u8
#EXTINF:-1,CCTV-8 电视剧
https://example.com/cctv8.m3u8
#EXTINF:-1,CCTV-9 纪录
https://example.com/cctv9.m3u8
#EXTINF:-1,浙江卫视
https://example.com/zjstv.m3u8
#EXTINF:-1,湖南卫视
https://example.com/hntv.m3u8
#EXTINF:-1,江苏卫视
https://example.com/jstv.m3u8
#EXTINF:-1,东方卫视
https://example.com/dftv.m3u8
"""
    
    # 提取频道
    channels = extract_simple_channels(content)
    
    # 写入文件
    write_cgq_file(channels)
    
    logger.info("完成!")

if __name__ == "__main__":
    main()
