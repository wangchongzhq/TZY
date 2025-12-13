#!/usr/bin/env python3

import sys
import os
import re

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入IPTV模块
import IPTV

# 测试错误分类的频道
wrong_4k_channels = [
    ("靖天映画", "https://cdn.iptv8k.top/dl/jrys.php?id=320&time=20240926215313&ip=111.229.253.40"),
    ("靖天戏剧", "https://cdn.iptv8k.top/dl/jrys.php?id=318&time=20240926215313&ip=111.229.253.40"),
    ("经典电影", "https://cdn.iptv8k.top/dl/jrys.php?id=396&time=20240926215313&ip=111.229.253.40"),
    ("天映经典", "https://cdn.iptv8k.top/dl/jrys.php?id=71&time=20240926215313&ip=111.229.253.40"),
    ("星空", "https://cdn.iptv8k.top/dl/jrys.php?id=21&time=20240926215313&ip=111.229.253.40"),
    ("东森电影", "https://cdn.iptv8k.top/dl/jrys.php?id=231&time=20240926215313&ip=111.229.253.40"),
    ("东森洋片", "https://cdn.iptv8k.top/dl/jrys.php?id=232&time=20240926215313&ip=111.229.253.40"),
    ("东森超视", "https://cdn.iptv8k.top/dl/jrys.php?id=216&time=20240926215313&ip=111.229.253.40#rtmp://f13h.mine.nu/sat/tv331#rtmp://f13h.mine.nu/sat/tv331"),
    ("CN卡通", "https://cdn.iptv8k.top/dl/jrys.php?id=364&time=20240926215313&ip=111.229.253.40"),
    ("翡翠", "https://cdn.iptv8k.top/dl/jrys.php?id=3&time=20240926215313&ip=111.229.253.40"),
]

print("测试错误分类的4K频道：")
print("=" * 50)

for channel_name, url in wrong_4k_channels:
    print(f"\n频道名称: {channel_name}")
    print(f"URL: {url}")
    
    # 测试has_4k_in_name
    has_4k_in_name = ("4K" in channel_name or "4k" in channel_name or 
                      "8K" in channel_name or "8k" in channel_name or
                      "超高清" in channel_name or "2160" in channel_name)
    print(f"has_4k_in_name: {has_4k_in_name}")
    
    # 测试normalize_channel_name
    normalized_name = IPTV.normalize_channel_name(channel_name)
    print(f"normalized_name: {normalized_name}")
    
    # 测试has_4k_in_normalized_name
    has_4k_in_normalized_name = ("4K" in normalized_name or "4k" in normalized_name or 
                                 "8K" in normalized_name or "8k" in normalized_name or
                                 "超高清" in normalized_name or "2160" in normalized_name)
    print(f"has_4k_in_normalized_name: {has_4k_in_normalized_name}")
    
    # 测试get_channel_category
    category = IPTV.get_channel_category(normalized_name)
    print(f"get_channel_category: {category}")
    
    # 测试ALIAS_TO_STANDARD
    if normalized_name in IPTV.ALIAS_TO_STANDARD:
        print(f"ALIAS_TO_STANDARD: {IPTV.ALIAS_TO_STANDARD[normalized_name]}")
    
    # 测试CHANNEL_TO_CATEGORY
    if normalized_name in IPTV.CHANNEL_TO_CATEGORY:
        print(f"CHANNEL_TO_CATEGORY: {IPTV.CHANNEL_TO_CATEGORY[normalized_name]}")

print("\n" + "=" * 50)
print("测试结束")
