#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证不同类型的4K频道是否都被正确归类到4K频道分类中
"""

import os

def verify_4k_categorization():
    """验证4K频道的分类情况"""
    
    m3u_file = "output/iptv.m3u"
    if not os.path.exists(m3u_file):
        print(f"文件 {m3u_file} 不存在")
        return
    
    print("=== 验证4K频道分类情况 ===")
    
    # 读取M3U文件
    with open(m3u_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    # 提取所有频道信息：频道名称 -> 分类
    channel_categories = {}
    current_category = None
    
    for i, line in enumerate(lines):
        if line.startswith('#EXTINF'):
            # 提取频道名称
            if 'group-title="' in line:
                # 提取分类
                group_title_start = line.find('group-title="') + len('group-title="')
                group_title_end = line.find('"', group_title_start)
                current_category = line[group_title_start:group_title_end]
            
            # 提取频道名称
            if ',' in line:
                channel_name = line.split(',')[-1]
                if channel_name:
                    channel_categories[channel_name] = current_category
    
    # 统计不同类型的4K频道及其分类
    types_to_check = ["4K", "4k", "8K", "8k", "超高清", "2160"]
    
    print("\n不同类型4K频道的分类情况:")
    
    for type_key in types_to_check:
        print(f"\n- 检查包含 '{type_key}' 的频道:")
        
        # 找到包含该类型的所有频道
        channels_with_type = [name for name in channel_categories.keys() if type_key in name]
        
        if not channels_with_type:
            print(f"  未找到包含 '{type_key}' 的频道")
            continue
        
        print(f"  共找到 {len(channels_with_type)} 个频道")
        
        # 统计这些频道的分类情况
        category_stats = {}
        for channel_name in channels_with_type:
            category = channel_categories[channel_name]
            category_stats[category] = category_stats.get(category, 0) + 1
        
        # 输出分类统计
        print(f"  分类情况:")
        for category, count in category_stats.items():
            print(f"    {category}: {count}个频道")
        
        # 输出前3个示例
        print(f"  示例频道:")
        for i, channel_name in enumerate(channels_with_type[:3]):
            category = channel_categories[channel_name]
            print(f"    {i+1}. {channel_name} -> 分类: {category}")
    
    # 总结
    print("\n=== 总结 ===")
    total_4k_channels = 0
    correctly_categorized = 0
    
    for type_key in types_to_check:
        channels_with_type = [name for name in channel_categories.keys() if type_key in name]
        total_4k_channels += len(channels_with_type)
        
        for channel_name in channels_with_type:
            if channel_categories[channel_name] == "4K频道":
                correctly_categorized += 1
    
    print(f"总计找到 {total_4k_channels} 个包含4K相关标识的频道")
    print(f"其中 {correctly_categorized} 个被正确归类到4K频道分类")
    print(f"归类准确率: {correctly_categorized/total_4k_channels*100:.1f}%" if total_4k_channels > 0 else "没有找到相关频道")

if __name__ == "__main__":
    verify_4k_categorization()
