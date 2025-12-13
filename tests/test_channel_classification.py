#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：模拟频道分类问题
"""

import re
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入需要测试的函数
from IPTV import normalize_channel_name, get_channel_category

# 测试频道列表（名称不含4K，但URL含iptv8k.top）
test_channels = [
    ("靖天映画", "https://live.iptv8k.top/live/jtyh.m3u8"),
    ("翡翠", "https://live.iptv8k.top/live/tvb1.m3u8"),
    ("CCTV5+体育赛事", "https://live.iptv8k.top/live/cctv5p.m3u8"),
    ("CCTV14少儿", "https://live.iptv8k.top/live/cctv14.m3u8"),
    ("广东体育", "https://live.iptv8k.top/live/gdty.m3u8"),
    ("星空卫视", "https://live.iptv8k.top/live/xingkong.m3u8"),
    ("湖南卫视", "https://live.iptv8k.top/live/hunan.m3u8"),
    ("浙江卫视", "https://live.iptv8k.top/live/zhejiang.m3u8"),
    ("江苏卫视", "https://live.iptv8k.top/live/jiangsu.m3u8"),
    ("东方卫视", "https://live.iptv8k.top/live/dongfang.m3u8")
]

print("测试频道分类问题：")
print("=" * 50)

for channel_name, url in test_channels:
    print(f"\n频道名称：{channel_name}")
    print(f"频道URL：{url}")
    
    # 检查原始名称是否包含4K标识
    has_4k_in_name = ("4K" in channel_name or "4k" in channel_name or 
                      "8K" in channel_name or "8k" in channel_name or
                      "超高清" in channel_name or "2160" in channel_name)
    print(f"原始名称含4K标识：{has_4k_in_name}")
    
    # 测试规范化后的名称
    normalized_name = normalize_channel_name(channel_name)
    print(f"规范化后的名称：{normalized_name}")
    
    # 检查规范化后的名称是否包含4K标识
    has_4k_in_normalized = ("4K" in normalized_name or "4k" in normalized_name or 
                            "8K" in normalized_name or "8k" in normalized_name or
                            "超高清" in normalized_name or "2160" in normalized_name)
    print(f"规范化名称含4K标识：{has_4k_in_normalized}")
    
    # 获取频道分类
    category = get_channel_category(channel_name)
    print(f"获取到的分类：{category}")
    
    # 模拟extract_channels_from_m3u中的逻辑
    if has_4k_in_name:
        print("模拟分类结果：4K频道（原始名称）")
    elif normalized_name and has_4k_in_normalized:
        print("模拟分类结果：4K频道（规范化名称）")
    else:
        print("模拟分类结果：非4K频道")

print("\n" + "=" * 50)
print("测试结束")
