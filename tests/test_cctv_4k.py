#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试CCTV 4K频道名称规范化
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append('.')

from IPTV import normalize_channel_name, get_channel_category

# 测试频道名称
test_names = [
    "CCTV 4K超高清",
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

print("测试normalize_channel_name函数处理CCTV 4K频道名称:")
print("=" * 60)
for name in test_names:
    normalized = normalize_channel_name(name)
    category = get_channel_category(normalized)
    print(f"  '{name}' -> '{normalized}' -> 分类: {category}")
