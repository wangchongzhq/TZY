#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较原始文件和验证后文件，找出被标记为无效的频道
"""

import sys
import os
import re
from urllib.parse import urlparse

def read_channels(file_path):
    """读取频道文件，返回包含URL和名称的字典"""
    channels = {}
    with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('#'):
                continue
            if ',' in line:
                try:
                    # 使用与iptv_validator.py相同的解析逻辑
                    # 首先检查是否包含URL协议
                    url_pattern = r'(http[s]?://|rtsp://|rtmp://|mms://|udp://|rtp://)'
                    url_match = re.search(url_pattern, line)
                    if url_match:
                        # 找到URL的起始位置，前面的都是频道名称
                        url_start = url_match.start()
                        name = line[:url_start].rstrip(',').strip()
                        url = line[url_start:].strip()
                    else:
                        # 没有找到明确的URL协议，使用最后一个逗号分割
                        name, url = line.rsplit(',', 1)
                        name = name.strip()
                        url = url.strip()
                    
                    # 处理包含$符号的URL
                    if '$' in url:
                        url = url.split('$')[0]
                    
                    if name and url:
                        channels[url.strip()] = name.strip()
                except ValueError:
                    continue
    return channels

def main():
    if len(sys.argv) < 3:
        print("用法: python compare_channels.py <原始文件> <有效文件>")
        sys.exit(1)
    
    original_file = sys.argv[1]
    valid_file = sys.argv[2]
    
    # 检查文件是否存在
    if not os.path.exists(original_file):
        print(f"原始文件不存在: {original_file}")
        sys.exit(1)
    
    if not os.path.exists(valid_file):
        print(f"有效文件不存在: {valid_file}")
        sys.exit(1)
    
    # 读取两个文件的频道
    original_channels = read_channels(original_file)
    valid_channels = read_channels(valid_file)
    
    print(f"原始频道数: {len(original_channels)}")
    print(f"有效频道数: {len(valid_channels)}")
    
    # 找出无效频道
    invalid_channels = {}
    for url, name in original_channels.items():
        found = False
        for valid_url in valid_channels.keys():
            # 比较基础URL（忽略可能的参数差异）
            if url in valid_url or valid_url in url:
                found = True
                break
        if not found:
            invalid_channels[url] = name
    
    print(f"无效频道数: {len(invalid_channels)}")
    
    # 打印无效频道
    if invalid_channels:
        print("\n无效频道列表:")
        for url, name in invalid_channels.items():
            print(f"{name},{url}")
            # 分析为什么被标记为无效
            try:
                parsed_url = urlparse(url)
                print(f"  格式检查: scheme={parsed_url.scheme}, netloc={parsed_url.netloc}")
            except Exception as e:
                print(f"  格式解析错误: {e}")
    else:
        print("\n所有频道都被标记为有效！")

if __name__ == "__main__":
    main()