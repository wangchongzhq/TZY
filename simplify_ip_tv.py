#!/usr/bin/env python3
"""
精简IP-TV.py文件的脚本
"""

def simplify_file():
    with open('IP-TV.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    simplified_lines = []
    blank_line_count = 0
    
    for line in lines:
        # 移除行尾空白字符
        line = line.rstrip()
        
        # 如果是空行，计数但不立即添加
        if not line:
            blank_line_count += 1
            # 最多保留一个连续空白行
            if blank_line_count <= 1:
                simplified_lines.append("\n")
            continue
        else:
            blank_line_count = 0
        
        # 1. 移除不必要的导入
        if line.strip() in ['import os', 'import threading']:
            continue
        
        # 2. 移除debug级别日志
        if 'logger.debug(' in line:
            continue
        
        # 3. 保留其他内容
        simplified_lines.append(line + "\n")
    
    # 保存精简后的文件
    with open('IP-TV_simplified.py', 'w', encoding='utf-8') as f:
        f.writelines(simplified_lines)
    
    print("文件精简完成，已保存为 IP-TV_simplified.py")

if __name__ == "__main__":
    simplify_file()