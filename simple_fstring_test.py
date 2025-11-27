#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
超简单的f-string测试脚本 - 所有输出都写入文件
"""

# 打开输出文件
with open('test_results.txt', 'w') as f:
    f.write('开始f-string测试\n')
    f.write('-' * 30 + '\n')
    
    # 测试基本的print函数
    f.write('测试1: print函数\n')
    f.write('print函数测试\n')
    f.write('-' * 30 + '\n')
    
    # 测试字符串格式化
    f.write('测试2: 字符串格式化\n')
    try:
        # 测试简单的字符串连接
        name = "测试"
        result = "Hello, " + name + "!"
        f.write(f"简单连接: {result}\n")
        
        # 测试f-string
        f.write('测试f-string:\n')
        f_string = f"Hello, {name}!\n"
        f.write(f"f-string结果: {f_string}\n")
        
        # 测试修复后的第277行f-string格式
        f.write('测试第277行格式:\n')
        channel_name = "测试频道"
        category = "测试分类"
        test_line = f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"{category}\",{channel_name}"
        f.write(f"修复后格式: {test_line}\n")
        
        f.write('\nf-string测试成功!\n')
        
except Exception as e:
        f.write(f'\n错误: {type(e).__name__}: {str(e)}\n')
        
    f.write('-' * 30 + '\n')
    f.write('测试完成\n')
