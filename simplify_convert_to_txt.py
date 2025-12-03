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
        content = f.read()
    
    # 移除所有print语句
    content = re.sub(r'\bprint\s*\([^)]*\)\s*', '', content)
    
    # 移除空的if-else结构
    content = re.sub(r'if\s+[^:]+:\s*else:\s*', '', content)
    
    # 简化异常处理
    content = re.sub(r'except Exception as e:\s*print\(f"[^"]*\{e\}[^"]*"\)\s*return False', 'except Exception: return False', content)
    content = re.sub(r'except Exception as e:\s*return False', 'except Exception: return False', content)
    
    # 移除调试相关的代码行
    content = re.sub(r'.*\bdebug\b.*\n', '', content, flags=re.IGNORECASE)
    
    # 处理多余的空行
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    # 写入精简后的内容
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"文件精简完成，已保存为 {output_file}")

if __name__ == "__main__":
    simplify_file()