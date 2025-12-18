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

def validate_channel_configs(file_path):
    """验证IPTV.py中的频道配置"""
    print(f"开始验证 {file_path} 中的频道配置...")
    
    # 提取字典
    categories = extract_dict_from_file(file_path, 'CHANNEL_CATEGORIES')
    mapping = extract_dict_from_file(file_path, 'CHANNEL_MAPPING')
    
    if categories:
        print(f"✓ 成功提取 CHANNEL_CATEGORIES")
        print(f"  - 共 {len(categories)} 个类别")
        
        # 检查类别中的频道是否都在CHANNEL_MAPPING中
        missing_channels = []
        for category, channels in categories.items():
            for channel in channels:
                if channel not in mapping:
                    missing_channels.append((category, channel))
        
        if missing_channels:
            print(f"✗ 发现 {len(missing_channels)} 个频道在 CHANNEL_CATEGORIES 中但不在 CHANNEL_MAPPING 中:")
            for category, channel in missing_channels[:10]:  # 只显示前10个
                print(f"    - {category}: {channel}")
            if len(missing_channels) > 10:
                print(f"    ... 还有 {len(missing_channels) - 10} 个")
        else:
            print("✓ 所有类别中的频道都在 CHANNEL_MAPPING 中")
    else:
        print("✗ 无法提取 CHANNEL_CATEGORIES")
    
    if mapping:
        print(f"\n✓ 成功提取 CHANNEL_MAPPING")
        print(f"  - 共 {len(mapping)} 个频道映射")
        
        # 检查是否有频道将自身作为别名
        self_aliases = []
        for channel, aliases in mapping.items():
            if channel in aliases:
                self_aliases.append(channel)
        
        if self_aliases:
            print(f"✗ 发现 {len(self_aliases)} 个频道将自身作为别名:")
            for channel in self_aliases[:10]:  # 只显示前10个
                print(f"    - {channel}")
            if len(self_aliases) > 10:
                print(f"    ... 还有 {len(self_aliases) - 10} 个")
        else:
            print("✓ 没有发现频道将自身作为别名的情况")
        
        # 检查是否有重复的别名
        alias_counts = {}
        for channel, aliases in mapping.items():
            for alias in aliases:
                if alias in alias_counts:
                    alias_counts[alias].append(channel)
                else:
                    alias_counts[alias] = [channel]
        
        duplicate_aliases = {alias: channels for alias, channels in alias_counts.items() if len(channels) > 1}
        if duplicate_aliases:
            print(f"✗ 发现 {len(duplicate_aliases)} 个别名被多个频道使用:")
            for alias, channels in list(duplicate_aliases.items())[:10]:  # 只显示前10个
                print(f"    - '{alias}' 被 {channels} 使用")
            if len(duplicate_aliases) > 10:
                print(f"    ... 还有 {len(duplicate_aliases) - 10} 个")
        else:
            print("✓ 没有发现重复的别名")
    else:
        print("✗ 无法提取 CHANNEL_MAPPING")

def main():
    iptv_path = 'IPTV.py'
    
    # 检查文件是否存在
    if not os.path.exists(iptv_path):
        print(f"错误: 找不到文件 {iptv_path}")
        return
    
    validate_channel_configs(iptv_path)

if __name__ == "__main__":
    main()
