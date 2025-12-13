#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试normalize_channel_name函数的修复是否有效
"""

import sys
import os
import re

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.channel_utils import normalize_channel_name

# 测试用例
test_cases = [
    ("翡翠台4K", "翡翠卫视4K"),      # 测试主要问题：保留4K标识
    ("CCTV4K", "CCTV4K"),           # 测试CCTV 4K频道
    ("CCTV8K", "CCTV8K"),           # 测试CCTV 8K频道
    ("北京卫视4K", "北京卫视4K"),    # 测试卫视频道4K
    ("湖南卫视HD", "湖南卫视HD"),    # 测试卫视频道高清
    ("浙江卫视", "浙江卫视"),       # 测试普通卫视频道
    ("东方卫视直播", "东方卫视直播"),  # 测试卫视频道直播
    ("凤凰中文台", "凤凰中文卫视"),   # 测试将"台"转换为"卫视"
    ("东森新闻台4K", "东森新闻卫视4K"), # 测试带4K的"台"转换
]

print("测试normalize_channel_name函数的修复：")
print("=" * 50)

all_passed = True
for input_name, expected_output in test_cases:
    actual_output = normalize_channel_name(input_name)
    status = "✓ PASS" if actual_output == expected_output else "✗ FAIL"
    if actual_output != expected_output:
        all_passed = False
    print(f"{status}: {input_name:<15} -> {actual_output:<15} (期望: {expected_output})")

print("=" * 50)
if all_passed:
    print("🎉 所有测试通过！修复有效。")
else:
    print("❌ 部分测试失败！修复需要调整。")
    sys.exit(1)
