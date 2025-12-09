#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

with open('config/config.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

categories = data['channels']['categories']
mappings = data['channels']['name_mappings']

# 获取所有分类中的频道
all_channels = set()
for category in categories:
    for channel in categories[category]:
        all_channels.add(channel)

# 检查别名键是否都在频道分类中
print("检查别名键在频道分类中是否存在:")
missing_keys = []
for key in mappings:
    if key not in all_channels:
        missing_keys.append(key)

if missing_keys:
    print(f"  发现 {len(missing_keys)} 个别名键不在频道分类中:")
    for key in missing_keys:
        print(f"    - {key}")
else:
    print("  ✓ 所有别名键都在频道分类中存在")

# 检查别名值是否都在频道分类中
print("\n检查别名值在频道分类中是否存在:")
missing_aliases = []
for key in mappings:
    for alias in mappings[key]:
        if alias not in all_channels:
            missing_aliases.append(alias)

if missing_aliases:
    print(f"  发现 {len(missing_aliases)} 个别名值不在频道分类中:")
    for alias in missing_aliases:
        print(f"    - {alias}")
else:
    print("  ✓ 所有别名值都在频道分类中存在")

print("\n检查完成！")