#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查生成的M3U文件中是否包含4K频道分类
"""

import os
import re

print("=== 检查生成的M3U文件中的4K频道 ===")

# 检查jieguo.m3u文件
m3u_file = "jieguo.m3u"
if not os.path.exists(m3u_file):
    print(f"❌ {m3u_file} 文件不存在")
    exit(1)

print(f"✅ 找到 {m3u_file} 文件")
print(f"📁 文件大小: {os.path.getsize(m3u_file)} 字节")

# 读取文件内容
try:
    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print("✅ 成功读取文件内容")
    
    # 查找4K频道分类
    print("\n=== 搜索4K频道分类 ===")
    
    # 查找所有group-title
    group_titles = set()
    group_pattern = re.compile(r'group-title="([^"]+)"')
    for match in group_pattern.finditer(content):
        group_titles.add(match.group(1))
    
    print(f"📊 找到 {len(group_titles)} 个分类")
    
    # 检查是否存在"4K频道"分类
    has_4k_category = "4K频道" in group_titles
    print(f"{'✅' if has_4k_category else '❌'} {'找到' if has_4k_category else '没有找到'}'4K频道'分类")
    
    # 一次性遍历文件，收集4K频道信息
    category_4k_channels = []
    name_4k_channels = []
    
    # 使用正则表达式匹配所有频道信息
    channel_pattern = re.compile(r'#EXTINF:.*?group-title="([^"]+)".*?,([^\n]+)\n([^\n]+)')
    for match in channel_pattern.finditer(content):
        group_title, channel_name, url = match.groups()
        
        # 收集属于"4K频道"分类的频道
        if group_title == "4K频道":
            category_4k_channels.append(channel_name.strip())
        
        # 收集名称包含4K的频道
        if '4K' in channel_name or '4k' in channel_name:
            name_4k_channels.append((channel_name.strip(), group_title))
    
    # 输出4K频道分类的统计信息
    if category_4k_channels:
        print(f"📺 4K频道数量: {len(category_4k_channels)}")
        print("📋 前20个4K频道:")
        for i, channel in enumerate(category_4k_channels[:20]):
            print(f"  {i+1}. {channel}")
        if len(category_4k_channels) > 20:
            print(f"  ... 还有 {len(category_4k_channels) - 20} 个4K频道")
    
    # 输出名称包含4K的频道统计信息
    print("\n=== 搜索名称包含4K的频道 ===")
    if name_4k_channels:
        print(f"✅ 找到 {len(name_4k_channels)} 个名称包含4K的频道")
        print("📋 名称包含4K的频道（显示频道名称和分类）:")
        for i, (channel_name, group_title) in enumerate(name_4k_channels[:20]):
            print(f"  {i+1}. '{channel_name}' -> 分类: '{group_title}'")
        if len(name_4k_channels) > 20:
            print(f"  ... 还有 {len(name_4k_channels) - 20} 个类似频道")
    else:
        print("❌ 没有找到名称包含4K的频道")
    
    print("\n=== 检查完成 ===")
    
except Exception as e:
    print(f"❌ 读取文件时出错: {e}")
    import traceback
    traceback.print_exc()
