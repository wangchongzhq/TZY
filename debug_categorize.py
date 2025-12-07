#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tvzy import filter_channel_name, categorize_channel, ChannelInfo, CHANNEL_CATEGORIES

def debug_categorize():
    print("CHANNEL_CATEGORIES中是否包含'港澳频道':", '港澳频道' in CHANNEL_CATEGORIES)
    print("港澳频道包含的频道:", CHANNEL_CATEGORIES.get('港澳频道', []))
    
    # 测试凤凰香港频道的分类
    test_channels = [
        "凤凰香港",
        "凤凰香港 (720p)",
        "凤凰香港高清",
        "凤凰卫视",
        "凤凰卫视中文台",
        "凤凰资讯",
        "凤凰电影"
    ]
    
    print("\n测试频道分类:")
    for channel_name in test_channels:
        channel = ChannelInfo(channel_name, "http://example.com/stream")
        filtered_name = filter_channel_name(channel_name)
        category = categorize_channel(channel)
        print(f"频道名称: {channel_name}")
        print(f"  过滤后名称: {filtered_name}")
        print(f"  分类结果: {category}")
        print("  是否在港澳频道中:", filtered_name in CHANNEL_CATEGORIES.get('港澳频道', []))
        print("  港澳频道中的频道是否在过滤后名称中:")
        for hk_channel in CHANNEL_CATEGORIES.get('港澳频道', []):
            print(f"    '{hk_channel}' in '{filtered_name}': {hk_channel in filtered_name}")
        print()

if __name__ == "__main__":
    debug_categorize()