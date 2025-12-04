# -*- coding: utf-8 -*-

import sys

# 检查Python版本
print(f"Python版本: {sys.version}")

# 尝试用不同的编码读取文件
encodings_to_try = ['utf-8', 'gbk', 'latin-1']

for encoding in encodings_to_try:
    try:
        with open('collect_ipzy.py', 'r', encoding=encoding) as f:
            content = f.read()
        print(f"\n用{encoding}编码读取成功")
        
        # 检查第177行附近的内容
        lines = content.split('\n')
        if len(lines) > 177:
            line_177 = lines[176]  # 索引从0开始
            line_178 = lines[177] if len(lines) > 178 else ""
            
            print(f"第177行内容: {repr(line_177)}")
            print(f"第178行内容: {repr(line_178)}")
            
            # 检查字符
            print("第177行字符分析:")
            for i, char in enumerate(line_177):
                print(f"  位置{i}: 字符{repr(char)}, ASCII值{ord(char)}")
                
    except Exception as e:
        print(f"用{encoding}编码读取失败: {e}")
