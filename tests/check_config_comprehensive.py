#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re


def check_config_comprehensive():
    print("开始全面检查config.json文件...")
    
    # 1. 检查JSON语法
    try:
        with open('config/config.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✓ JSON语法正确")
    except json.JSONDecodeError as e:
        print(f"✗ JSON语法错误: {e}")
        return
    except Exception as e:
        print(f"✗ 读取文件时出错: {e}")
        return
    
    # 2. 检查基本结构
    channels = data.get('channels', {})
    categories = channels.get('categories', {})
    name_mappings = channels.get('name_mappings', {})
    
    print(f"\n频道分类数量: {len(categories)}")
    print(f"频道别名映射数量: {len(name_mappings)}")
    
    # 3. 检查分类中的频道列表
    all_channels = []
    duplicate_channels = []
    
    for category, channel_list in categories.items():
        if not isinstance(channel_list, list):
            print(f"✗ 分类 '{category}' 不是列表类型")
            continue
        
        # 检查重复频道
        seen = set()
        for channel in channel_list:
            if channel in seen:
                duplicate_channels.append((category, channel))
            seen.add(channel)
            all_channels.append((category, channel))
    
    if duplicate_channels:
        print("\n✗ 发现重复频道:")
        for category, channel in duplicate_channels:
            print(f"  - {channel} (在分类 '{category}' 中重复)")
    else:
        print("\n✓ 没有发现重复频道")
    
    # 4. 检查别名映射的一致性
    mapping_keys = set(name_mappings.keys())
    category_channels = set(channel for _, channel in all_channels)
    
    # 检查别名键是否都在频道列表中
    missing_in_categories = mapping_keys - category_channels
    if missing_in_categories:
        print("\n✗ 发现别名键不在任何频道分类中:")
        for channel in missing_in_categories:
            print(f"  - {channel}")
    else:
        print("\n✓ 所有别名键都在频道分类中存在")
    
    # 5. 检查手动删除频道后可能残留的别名映射
    # 获取所有在别名映射中引用的频道
    all_alias_channels = []
    for channel, aliases in name_mappings.items():
        all_alias_channels.extend(aliases)
    
    # 检查这些别名频道是否都在任何分类中存在
    all_alias_channels_set = set(all_alias_channels)
    missing_alias_channels = all_alias_channels_set - category_channels
    if missing_alias_channels:
        print("\n✗ 发现别名引用的频道不在任何频道分类中:")
        for channel in missing_alias_channels:
            print(f"  - {channel}")
    else:
        print("\n✓ 所有别名引用的频道都在频道分类中存在")
    
    # 5. 检查是否有空分类
    empty_categories = [category for category, channel_list in categories.items() 
                       if isinstance(channel_list, list) and len(channel_list) == 0]
    if empty_categories:
        print("\n✗ 发现空分类:")
        for category in empty_categories:
            print(f"  - {category}")
    else:
        print("\n✓ 没有发现空分类")
    
    # 6. 检查频道名称格式
    print("\n检查频道名称格式...")
    for category, channel in all_channels:
        # 检查是否有多余空格
        if channel.strip() != channel:
            print(f"  - 频道 '{channel}' (分类 '{category}') 前后有多余空格")
        # 检查是否有特殊字符
        if re.search(r'[^\w\u4e00-\u9fa5\s\-_()（）]', channel):
            print(f"  - 频道 '{channel}' (分类 '{category}') 包含可能的特殊字符")
    
    print("\n检查完成！")


if __name__ == "__main__":
    check_config_comprehensive()