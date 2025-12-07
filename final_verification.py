#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证脚本：测试简繁体转换功能的完整实现
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入核心模块
from core.chinese_conversion import (
    simplify_chinese, 
    traditionalize_chinese, 
    add_traditional_aliases
)
from core.tvzy_processor import get_channel_mapping
from tvzy import CHANNEL_MAPPING as TVZY_CHANNEL_MAPPING

def test_simplified_traditional_conversion():
    """
    测试简繁体转换功能
    """
    print("=== 1. 测试简繁体转换功能 ===")
    
    test_cases = [
        ("简体中文", "繁體中文"),
        ("CCTV1", "CCTV1"),
        ("湖南卫视", "湖南衛視"),
        ("女性时尚", "女性時尚"),
        ("北京卫视4K", "北京衛視4K"),
        ("CCTV16 奥林匹克 4K", "CCTV16 奧林匹克 4K"),
    ]
    
    all_passed = True
    for simplified, expected_traditional in test_cases:
        result = traditionalize_chinese(simplified)
        if result == expected_traditional:
            print(f"✓ {simplified} -> {result} (正确)")
        else:
            print(f"✗ {simplified} -> {result} (错误，期望: {expected_traditional})")
            all_passed = False
        
        # 反向测试
        reverse_result = simplify_chinese(result)
        if reverse_result == simplified:
            print(f"  ✓ {result} -> {reverse_result} (反向转换正确)")
        else:
            print(f"  ✗ {result} -> {reverse_result} (反向转换错误，期望: {simplified})")
            all_passed = False
    
    return all_passed

def test_existing_aliases():
    """
    测试现有频道别名是否包含繁体版本
    """
    print("\n=== 2. 测试现有频道别名 ===")
    
    # 测试core.tvzy_processor中的频道映射
    processor_mapping = get_channel_mapping()
    print(f"\ncore.tvzy_processor中的频道映射数: {len(processor_mapping)}")
    
    # 测试tvzy.py中的频道映射
    print(f"tvzy.py中的频道映射数: {len(TVZY_CHANNEL_MAPPING)}")
    
    # 检查前5个频道
    print("\n检查前5个频道的别名:")
    for i, (channel, aliases) in enumerate(list(processor_mapping.items())[:5]):
        print(f"\n{i+1}. {channel}:")
        print(f"   别名: {aliases}")
        
        # 检查是否包含繁体别名
        traditional_version = traditionalize_chinese(channel)
        if traditional_version != channel and traditional_version in aliases:
            print(f"   ✓ 包含繁体别名: {traditional_version}")
        else:
            print(f"   ✗ 未包含繁体别名")
    
    return True

def test_new_channel_aliases():
    """
    测试新增频道时的自动繁体别名生成
    """
    print("\n=== 3. 测试新增频道的自动繁体别名生成 ===")
    
    # 模拟新增频道的映射
    new_channels = {
        "测试频道1": ["Test Channel 1"],
        "高清体育": ["HD Sports"],
        "电影频道": ["Movie Channel", "CCTV-6"],
    }
    
    print("新增频道映射:")
    for channel, aliases in new_channels.items():
        print(f"  {channel}: {aliases}")
    
    # 添加繁体别名
    new_channels_with_traditional = add_traditional_aliases(new_channels)
    
    print("\n添加繁体别名后的映射:")
    all_passed = True
    for channel, aliases in new_channels_with_traditional.items():
        print(f"  {channel}: {aliases}")
        
        # 检查是否包含繁体别名
        traditional_version = traditionalize_chinese(channel)
        if traditional_version != channel and traditional_version in aliases:
            print(f"    ✓ 包含频道繁体版本: {traditional_version}")
        else:
            print(f"    ✗ 未包含频道繁体版本")
            all_passed = False
            
        # 检查别名是否有繁体版本
        for alias in aliases:
            if alias == channel or alias.isascii():
                continue  # 跳过频道名称本身和纯英文字符
                
            traditional_alias = traditionalize_chinese(alias)
            if traditional_alias != alias and traditional_alias in aliases:
                print(f"    ✓ 包含别名繁体版本: {alias} -> {traditional_alias}")
                break
    
    return all_passed

def test_specific_channels():
    """
    测试特定频道的别名
    """
    print("\n=== 4. 测试特定频道 ===")
    
    test_channels = ["CCTV1", "湖南卫视", "女性时尚", "北京卫视4K", "CCTV16 奥林匹克 4K"]
    
    for channel in test_channels:
        print(f"\n频道: {channel}")
        
        # 在tvzy_processor映射中查找
        processor_mapping = get_channel_mapping()
        if channel in processor_mapping:
            aliases = processor_mapping[channel]
            print(f"  tvzy_processor映射别名: {aliases}")
            
            # 检查是否包含繁体别名
            traditional_version = traditionalize_chinese(channel)
            if traditional_version in aliases:
                print(f"  ✓ tvzy_processor包含繁体别名")
            else:
                print(f"  ✗ tvzy_processor未包含繁体别名")
        else:
            print(f"  ✗ 未在tvzy_processor映射中找到")
        
        # 在tvzy.py映射中查找
        if channel in TVZY_CHANNEL_MAPPING:
            aliases = TVZY_CHANNEL_MAPPING[channel]
            print(f"  tvzy.py映射别名: {aliases}")
            
            # 检查是否包含繁体别名
            traditional_version = traditionalize_chinese(channel)
            if traditional_version in aliases:
                print(f"  ✓ tvzy.py包含繁体别名")
            else:
                print(f"  ✗ tvzy.py未包含繁体别名")
        else:
            print(f"  ✗ 未在tvzy.py映射中找到")

def main():
    """
    主函数：运行所有测试
    """
    print("开始简繁体转换功能最终验证\n")
    
    # 运行所有测试
    tests = [
        test_simplified_traditional_conversion,
        test_existing_aliases,
        test_new_channel_aliases,
        test_specific_channels
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✓ 所有测试通过！简繁体转换功能已成功实现。")
        print("\n功能总结：")
        print("1. 现有config.json中的频道别名已添加繁体版本")
        print("2. 新增频道时会自动生成繁体别名")
        print("3. 支持简繁体频道名称的识别和匹配")
    else:
        print("✗ 部分测试失败，请检查实现。")
    print("="*50)

if __name__ == "__main__":
    main()
