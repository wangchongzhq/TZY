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
        print(f"开始处理文件: {FILE_PATH}")
        
        # 读取文件内容
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"原始文件行数: {len(lines)}")
        
        # 过滤掉包含"example"或"demo"字符的行
        filtered_lines = []
        excluded_count = 0
        
        for line in lines:
            line = line.strip()
            if not line or not EXCLUDE_PATTERN.search(line):
                filtered_lines.append(line)
            else:
                excluded_count += 1
        
        print(f"过滤后文件行数: {len(filtered_lines)}")
        print(f"排除的行数: {excluded_count}")
        
        # 写入过滤后的内容
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write('\n'.join(filtered_lines))
        
        print(f"成功更新文件: {FILE_PATH}")
        return True
    except Exception as e:
        print(f"处理文件时出错: {e}")
        return False

if __name__ == "__main__":
    main()
