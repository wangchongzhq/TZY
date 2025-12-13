#!/usr/bin/env python3

# 测试normalize_channel_name函数

# 导入IPTV模块
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import IPTV

# 测试频道名称
channel_names = [
    "CCTV4",
    "CCTV8",
    "CCTV4K",
    "CCTV 4K",
    "CCTV-4K",
    "CCTV4K 超高清",
    "CCTV8K",
    "CCTV 8K",
    "CCTV-8K",
    "CCTV8K 超高清",
    "CCTV5-4K",
    "CCTV5+4K",
    "CCTV5_4K"
]

# 测试normalize_channel_name函数
print("测试normalize_channel_name函数:")
for name in channel_names:
    result = IPTV.normalize_channel_name(name)
    print(f"  '{name}' -> '{result}'")

# 测试URL处理
print("\n测试URL处理逻辑:")
url_tests = [
    ("CCTV4", "http://example.com/nptv/cctv4k.m3u8"),
    ("CCTV8", "http://example.com/nptv/cctv8k.m3u8"),
    ("CCTV5", "http://example.com/nptv/cctv5-4k.m3u8"),
    ("CCTV6", "http://example.com/nptv/cctv6-8k.m3u8")
]

for channel_name, url in url_tests:
    has_4k_in_name = ("4K" in channel_name or "4k" in channel_name or 
                      "8K" in channel_name or "8k" in channel_name or
                      "超高清" in channel_name or "2160" in channel_name)
    has_4k_in_url = ("4K" in url or "4k" in url or 
                     "8K" in url or "8k" in url or
                     "2160" in url)
    
    print(f"  频道: '{channel_name}', URL: '{url}'")
    print(f"    has_4k_in_name: {has_4k_in_name}, has_4k_in_url: {has_4k_in_url}")
    
    if has_4k_in_url and not has_4k_in_name:
        # 模拟4K频道处理逻辑
        if re.match(r'^CCTV\d+|^CCTV.*频道', channel_name, re.IGNORECASE):
            if re.search(r'cctv4k', url.lower()):
                display_name = "CCTV4K"
                print(f"    -> 处理为: '{display_name}'")
            elif re.search(r'cctv8k', url.lower()):
                display_name = "CCTV8K"
                print(f"    -> 处理为: '{display_name}'")
            elif re.search(r'4k', url.lower()):
                display_name = f"{channel_name}-4K"
                print(f"    -> 处理为: '{display_name}'")
            elif re.search(r'8k', url.lower()):
                display_name = f"{channel_name}-8K"
                print(f"    -> 处理为: '{display_name}'")
    else:
        print(f"    -> 不处理4K/8K")