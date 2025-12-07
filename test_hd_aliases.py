#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试HD格式别名自动生成功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.tvzy_processor import get_channel_mapping, add_hd_aliases

def test_hd_aliases_for_new_channels():
    """
    测试为新频道自动生成HD格式别名
    """
    print("=== 测试HD格式别名自动生成功能 ===")
    
    # 创建一个包含新频道的测试映射
    test_mapping = {
        "测试频道": ["测试频道"],
        "NEWTV": ["NEWTV"],
        "TEST-CHANNEL": ["TEST-CHANNEL"],
        "CCTV18": ["CCTV18"],
        "高清测试": ["高清测试"]
    }
    
    # 应用HD别名生成函数
    result = add_hd_aliases(test_mapping)
    
    # 验证结果
    all_passed = True
    
    for channel, aliases in result.items():
        print(f"\n频道: {channel}")
        print(f"别名: {aliases}")
        
        # 检查是否包含各种HD格式的别名
        base_name = channel.replace(' HD', '').replace('-HD', '').replace('HD', '')
        
        expected_aliases = [
            f"{base_name}HD",
            f"{base_name} HD",
            f"{base_name}-HD"
        ]
        
        # 如果包含连字符，还需要检查更多变体
        if '-' in base_name:
            base_name_no_dash = base_name.replace('-', '')
            expected_aliases.extend([
                f"{base_name_no_dash}HD",
                f"{base_name_no_dash} HD",
                f"{base_name_no_dash}-HD"
            ])
        
        for expected in expected_aliases:
            if expected not in aliases:
                print(f"❌ 缺少预期别名: {expected}")
                all_passed = False
            else:
                print(f"✅ 包含预期别名: {expected}")
    
    return all_passed

def test_existing_channels():
    """
    测试现有频道是否包含HD格式别名
    """
    print("\n=== 测试现有频道的HD格式别名 ===")
    
    # 获取完整的频道映射
    mapping = get_channel_mapping()
    
    # 检查几个主要频道
    test_channels = ["CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5"]
    all_passed = True
    
    for channel in test_channels:
        if channel in mapping:
            aliases = mapping[channel]
            print(f"\n频道: {channel}")
            
            # 检查是否包含HD格式的别名
            has_hd_aliases = any('HD' in alias.upper() for alias in aliases)
            
            if has_hd_aliases:
                print(f"✅ 已包含HD格式别名")
                # 显示所有HD别名
                hd_aliases = [alias for alias in aliases if 'HD' in alias.upper()]
                print(f"   HD别名: {hd_aliases}")
            else:
                print(f"❌ 缺少HD格式别名")
                print(f"   所有别名: {aliases}")
                all_passed = False
        else:
            print(f"\n频道 {channel} 不在映射中")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    test1_passed = test_hd_aliases_for_new_channels()
    test2_passed = test_existing_channels()
    
    print("\n" + "="*50)
    if test1_passed and test2_passed:
        print("🎉 所有测试通过！HD格式别名自动生成功能正常工作")
        sys.exit(0)
    else:
        print("❌ 部分测试失败！请检查HD格式别名自动生成功能")
        sys.exit(1)