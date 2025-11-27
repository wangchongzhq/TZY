#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本的文件操作测试脚本
"""

import os
import time

# 测试基本的文件写入功能
test_file = 'basic_test_output.txt'

try:
    print(f"测试基本文件写入...")
    print(f"当前目录: {os.getcwd()}")
    
    # 写入测试文件
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(f"测试文件内容\n")
        f.write(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"当前目录: {os.getcwd()}\n")
        f.write(f"Python版本: {os.sys.version}")
    
    print(f"文件写入完成")
    
    # 读取并显示文件内容
    if os.path.exists(test_file):
        print(f"✓ 文件已创建: {test_file}")
        print(f"文件大小: {os.path.getsize(test_file)} 字节")
        print(f"\n文件内容:")
        with open(test_file, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print(f"✗ 文件未创建!")
        print(f"当前目录文件列表:")
        files = os.listdir('.')
        print(f"文件数量: {len(files)}")
        for i, f in enumerate(files[:20]):  # 只显示前20个文件
            print(f"  {i+1}. {f}")
        if len(files) > 20:
            print(f"  ... 还有 {len(files) - 20} 个文件")
    
except Exception as e:
    print(f"发生错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成!")
