#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试extract_channels_from_m3u函数对包含URL的频道的处理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from IPTV import extract_channels_from_m3u

# 模拟M3U内容，包含名称不含4K但URL含iptv8k.top的频道
m3u_content = """#EXTM3U
#EXTINF:-1 tvg-name="JTYY",靖天映画
https://live.iptv8k.top/live/jtYY.m3u8
#EXTINF:-1 tvg-name="Jade",翡翠台
https://live.iptv8k.top/live/jade.m3u8
#EXTINF:-1 tvg-name="CCTV4K",CCTV4K超高清
https://live.example.com/cctv4k.m3u8
#EXTINF:-1 tvg-name="CCTV1",CCTV1
https://live.example.com/cctv1.m3u8
"""

print("=== 测试extract_channels_from_m3u函数 ===")
print("测试内容：")
print(m3u_content)
print("\n" + "="*50)

# 测试函数
channels = extract_channels_from_m3u(m3u_content)

print("\n提取到的频道：")
for category, channel_list in channels.items():
    print(f"\n{category}：")
    for channel_name, url in channel_list:
        print(f"  - {channel_name} -> {url}")

# 检查错误分类
print("\n" + "="*50)
print("检查错误分类：")
if "4K频道" in channels:
    for channel_name, url in channels["4K频道"]:
        if "4K" not in channel_name and "4k" not in channel_name and "8K" not in channel_name and "8k" not in channel_name and "超高清" not in channel_name and "2160" not in channel_name:
            print(f"❌ 错误：{channel_name} 被错误分类到4K频道")
        else:
            print(f"✅ 正确：{channel_name} 分类到4K频道")
else:
    print("❌ 没有4K频道")

# 检查普通频道是否被正确分类
print("\n" + "="*50)
print("检查普通频道分类：")
for category, channel_list in channels.items():
    if category != "4K频道":
        for channel_name, url in channel_list:
            if "4K" not in channel_name and "4k" not in channel_name and "8K" not in channel_name and "8k" not in channel_name and "超高清" not in channel_name and "2160" not in channel_name:
                print(f"✅ 正确：{channel_name} 分类到 {category}")
