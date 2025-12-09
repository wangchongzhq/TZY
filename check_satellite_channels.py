#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

# 读取M3U文件
with open('jieguo.m3u', 'r', encoding='utf-8') as f:
    content = f.read()

# 更简单的方法来处理频道信息
lines = content.split('\n')
satellite_channels = []

for i in range(len(lines)):
    if lines[i].startswith('#EXTINF:-1'):
        # 提取频道信息
        line = lines[i]
        # 提取group-title
        group_match = re.search(r'group-title="([^"]+)"', line)
        if group_match and group_match.group(1) == '卫视频道':
            # 提取频道名称
            name_match = re.search(r',([^\n]+)$', line)
            if name_match:
                channel_name = name_match.group(1)
                # 获取URL
                if i+1 < len(lines):
                    url = lines[i+1]
                    satellite_channels.append((channel_name, url))

print(f"卫视频道总数: {len(satellite_channels)}")
print("前20个卫视频道:")
for i, (channel_name, url) in enumerate(satellite_channels[:20]):
    print(f"{i+1}. {channel_name} -> {url[:50]}...")

# 搜索特定的卫视频道
print("\n查找特定卫视频道:")
target_channels = ['北京卫视', '浙江卫视', '东方卫视', '湖南卫视', '江苏卫视']
for channel_name, url in satellite_channels:
    for target in target_channels:
        if target in channel_name:
            print(f"找到: {channel_name} -> {url}")
