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

def analyze_dict(dict_obj, name, file_name):
    """分析字典内容"""
    if not dict_obj:
        print(f"✗ 无法从 {file_name} 中提取 {name}")
        return False
    
    print(f"✓ 从 {file_name} 中成功提取 {name}")
    print(f"  - 包含 {len(dict_obj)} 个条目")
    
    return True

def check_self_aliases(mapping_dict, file_name):
    """检查频道映射中是否包含自别名"""
    if not mapping_dict:
        return
    
    print(f"\n检查 {file_name} 中的自别名:")
    missing_self_aliases = []
    
    for channel, aliases in mapping_dict.items():
        if channel not in aliases:
            missing_self_aliases.append(channel)
    
    if missing_self_aliases:
        print(f"  - 以下频道缺少自别名: {missing_self_aliases[:10]}")
        if len(missing_self_aliases) > 10:
            print(f"    ... 共 {len(missing_self_aliases)} 个频道")
    else:
        print(f"  - 所有频道都包含自别名")

def main():
    iptv_path = 'IPTV.py'
    
    # 检查文件是否存在
    if not os.path.exists(iptv_path):
        print(f"错误: 找不到文件 {iptv_path}")
        return
    
    print(f"开始分析 {iptv_path} 中的配置...")
    
    # 提取IPTV.py中的字典
    iptv_categories = extract_dict_from_file(iptv_path, 'CHANNEL_CATEGORIES')
    iptv_mapping = extract_dict_from_file(iptv_path, 'CHANNEL_MAPPING')
    
    # 分析提取的字典
    analyze_dict(iptv_categories, 'CHANNEL_CATEGORIES', 'IPTV.py')
    analyze_dict(iptv_mapping, 'CHANNEL_MAPPING', 'IPTV.py')
    
    # 检查自别名
    check_self_aliases(iptv_mapping, 'IPTV.py')

if __name__ == "__main__":
    main()
