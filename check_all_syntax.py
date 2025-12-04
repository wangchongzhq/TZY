#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import ast
import glob

# 获取当前目录下所有Python文件
python_files = glob.glob('*.py')

# 检查每个Python文件的语法
print("正在检查Python文件语法...")
print("=" * 50)

error_count = 0
success_count = 0

for file in python_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print(f"✓ {file}: 语法正确")
        success_count += 1
    except SyntaxError as e:
        print(f"✗ {file}: 语法错误")
        print(f"  行号: {e.lineno}, 偏移量: {e.offset}")
        print(f"  错误信息: {e.msg}")
        error_count += 1
    except UnicodeDecodeError as e:
        print(f"✗ {file}: 编码错误")
        print(f"  错误信息: {e}")
        error_count += 1
    except Exception as e:
        print(f"✗ {file}: 其他错误")
        print(f"  错误信息: {e}")
        error_count += 1
    print()

print("=" * 50)
print(f"检查完成: {success_count} 个文件语法正确, {error_count} 个文件有错误")
