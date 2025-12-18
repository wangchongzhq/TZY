#!/usr/bin/env python3

import ast
import os

# 读取文件内容
def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 从文件中提取特定的字典
def extract_dict_from_file(file_path, dict_name):
    content = read_file_content(file_path)
    tree = ast.parse(content)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == dict_name:
                    # 找到目标字典的定义
                    return ast.literal_eval(ast.Expression(body=node.value))
    
    return None

def compare_dicts(dict1, dict2, name):
    """比较两个字典是否完全相同"""
    if dict1 == dict2:
        print(f"✓ {name} 在两个文件中完全一致")
        return True
    else:
        print(f"✗ {name} 在两个文件中不一致")
        
        # 检查键是否相同
        keys1 = set(dict1.keys())
        keys2 = set(dict2.keys())
        
        if keys1 != keys2:
            print(f"  - 键差异: {keys1.symmetric_difference(keys2)}")
        
        # 检查每个键的值是否相同
        for key in keys1.intersection(keys2):
            if dict1[key] != dict2[key]:
                print(f"  - 键 '{key}' 的值不同")
                if isinstance(dict1[key], list) and isinstance(dict2[key], list):
                    # 详细比较列表差异
                    items1 = set(dict1[key])
                    items2 = set(dict2[key])
                    if items1 != items2:
                        print(f"    + {items1.difference(items2)}")
                        print(f"    - {items2.difference(items1)}")
        
        return False

def main():
    tvzy_path = 'tvzy.py'
    iptv_path = 'IPTV.py'
    
    # 检查文件是否存在
    if not os.path.exists(tvzy_path):
        print(f"错误: 找不到文件 {tvzy_path}")
        return
    
    if not os.path.exists(iptv_path):
        print(f"错误: 找不到文件 {iptv_path}")
        return
    
    print("开始比较CHANNEL_CATEGORIES和CHANNEL_MAPPING...")
    
    # 提取两个文件中的字典
    tvzy_categories = extract_dict_from_file(tvzy_path, 'CHANNEL_CATEGORIES')
    iptv_categories = extract_dict_from_file(iptv_path, 'CHANNEL_CATEGORIES')
    
    tvzy_mapping = extract_dict_from_file(tvzy_path, 'additional_mappings')
    iptv_mapping = extract_dict_from_file(iptv_path, 'CHANNEL_MAPPING')
    
    if tvzy_categories and iptv_categories:
        compare_dicts(tvzy_categories, iptv_categories, 'CHANNEL_CATEGORIES')
    else:
        print("✗ 无法提取CHANNEL_CATEGORIES")
    
    if tvzy_mapping and iptv_mapping:
        compare_dicts(tvzy_mapping, iptv_mapping, 'CHANNEL_MAPPING')
    else:
        print("✗ 无法提取CHANNEL_MAPPING")
    
    # 检查自别名
    if tvzy_mapping:
        print("\n检查tvzy.py中的自别名:")
        for channel, aliases in tvzy_mapping.items():
            if channel not in aliases:
                print(f"  - '{channel}' 缺少自别名")
    
    if iptv_mapping:
        print("\n检查IPTV.py中的自别名:")
        for channel, aliases in iptv_mapping.items():
            if channel not in aliases:
                print(f"  - '{channel}' 缺少自别名")

if __name__ == "__main__":
    main()
