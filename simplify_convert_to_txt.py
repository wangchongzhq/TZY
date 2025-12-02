#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精简convert_to_txt.py文件的脚本
"""

import re

def simplify_file():
    """精简convert_to_txt.py文件"""
    input_file = 'convert_to_txt.py'
    output_file = 'convert_to_txt_simplified.py'
    
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
        stripped_line = re.sub(r'except Exception as e:\s*print\(f"[^"\n]*\{e\}[^"\n]*"\)\s*return False', 'except Exception: return False', stripped_line)
        stripped_line = re.sub(r'except UnicodeDecodeError:\s*try:', 'except UnicodeDecodeError: try:', stripped_line)
        stripped_line = re.sub(r'except Exception as e:\s*return False', 'except Exception: return False', stripped_line)
        
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