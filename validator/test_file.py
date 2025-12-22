#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文件解析脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from iptv_validator import IPTVValidator

# 测试用户上传的文件
test_file = "c:\Users\Administrator\Documents\GitHub\TZY\109  live 1205 直播源 -减.txt"

print(f"测试文件: {test_file}")
print(f"文件大小: {os.path.getsize(test_file)} 字节")

# 读取文件内容
with open(test_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"\n文件内容预览:")
print(content[:500] + "...")

# 创建验证器
try:
    validator = IPTVValidator(test_file, debug=True)
    print(f"\n文件类型: {validator.file_type}")
    
    # 根据文件类型选择解析方法
    if validator.file_type == 'm3u':
        channels, categories = validator.read_m3u_file()
    else:
        channels, categories = validator.read_txt_file()
    
    print(f"\n解析结果:")
    print(f"- 总频道数: {len(channels)}")
    print(f"- 分类数: {len(categories)}")
    
    if channels:
        print(f"\n前5个频道:")
        for i, channel in enumerate(channels[:5]):
            print(f"  {i+1}. {channel['name']} -> {channel['url']} (分类: {channel.get('category', '未分类')})")
    else:
        print("\n没有解析到任何频道!")
        
        # 分析为什么没有解析到频道
        print(f"\n文件内容分析:")
        lines = content.split('\n')
        total_lines = len(lines)
        comment_lines = sum(1 for line in lines if line.strip().startswith('//'))
        empty_lines = sum(1 for line in lines if not line.strip())
        other_lines = total_lines - comment_lines - empty_lines
        
        print(f"- 总行数: {total_lines}")
        print(f"- 注释行(//开头): {comment_lines}")
        print(f"- 空行: {empty_lines}")
        print(f"- 其他行: {other_lines}")
        
        # 显示其他行的内容
        print(f"\n其他行内容:")
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith('//'):
                print(f"  {line}")

    
except Exception as e:
    print(f"\n解析错误: {e}")
    import traceback
    traceback.print_exc()
