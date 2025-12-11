#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查仓库中所有Python文件引用的文件是否实际存在
"""

import os
import re
import sys

# 获取当前脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 要检查的文件扩展名
CHECK_EXTENSIONS = ['.py']

# 排除的目录
EXCLUDE_DIRS = ['.git', '.github', '__pycache__', 'tests']

# 文件引用的正则表达式模式
FILE_REFERENCE_PATTERNS = [
    # 直接字符串引用
    r"['"]([^'"]+)['"]",
    # open函数调用
    r"open\(['"]([^'"]+)['"]",
    # 文件操作相关的函数调用
    r"read_file\(['"]([^'"]+)['"]",
    r"write_file\(['"]([^'"]+)['"]",
    r"os\.path\.exists\(['"]([^'"]+)['"]",
    r"os\.path\.join\([^)]*['"]([^'"]+)['"][^)]*\)",
    # 配置文件路径
    r"config\.json|config\.yaml|sources\.json"
]

# 常见的文件名模式，可能是引用的文件
COMMON_FILE_PATTERNS = [
    r'\.m3u$',
    r'\.txt$',
    r'\.json$',
    r'\.yaml$',
    r'\.log$',
    r'\.py$',
]

def is_valid_file_path(path, base_dir):
    """检查文件路径是否有效"""
    if not path:
        return False
    
    # 忽略URL和绝对路径
    if path.startswith('http://') or path.startswith('https://') or os.path.isabs(path):
        return True
    
    # 构建完整路径
    full_path = os.path.join(base_dir, path)
    
    # 检查文件是否存在
    return os.path.exists(full_path)

def extract_file_references(content, base_dir):
    """从文件内容中提取可能的文件引用"""
    file_references = set()
    
    for pattern in FILE_REFERENCE_PATTERNS:
        matches = re.findall(pattern, content)
        for match in matches:
            # 如果匹配是元组，取第一个元素
            if isinstance(match, tuple):
                match = match[0]
            
            # 过滤掉空字符串和不符合常见文件模式的引用
            if match and any(re.search(fp, match) for fp in COMMON_FILE_PATTERNS):
                file_references.add(match)
    
    return file_references

def check_file(file_path):
    """检查单个文件中引用的文件是否实际存在"""
    invalid_references = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取文件引用
        file_references = extract_file_references(content, os.path.dirname(file_path))
        
        # 检查每个引用的文件是否存在
        for ref in file_references:
            if not is_valid_file_path(ref, os.path.dirname(file_path)):
                invalid_references.append(ref)
                
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
    
    return invalid_references

def main():
    """主函数"""
    print("开始检查仓库中无效的文件引用...")
    print("=" * 60)
    
    # 遍历仓库中的所有文件
    invalid_references_dict = {}
    
    for root, dirs, files in os.walk(SCRIPT_DIR):
        # 排除指定目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if any(file.endswith(ext) for ext in CHECK_EXTENSIONS):
                file_path = os.path.join(root, file)
                invalid_references = check_file(file_path)
                
                if invalid_references:
                    invalid_references_dict[file_path] = invalid_references
    
    # 打印结果
    if invalid_references_dict:
        print(f"找到 {len(invalid_references_dict)} 个文件包含无效的文件引用:")
        print("=" * 60)
        
        for file_path, references in invalid_references_dict.items():
            print(f"文件: {file_path}")
            for ref in references:
                print(f"  - {ref}")
            print()
    else:
        print("没有发现无效的文件引用!")
    
    print("检查完成。")

if __name__ == "__main__":
    main()