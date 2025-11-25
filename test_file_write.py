#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from datetime import datetime

# 测试文件写入功能
print("测试文件写入功能...")

try:
    # 写入测试信息到文件
    with open('test_update.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 测试文件\n")
        f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 测试内容\n\n")
        f.write(f"测试频道,http://example.com/test\n")
    
    print("文件写入成功！")
    
    # 读取文件内容并打印
    with open('test_update.txt', 'r', encoding='utf-8') as f:
        content = f.read()
        print("\n文件内容:")
        print(content)
        
    # 检查文件大小
    file_size = os.path.getsize('test_update.txt')
    print(f"\n文件大小: {file_size} 字节")
    
    exit(0)
except Exception as e:
    print(f"错误: {e}")
    exit(1)
