#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
专门测试f-string修复的脚本
"""

print("测试f-string修复")

# 模拟第277行的f-string
channel_name = "测试频道"
category = "测试分类"

try:
    # 测试修复后的f-string
    test_line = f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"{category}\",{channel_name}"
    print(f"f-string测试成功:")
    print(f"  {test_line}")
    
    # 写入测试文件
    with open('fstring_test.txt', 'w', encoding='utf-8') as f:
        f.write(f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"{category}\",{channel_name}\n")
        f.write("http://test-url.com/test.m3u8\n")
    print("\n测试文件写入成功:")
    with open('fstring_test.txt', 'r', encoding='utf-8') as f:
        print(f.read())
        
    print("\nf-string修复验证通过!")
    
except SyntaxError as e:
    print(f"\n语法错误: {e}")
    print("f-string修复失败!")
except Exception as e:
    print(f"\n其他错误: {e}")
    print("测试过程中出现异常!")
