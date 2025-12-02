#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
过滤掉包含"example"或"demo"字符的URL的脚本
"""

import re

# 定义要处理的文件
FILE_PATH = 'ipzy_channels.txt'

# 定义要排除的模式（不区分大小写）
EXCLUDE_PATTERN = re.compile(r'(example|demo)', re.IGNORECASE)

def main():
    try:
        # 读取文件内容
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 过滤掉包含"example"或"demo"字符的行
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if not line or not EXCLUDE_PATTERN.search(line):
                filtered_lines.append(line)
        
        # 写入过滤后的内容
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write('\n'.join(filtered_lines))
        
        return True
    except Exception:
        return False

if __name__ == "__main__":
    main()
