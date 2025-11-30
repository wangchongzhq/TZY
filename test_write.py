#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的文件写入测试脚本
"""

import os
from datetime import datetime

OUTPUT_FILE = 'test_output.txt'

# 生成测试内容
test_lines = [
    '# 测试文件',
    f'# 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    '# 这是一个测试文件',
    '',
    '测试频道1,http://test1.com',
    '测试频道2,http://test2.com'
]

# 打印调试信息
print(f'输出文件路径: {os.path.abspath(OUTPUT_FILE)}')
print(f'输出目录是否存在: {os.path.exists(os.path.dirname(os.path.abspath(OUTPUT_FILE)))}')
print(f'输出内容行数: {len(test_lines)}')
print(f'输出内容示例:')
for i, line in enumerate(test_lines[:3]):
    print(f'  {i+1}: {line}')

# 尝试写入文件
try:
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        written = f.write('\n'.join(test_lines))
    print(f'\n成功写入输出文件: {OUTPUT_FILE}')
    print(f'写入的字符数: {written}')
    print(f'文件是否存在: {os.path.exists(OUTPUT_FILE)}')
    print(f'文件大小: {os.path.getsize(OUTPUT_FILE) if os.path.exists(OUTPUT_FILE) else "不存在"} 字节')
    
    # 读取文件内容验证
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f'\n文件内容验证:')
        print(f'读取的字符数: {len(content)}')
        print(f'读取的行数: {len(content.splitlines())}')
        print(f'文件前3行:')
        for i, line in enumerate(content.splitlines()[:3]):
            print(f'  {i+1}: {line}')
    else:
        print('\n警告: 文件创建失败！')
        
    # 检查目录内容
    print(f'\n当前目录文件列表:')
    files = [f for f in os.listdir('.') if f.startswith('test')]
    print(files)
    
except Exception as e:
    print(f'\n写入文件失败: {e}')
    import traceback
    print(f'异常堆栈: {traceback.format_exc()}')
