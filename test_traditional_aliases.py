#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试频道别名自动添加繁体中文功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.tvzy_processor import get_channel_mapping
from core.chinese_conversion import traditionalize_chinese

def test_traditional_aliases():
    """
    测试频道别名自动添加繁体中文功能
    """
    print("=== 测试频道别名自动添加繁体中文功能 ===")
    
    # 获取频道映射
    channel_mapping = get_channel_mapping()
    
    print(f"\n总频道数: {len(channel_mapping)}")
    
    # 检查前10个频道的别名是否包含繁体版本
    print("\n检查前10个频道的别名:")
    for i, (channel_name, aliases) in enumerate(list(channel_mapping.items())[:10]):
        print(f"\n{i+1}. 频道: {channel_name}")
        print(f"   别名列表: {aliases}")
        
        # 检查是否包含繁体别名
        has_traditional = False
        for alias in aliases:
            if traditionalize_chinese(channel_name) == alias and alias != channel_name:
                has_traditional = True
                print(f"   ✓ 包含繁体别名: {alias}")
                break
        if not has_traditional:
            print(f"   ✗ 未包含繁体别名")
    
    # 检查特定频道的别名
    print("\n检查特定频道的别名:")
    test_channels = ["CCTV1", "湖南卫视", "女性时尚"]
    for channel in test_channels:
        if channel in channel_mapping:
            aliases = channel_mapping[channel]
            print(f"\n频道: {channel}")
            print(f"别名: {aliases}")
            
            # 检查是否包含繁体别名
            traditional_version = traditionalize_chinese(channel)
            if traditional_version in aliases:
                print(f"✓ 包含繁体别名: {traditional_version}")
            else:
                print(f"✗ 未包含繁体别名: {traditional_version}")
        else:
            print(f"\n频道 {channel} 不在映射中")

if __name__ == "__main__":
    test_traditional_aliases()
