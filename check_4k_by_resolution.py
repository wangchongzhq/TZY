#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

# 读取M3U文件
with open('jieguo.m3u', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找包含分辨率信息的频道
# EXT-X-STREAM-INF标签中可能包含RES="1920x1080"等分辨率信息
stream_inf_pattern = re.compile(r'#EXT-X-STREAM-INF:.*?(RES="[^\"]+")', re.DOTALL)
res_matches = stream_inf_pattern.finditer(content)

# 统计不同分辨率的频道数量
resolution_count = {}
all_4k_channels = []

for match in res_matches:
    res_str = match.group(1)
    # 提取分辨率值
    res_value = re.search(r'RES="([^"]+)"', res_str).group(1)
    if res_value in resolution_count:
        resolution_count[res_value] += 1
    else:
        resolution_count[res_value] = 1
    # 检查是否为4K分辨率（宽度≥3840）
    if 'x' in res_value:
        width, height = map(int, res_value.split('x'))
        if width >= 3840 or height >= 2160:
            all_4k_channels.append(res_value)

print("不同分辨率频道数量:")
for res, count in sorted(resolution_count.items()):
    print(f"{res}: {count}个频道")

print(f"\n总4K频道数量（按分辨率）: {len(all_4k_channels)}")

# 检查所有频道的EXTINF信息，查找可能的4K频道
print("\n查找所有可能的4K频道（名称或描述中可能包含4K的频道）:")
channel_pattern = re.compile(r'#EXTINF:-1.*?,([^\n]+)\n([^\n]+)', re.DOTALL)
for match in channel_pattern.finditer(content):
    channel_name, url = match.groups()
    if '4K' in channel_name or 'UHD' in channel_name:
        print(f"{channel_name} -> {url[:100]}")
