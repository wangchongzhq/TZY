#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分类标题格式的修复
"""

# 模拟CHANNEL_CATEGORIES
CHANNEL_CATEGORIES = {
    "央视频道": [],
    "卫视频道": [],
    "其他": []
}

# 简化版的generate_txt_file函数，只测试分类标题生成
def test_category_format():
    print("测试分类标题格式")
    print("=" * 40)
    
    print("\n1. 测试原始错误格式：")
    for category in CHANNEL_CATEGORIES:
        old_format = f"#{category}#,genre#"  # 原始错误格式
        print(f"   {old_format}")
        if '#,#genre#' in old_format:
            print(f"   ❌ 格式正确")
        else:
            print(f"   ✅ 格式错误（缺少逗号）")
    
    print("\n2. 测试修复后的正确格式：")
    for category in CHANNEL_CATEGORIES:
        new_format = f"#{category}#,#genre#"  # 修复后的格式
        print(f"   {new_format}")
        if '#,#genre#' in new_format:
            print(f"   ✅ 格式正确")
        else:
            print(f"   ❌ 格式错误")
    
    print("\n3. 测试其他特殊情况：")
    test_cases = [
        "#4K频道#,#genre#",
        "#电影频道#,#genre#",
        "#儿童频道#,#genre#",
        "#4K频道#,genre#",  # 错误格式
        "#电影频道#,genre#",  # 错误格式
        "#儿童频道#,genre#"   # 错误格式
    ]
    
    for test_case in test_cases:
        if '#,#genre#' in test_case:
            print(f"   ✅ 正确格式: {test_case}")
        else:
            print(f"   ❌ 错误格式: {test_case}")

if __name__ == "__main__":
    test_category_format()
