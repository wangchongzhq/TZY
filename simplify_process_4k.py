#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精简process_4k_channels.py文件的脚本
"""

import re

def simplify_file():
    """精简process_4k_channels.py文件"""
    input_file = 'process_4k_channels.py'
    output_file = 'process_4k_channels_simplified.py'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    simplified_lines = []
    blank_line_count = 0
    
    for line in lines:
        # 去除行尾空白
        stripped_line = line.rstrip()
        
        # 跳过包含print语句的行
        if re.search(r'\bprint\s*\(', stripped_line):
            continue
        
        # 跳过调试相关的代码行
        if re.search(r'\bdebug\b|\bDEBUG\b', stripped_line, re.IGNORECASE):
            continue
        
        # 简化异常处理
        stripped_line = re.sub(r'except Exception as e:\s*return\s*False,\s*None', 'except Exception: return False, None', stripped_line)
        stripped_line = re.sub(r'except Exception as e:\s*results\[url\]\s*=\s*{[^}]*}', 'except Exception: results[url] = {"valid": False, "speed_info": None}', stripped_line)
        stripped_line = re.sub(r'except:\s*sys\.exit\(1\)', 'except: sys.exit(1)', stripped_line)
        
        # 处理空行
        if not stripped_line:
            blank_line_count += 1
            if blank_line_count <= 1:
                simplified_lines.append('')
            continue
        else:
            blank_line_count = 0
        
        # 保留其他所有行
        simplified_lines.append(stripped_line)
    
    # 写入精简后的内容
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in simplified_lines:
            f.write(line + '\n')
    
    print(f"文件精简完成，已保存为 {output_file}")

if __name__ == "__main__":
    simplify_file()