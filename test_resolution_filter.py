#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证低分辨率过滤功能
"""

import re

def is_low_resolution(line, channel_name):
    """判断是否为低分辨率线路
    识别并过滤576p等低分辨率线路
    """
    line_lower = line.lower()
    name_lower = channel_name.lower()
    
    # 明确标记的低分辨率
    if '576p' in line_lower or '576p' in name_lower:
        return True
    
    # 其他低分辨率标记
    if '标清' in line or '标清' in channel_name:
        return True
    
    # 明确的低质量标记
    if 'sd' in line_lower or '480p' in line_lower:
        return True
    
    return False

# 测试用例
test_cases = [
    ("甘肃卫视 (576p)", "http://118.81.195.79:9003/hls/25/index.m3u8", True),
    ("贵州卫视 (576p)", "http://183.207.248.71/gitv/live1/G_GUIZHOU/G_GUIZHOU", True),
    ("CCTV-1 HD", "http://example.com/cctv1.m3u8", False),
    ("湖南卫视 标清", "http://example.com/hunan.m3u8", True),
    ("浙江卫视 SD", "http://example.com/zhejiang.m3u8", True),
    ("北京卫视 4K", "http://example.com/beijing4k.m3u8", False),
    ("东方卫视 1080p", "http://example.com/dongfang.m3u8", False),
]

print("=== 低分辨率过滤功能测试 ===")
print()

for channel_name, url, expected in test_cases:
    # 测试频道名和URL的低分辨率检测
    result_name = is_low_resolution(channel_name, channel_name)
    result_url = is_low_resolution(url, channel_name)
    result = result_name or result_url
    
    status = "✓ 通过" if result == expected else "✗ 失败"
    expected_text = "应被过滤" if expected else "应被保留"
    result_text = "被过滤" if result else "被保留"
    
    print(f"频道: {channel_name}")
    print(f"URL: {url}")
    print(f"预期: {expected_text}")
    print(f"实际: {result_text}")
    print(f"结果: {status}")
    print()

print("=== 测试完成 ===")
