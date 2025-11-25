#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载并处理GitHub上的4K超高清直播源
"""

import os
import re
import sys
import time
from urllib.request import urlopen, Request

# 确保UTF-8编码
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# 4K直播源URL列表
UHD_SOURCES = [
    "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/4K.m3u",
    "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/HDTV.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u",
    "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV.txt",
]

# 超高清关键词
UHD_KEYWORDS = ['4K', '4k', '超高清', '2160', '2160p', '8K', '8k']

def get_content(url):
    """获取URL内容"""
    try:
        print(f"正在获取: {url}")
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
            print(f"成功获取，大小: {len(content)} 字节")
            return content
    except Exception as e:
        print(f"获取失败: {str(e)}")
        return None

def is_uhd_channel(line, channel_name):
    """判断是否为超高清频道"""
    line_lower = line.lower()
    name_lower = channel_name.lower()
    
    for keyword in UHD_KEYWORDS:
        if keyword.lower() in line_lower or keyword.lower() in name_lower:
            return True
    return False

def extract_uhd_channels(content, source_name):
    """从内容中提取4K超高清频道"""
    if not content:
        return []
    
    uhd_channels = []
    lines = content.split('\n')
    
    # 处理M3U格式
    if '#EXTM3U' in content:
        extinf_line = None
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                extinf_line = line
            elif line.startswith(('http://', 'https://')) and extinf_line:
                # 提取频道名称
                channel_name = extinf_line.split(',')[-1].strip()
                url = line
                
                if is_uhd_channel(extinf_line, channel_name) or is_uhd_channel(url, channel_name):
                    uhd_channels.append((channel_name, url, source_name))
                    print(f"找到4K频道: {channel_name} -> {url}")
                
                extinf_line = None
    # 处理文本格式 (频道名称,URL)
    else:
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and ',' in line:
                parts = line.split(',')
                if len(parts) >= 2:
                    channel_name = parts[0].strip()
                    url = parts[1].strip()
                    
                    if url.startswith(('http://', 'https://')) and is_uhd_channel(line, channel_name):
                        uhd_channels.append((channel_name, url, source_name))
                        print(f"找到4K频道: {channel_name} -> {url}")
    
    return uhd_channels

def main():
    """主函数"""
    print("开始下载并处理4K超高清直播源...")
    print("=" * 60)
    
    all_uhd_channels = []
    
    for source_url in UHD_SOURCES:
        source_name = source_url.split('/')[-1]
        print(f"\n--- 处理来源: {source_name} ---")
        
        content = get_content(source_url)
        if content:
            uhd_channels = extract_uhd_channels(content, source_name)
            if uhd_channels:
                all_uhd_channels.extend(uhd_channels)
                print(f"从{source_name}提取到 {len(uhd_channels)} 个4K频道")
            else:
                print(f"{source_name}中未找到4K频道")
        
    print("\n" + "=" * 60)
    print(f"总共找到 {len(all_uhd_channels)} 个4K超高清直播源")
    
    # 去重处理
    unique_channels = {}
    for channel_name, url, source in all_uhd_channels:
        if channel_name not in unique_channels:
            unique_channels[channel_name] = (url, source)
    
    print(f"去重后剩余 {len(unique_channels)} 个4K频道")
    
    # 生成结果文件
    output_file = 'uhd_channels.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 4K超高清直播源列表\n")
        f.write(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 共包含 {len(unique_channels)} 个4K超高清频道\n\n")
        
        f.write("4K超高清频道 (#genre#\n")
        for channel_name, (url, source) in sorted(unique_channels.items()):
            f.write(f"{channel_name},{url}\n")
    
    print(f"\n4K超高清直播源已保存到: {output_file}")
    print("\n4K超高清直播源列表:")
    for i, (channel_name, (url, source)) in enumerate(sorted(unique_channels.items()), 1):
        print(f"{i}. {channel_name} -> {url}")

if __name__ == "__main__":
    main()
