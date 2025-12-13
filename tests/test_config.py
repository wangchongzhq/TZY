#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置文件读取
"""

import os
from core.config import get_config
from core.file_utils import write_file

# 测试配置读取
print("=== 测试配置读取 ===")
output_config = get_config('output', {})
print(f"output配置: {output_config}")

# 检查output_dir设置
output_dir = "output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"创建目录: {output_dir}")
else:
    print(f"目录已存在: {output_dir}")

# 测试文件路径生成
if 'm3u_file' in output_config:
    output_file_m3u_all = output_config['m3u_file']
    output_file_txt_all = output_config['txt_file']
else:
    output_file_m3u_all = os.path.join(output_dir, output_config.get('m3u_filename', "iptv.m3u"))
    output_file_txt_all = os.path.join(output_dir, output_config.get('txt_filename', "channels.txt"))

print(f"M3U文件路径: {output_file_m3u_all}")
print(f"TXT文件路径: {output_file_txt_all}")

# 测试写入文件
try:
    write_file(output_file_m3u_all, "#EXTM3U\n# 测试文件")
    print(f"✓ 成功写入测试文件: {output_file_m3u_all}")
    print(f"  文件存在: {os.path.exists(output_file_m3u_all)}")
    if os.path.exists(output_file_m3u_all):
        print(f"  文件大小: {os.path.getsize(output_file_m3u_all)} 字节")
        print(f"  文件内容: {open(output_file_m3u_all, 'r', encoding='utf-8').read()[:50]}...")
except Exception as e:
    print(f"✗ 写入文件失败: {e}")

# 检查是否有其他输出路径设置
print("\n=== 检查其他输出路径设置 ===")
for key in output_config:
    print(f"  {key}: {output_config[key]}")