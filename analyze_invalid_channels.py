#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析被验证工具标记为无效的频道
比较原始文件和有效文件，找出被误判的频道
"""

import re
import os

def extract_base_url(url):
    """从URL中提取基础URL，去除$符号及其后面的内容"""
    if '$' in url:
        return url.split('$')[0]
    return url

def read_channels(file_path):
    """从文件中读取频道信息，返回字典 {base_url: name} """
    channels = {}
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('//'):
                    continue
                if ',' in line:
                    name, url = line.split(',', 1)
                    name = name.strip()
                    url = url.strip()
                    base_url = extract_base_url(url)
                    channels[base_url] = name
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
    return channels

def analyze_invalid_channels(original_file, valid_file):
    """分析无效频道"""
    # 读取原始文件和有效文件中的频道
    original_channels = read_channels(original_file)
    valid_channels = read_channels(valid_file)
    
    # 找出未通过验证的频道
    invalid_channels = {}
    for base_url, name in original_channels.items():
        if base_url not in valid_channels:
            invalid_channels[base_url] = name
    
    print(f"原始频道总数: {len(original_channels)}")
    print(f"有效频道数: {len(valid_channels)}")
    print(f"无效频道数: {len(invalid_channels)}")
    
    # 分析无效频道的类型
    print("\n无效频道类型分析:")
    protocol_counts = {}
    for base_url, name in invalid_channels.items():
        if 'http://' in base_url:
            protocol = 'http'
        elif 'https://' in base_url:
            protocol = 'https'
        elif 'rtsp://' in base_url:
            protocol = 'rtsp'
        elif 'rtmp://' in base_url:
            protocol = 'rtmp'
        elif 'udp://' in base_url:
            protocol = 'udp'
        elif 'rtp://' in base_url:
            protocol = 'rtp'
        elif 'mms://' in base_url:
            protocol = 'mms'
        else:
            protocol = 'unknown'
        
        protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
    
    for protocol, count in protocol_counts.items():
        print(f"  {protocol}: {count} 个频道")
    
    # 检查是否包含动态参数
    print("\n包含动态参数的无效频道:")
    dynamic_param_pattern = re.compile(r'(\{[A-Z_]+\}|%7B[A-Z_]+%7D)')
    dynamic_count = 0
    for base_url, name in invalid_channels.items():
        if dynamic_param_pattern.search(base_url):
            dynamic_count += 1
            print(f"  {name}: {base_url}")
    print(f"\n总共有 {dynamic_count} 个包含动态参数的无效频道")
    
    # 检查是否包含IPv6地址
    print("\n包含IPv6地址的无效频道:")
    ipv6_count = 0
    for base_url, name in invalid_channels.items():
        if ':' in base_url and '://' in base_url:
            hostname_part = base_url.split('://')[1].split('/')[0]
            if (':' in hostname_part and not hostname_part.startswith('[') and not hostname_part.replace('.', '').replace(':', '').isdigit()) or (hostname_part.startswith('[') and hostname_part.endswith(']')):
                ipv6_count += 1
                print(f"  {name}: {base_url}")
    print(f"\n总共有 {ipv6_count} 个包含IPv6地址的无效频道")
    
    # 将无效频道保存到文件
    invalid_file = "invalid_channels.txt"
    with open(invalid_file, 'w', encoding='utf-8') as f:
        f.write("# 被标记为无效的频道\n")
        f.write("# 频道名称,原始URL\n")
        for base_url, name in invalid_channels.items():
            f.write(f"{name},{base_url}\n")
    
    print(f"\n无效频道列表已保存到 {invalid_file}")
    return invalid_channels

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("用法: python analyze_invalid_channels.py <原始文件> <有效文件>")
        print("示例: python analyze_invalid_channels.py original.m3u outputs/original_valid.m3u")
        sys.exit(1)
    
    original_file = sys.argv[1]
    valid_file = sys.argv[2]
    
    if not os.path.exists(original_file):
        print(f"原始文件 {original_file} 不存在")
        sys.exit(1)
    elif not os.path.exists(valid_file):
        print(f"有效文件 {valid_file} 不存在")
        sys.exit(1)
    else:
        analyze_invalid_channels(original_file, valid_file)
