#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

def check_config():
    with open('config/config.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    categories = data.get('channels', {}).get('categories', {})
    print("所有频道分类:")
    for category in categories:
        print(f"  - {category}")
    
    # 检查音乐频道
    music_channel = categories.get('音乐频道')
    print(f"\n音乐频道配置: {music_channel}")
    
    # 检查是否有格式错误
    print("\n检查格式错误...")
    valid = True
    for category, channels in categories.items():
        if not isinstance(channels, list):
            print(f"错误: 分类 '{category}' 的值不是列表类型")
            valid = False
    
    if valid:
        print("所有分类格式正确")
    
    # 检查港澳频道
    print(f"\n港澳频道配置: {categories.get('港澳频道')}")

if __name__ == "__main__":
    check_config()