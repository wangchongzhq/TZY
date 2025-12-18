#!/usr/bin/env python3

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入两个文件的配置
import IPTV
import tvzy

print("=== 验证频道配置合并结果 ===")
print()

# 验证 CHANNEL_CATEGORIES
print("1. 验证 CHANNEL_CATEGORIES：")
if IPTV.CHANNEL_CATEGORIES == tvzy.CHANNEL_CATEGORIES:
    print("   ✓ CHANNEL_CATEGORIES 在两个文件中完全相同")
else:
    print("   ✗ CHANNEL_CATEGORIES 在两个文件中存在差异")
    # 找出差异
    for category in set(IPTV.CHANNEL_CATEGORIES.keys()) | set(tvzy.CHANNEL_CATEGORIES.keys()):
        if category not in IPTV.CHANNEL_CATEGORIES:
            print(f"     - 仅在 tvzy.py 中存在类别: {category}")
        elif category not in tvzy.CHANNEL_CATEGORIES:
            print(f"     - 仅在 IPTV.py 中存在类别: {category}")
        else:
            diff1 = set(IPTV.CHANNEL_CATEGORIES[category]) - set(tvzy.CHANNEL_CATEGORIES[category])
            diff2 = set(tvzy.CHANNEL_CATEGORIES[category]) - set(IPTV.CHANNEL_CATEGORIES[category])
            if diff1:
                print(f"     - 类别 {category} 中，仅在 IPTV.py 中存在频道: {diff1}")
            if diff2:
                print(f"     - 类别 {category} 中，仅在 tvzy.py 中存在频道: {diff2}")

print()

# 验证 CHANNEL_MAPPING
print("2. 验证 CHANNEL_MAPPING：")
# 注意：tvzy.py 的 CHANNEL_MAPPING 是在运行时生成的，包含了 additional_mappings
# 而 IPTV.py 的 CHANNEL_MAPPING 是直接定义的

# 比较映射键是否相同
mapping_keys_same = set(IPTV.CHANNEL_MAPPING.keys()) == set(tvzy.CHANNEL_MAPPING.keys())

# 比较每个频道的别名是否相同（不考虑顺序）
alias_sets_same = True
different_channels = []

if mapping_keys_same:
    for channel in IPTV.CHANNEL_MAPPING.keys():
        if set(IPTV.CHANNEL_MAPPING[channel]) != set(tvzy.CHANNEL_MAPPING[channel]):
            alias_sets_same = False
            different_channels.append(channel)

if mapping_keys_same and alias_sets_same:
    print("   ✓ CHANNEL_MAPPING 在两个文件中完全相同")
else:
    print("   ✗ CHANNEL_MAPPING 在两个文件中存在差异")
    if not mapping_keys_same:
        # 找出差异
        all_channels = set(IPTV.CHANNEL_MAPPING.keys()) | set(tvzy.CHANNEL_MAPPING.keys())
        for channel in all_channels:
            if channel not in IPTV.CHANNEL_MAPPING:
                print(f"     - 仅在 tvzy.py 中存在频道映射: {channel}")
            elif channel not in tvzy.CHANNEL_MAPPING:
                print(f"     - 仅在 IPTV.py 中存在频道映射: {channel}")
    
    if different_channels:
        for channel in different_channels:
            print(f"     - 频道 {channel} 的别名存在差异")
            print(f"       IPTV.py: {sorted(IPTV.CHANNEL_MAPPING[channel])}")
            print(f"       tvzy.py: {sorted(tvzy.CHANNEL_MAPPING[channel])}")

print()

# 验证山东教育频道的别名
try:
    print("3. 验证山东教育频道的别名：")
    iptv_aliases = IPTV.CHANNEL_MAPPING.get("山东教育", [])
    tvzy_aliases = tvzy.CHANNEL_MAPPING.get("山东教育", [])
    if set(iptv_aliases) == set(tvzy_aliases):
        print(f"   ✓ 山东教育频道的别名在两个文件中完全相同")
        print(f"     别名: {sorted(iptv_aliases)}")
    else:
        print(f"   ✗ 山东教育频道的别名在两个文件中存在差异")
        print(f"     IPTV.py: {sorted(iptv_aliases)}")
        print(f"     tvzy.py: {sorted(tvzy_aliases)}")
except Exception as e:
    print(f"   ✗ 验证山东教育频道时出错: {e}")

print()

print("=== 验证完成 ===")
