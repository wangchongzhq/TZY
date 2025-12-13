#!/usr/bin/env python3

import re

# 导入原始的CHANNEL_CATEGORIES字典
from IPTV import CHANNEL_CATEGORIES, CHANNEL_TO_CATEGORY

# 检查4K频道列表中是否有不包含4K/8K/超高清/2160关键词的频道
print("检查4K频道列表中是否有不包含4K/8K/超高清/2160关键词的频道：")
print("=" * 80)

list_4k_channels = CHANNEL_CATEGORIES.get("4K频道", [])
problem_channels = []

for channel in list_4k_channels:
    has_4k_keyword = ("4K" in channel or "4k" in channel or 
                     "8K" in channel or "8k" in channel or
                     "超高清" in channel or "2160" in channel)
    if not has_4k_keyword:
        problem_channels.append(channel)

if problem_channels:
    print(f"发现 {len(problem_channels)} 个问题频道：")
    for channel in problem_channels:
        print(f"  - {channel}")
else:
    print("没有发现问题频道。")

print("\n检查CHANNEL_TO_CATEGORY字典中是否有普通频道被映射到4K频道：")
print("=" * 80)

wrong_mappings = []
for channel, category in CHANNEL_TO_CATEGORY.items():
    if category == "4K频道":
        has_4k_keyword = ("4K" in channel or "4k" in channel or 
                         "8K" in channel or "8k" in channel or
                         "超高清" in channel or "2160" in channel)
        if not has_4k_keyword:
            wrong_mappings.append((channel, category))

if wrong_mappings:
    print(f"发现 {len(wrong_mappings)} 个错误映射：")
    for channel, category in wrong_mappings:
        print(f"  - {channel} -> {category}")
else:
    print("没有发现错误映射。")

print("\n检查翡翠台相关频道：")
print("=" * 80)

for channel, category in CHANNEL_TO_CATEGORY.items():
    if "翡翠" in channel:
        print(f"  - {channel} -> {category}")
