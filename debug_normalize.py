#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试normalize_channel_name函数
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append('.')

from IPTV import normalize_channel_name, get_channel_category

# 测试频道名称
test_names = [
    "4K测试频道",
    "普通频道",
    "CCTV 4K",
    "CCTV1",
    "超高清频道",
    "2160测试",
    "普通频道2",
    "8K测试频道",
    "这个频道不包含4K关键词"
]

print("测试normalize_channel_name函数:")
for name in test_names:
    normalized = normalize_channel_name(name)
    category = get_channel_category(normalized)
    print(f"  '{name}' -> '{normalized}' -> 分类: {category}")
