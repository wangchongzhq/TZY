#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证4K频道归类效果的脚本
"""

import os

# 检查输出目录是否存在
output_dir = "output"
if not os.path.exists(output_dir):
    print(f"错误：未找到output目录")
    exit(1)

# 检查iptv.m3u文件是否存在
m3u_file = os.path.join(output_dir, "iptv.m3u")
if not os.path.exists(m3u_file):
    print(f"错误：未找到{os.path.abspath(m3u_file)}文件")
    exit(1)

# 打开生成的m3u文件
with open(m3u_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 将内容按#EXTINF分割，这样每个频道信息都在一个部分中
sections = content.split('#EXTINF:')

# 统计4K频道类别中的频道数量
print('检查4K频道类别中的频道数量:')
count_4k_channel = 0
for section in sections[1:]:  # 跳过第一个空部分
    if 'group-title="4K频道"' in section:
        count_4k_channel += 1
print(f'4K频道类别中的频道数量: {count_4k_channel}')

# 检查其他类别中是否包含4K频道
print('\n检查其他类别中是否包含4K频道:')
other_categories_with_4k = []
for section in sections[1:]:  # 跳过第一个空部分
    if 'group-title' in section:
        # 提取group-title
        if 'group-title="' in section:
            group_title_start = section.index('group-title="') + len('group-title="')
            group_title_end = section.index('"', group_title_start)
            group_title = section[group_title_start:group_title_end]
        else:
            continue
        
        # 检查是否包含4K且不是4K频道类别
        if group_title != '4K频道' and '4K' in section:
            other_categories_with_4k.append(group_title)

# 去重并输出结果
if other_categories_with_4k:
    unique_categories = sorted(list(set(other_categories_with_4k)))
    print(f'其他类别中包含4K的频道类别: {unique_categories}')
    
    # 收集所有相关频道
    relevant_channels = []
    for section in sections[1:]:
        for category in unique_categories:
            if f'group-title="{category}"' in section and '4K' in section:
                relevant_channels.append('#EXTINF:' + section.split('\n')[0].strip())
    
    # 输出具体的频道信息，限制数量
    print(f'\n具体的频道信息（共 {len(relevant_channels)} 个频道）:')
    # 只显示前20个
    for i, channel_line in enumerate(relevant_channels[:20]):
        print(f'  {i+1}. {channel_line}')
    if len(relevant_channels) > 20:
        print(f'  ... 还有 {len(relevant_channels) - 20} 个频道未显示')
else:
    print('其他类别中没有发现4K频道')

# 检查是否所有包含4K的频道都属于4K频道类别
print('\n检查是否所有包含4K的频道都属于4K频道类别:')
all_4k_in_one_category = True
fourk_not_in_category = []
for section in sections[1:]:
    if '4K' in section and 'group-title="4K频道"' not in section:
        fourk_not_in_category.append('#EXTINF:' + section.split('\n')[0].strip())
        all_4k_in_one_category = False

if not all_4k_in_one_category:
    print(f'发现 {len(fourk_not_in_category)} 个4K频道不在4K频道类别中')
    # 只显示前20个
    for i, channel_line in enumerate(fourk_not_in_category[:20]):
        print(f'  {i+1}. {channel_line}')
    if len(fourk_not_in_category) > 20:
        print(f'  ... 还有 {len(fourk_not_in_category) - 20} 个频道未显示')
    print('还有4K频道分散在其他类别中')
else:
    print('所有包含4K的频道都已集中在4K频道类别中')

