#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查剩余的4K频道
"""

import os
import re

def check_remaining_4k():
    # 检查输出目录是否存在
    output_dir = "output"
    if not os.path.exists(output_dir):
        print(f"错误：未找到output目录")
        return False
    
    # 检查iptv.m3u文件是否存在
    m3u_file = os.path.join(output_dir, "iptv.m3u")
    if not os.path.exists(m3u_file):
        print(f"错误：未找到{os.path.abspath(m3u_file)}文件")
        return False
    
    # 读取文件内容
    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有包含4K但不在4K频道类别的行
    pattern = r'#EXTINF:-1 group-title="[^"]+",[^"]*4K[^"]*'
    all_4k_lines = re.findall(pattern, content, re.IGNORECASE)
    
    fourk_channel_lines = re.findall(r'#EXTINF:-1 group-title="4K频道",[^"]*4K[^"]*', content, re.IGNORECASE)
    
    remaining_4k_lines = [line for line in all_4k_lines if line not in fourk_channel_lines]
    
    print(f"剩余的4K频道数量: {len(remaining_4k_lines)}")
    for i, line in enumerate(remaining_4k_lines):
        print(f"  {i+1}. {line}")
        
        # 查看完整的频道信息，包括URL
        line_number = content.find(line)
        if line_number != -1:
            next_newline = content.find('\n', line_number)
            if next_newline != -1:
                url_line = content[next_newline+1:content.find('\n', next_newline+1)]
                print(f"     URL: {url_line.strip()}")
    
    return True

if __name__ == "__main__":
    check_remaining_4k()