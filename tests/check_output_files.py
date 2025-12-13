#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查输出目录和文件是否存在
"""

import os

# 检查输出目录是否存在
output_dir = "./output"
if os.path.exists(output_dir):
    print(f"输出目录 {output_dir} 存在")
    # 列出目录中的文件
    files = os.listdir(output_dir)
    print(f"目录中的文件: {files}")
    
    # 检查iptv_ipv4.m3u文件是否存在
    m3u_file = os.path.join(output_dir, "iptv_ipv4.m3u")
    if os.path.exists(m3u_file):
        print(f"文件 {m3u_file} 存在，大小为 {os.path.getsize(m3u_file)} 字节")
    else:
        print(f"文件 {m3u_file} 不存在")
else:
    print(f"输出目录 {output_dir} 不存在")

# 检查当前目录中的文件
print("\n当前目录中的文件:")
current_files = os.listdir(".")
for file in current_files:
    if file.endswith(".m3u"):
        print(f"{file} ({os.path.getsize(file)} 字节)")