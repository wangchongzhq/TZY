#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复Python文件的缩进错误
"""

import sys

def fix_indentation(file_path):
    """修复文件的缩进错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 修复缩进
        fixed_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped:
                # 保持原有的缩进级别，但确保使用空格
                indent_level = len(line) - len(line.lstrip())
                # 重新创建缩进（使用4个空格）
                fixed_line = ' ' * indent_level + stripped + '\n'
                fixed_lines.append(fixed_line)
            else:
                # 空行保持不变
                fixed_lines.append('\n')
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print(f"成功修复 {file_path} 的缩进")
        return True
    except Exception as e:
        print(f"修复缩进时出错: {e}")
        return False

def check_file(file_path):
    """检查文件的特定行"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"文件 {file_path} 共有 {len(lines)} 行")
        print("检查第325-340行:")
        for i in range(324, min(340, len(lines))):
            print(f'{i+1:3d}: {repr(lines[i])}')
    except Exception as e:
        print(f"检查文件时出错: {e}")

if __name__ == "__main__":
    file_path = "get_cgq_sources.py"
    check_file(file_path)
    print("\n正在修复缩进...")
    fix_indentation(file_path)
    print("\n修复后再次检查:")
    check_file(file_path)
