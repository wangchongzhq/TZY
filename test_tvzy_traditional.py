#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试tvzy.py中的频道映射是否包含繁体别名
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入tvzy.py中的频道映射
from tvzy import CHANNEL_MAPPING
from core.chinese_conversion import traditionalize_chinese

def test_tvzy_traditional_aliases():
    """
    测试tvzy.py中的频道映射是否包含繁体别名
    """
    print("=== 测试tvzy.py中的频道映射繁体别名功能 ===")
    
    print(f"\n总频道数: {len(CHANNEL_MAPPING)}")
    
    # 检查前10个频道的别名是否包含繁体版本
    print("\n检查前10个频道的别名:")
    for i, (channel_name, aliases) in enumerate(list(CHANNEL_MAPPING.items())[:10]):
        print(f"\n{i+1}. 频道: {channel_name}")
        print(f"   别名列表: {aliases}")
        
        # 检查是否包含繁体别名
        has_traditional = False
        traditional_channel = traditionalize_chinese(channel_name)
        if traditional_channel != channel_name and traditional_channel in aliases:
            has_traditional = True
            print(f"   ✓ 包含繁体别名: {traditional_channel}")
        
        # 检查别名中的繁体版本
        for alias in aliases:
            traditional_alias = traditionalize_chinese(alias)
            if traditional_alias != alias and traditional_alias in aliases:
                has_traditional = True
                print(f"   ✓ 包含别名的繁体版本: {alias} -> {traditional_alias}")
                break
                
        if not has_traditional:
            print(f"   ✗ 未包含繁体别名")
    
    # 检查特定频道的别名
    print("\n检查特定频道的别名:")
    test_channels = ["CCTV1", "湖南卫视", "女性时尚", "北京卫视4K"]
    for channel in test_channels:
        if channel in CHANNEL_MAPPING:
            aliases = CHANNEL_MAPPING[channel]
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
    test_tvzy_traditional_aliases()
