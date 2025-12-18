#!/usr/bin/env python3

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入IPTV模块
import IPTV

print("=== 验证频道配置 ===")
print()

# 验证 CHANNEL_CATEGORIES
print("1. 验证 CHANNEL_CATEGORIES：")
print(f"   ✓ CHANNEL_CATEGORIES 包含 {len(IPTV.CHANNEL_CATEGORIES)} 个类别")
for category, channels in sorted(IPTV.CHANNEL_CATEGORIES.items()):
    print(f"     - {category}: {len(channels)} 个频道")

print()

# 验证 CHANNEL_MAPPING
print("2. 验证 CHANNEL_MAPPING：")
print(f"   ✓ CHANNEL_MAPPING 包含 {len(IPTV.CHANNEL_MAPPING)} 个频道映射")

# 检查是否有频道名作为别名的情况
self_aliases = []
for channel, aliases in IPTV.CHANNEL_MAPPING.items():
    if channel in aliases:
        self_aliases.append(channel)

if self_aliases:
    print(f"   ✗ 发现 {len(self_aliases)} 个频道将自身作为别名:")
    for channel in self_aliases[:5]:  # 只显示前5个
        print(f"     - {channel}")
    if len(self_aliases) > 5:
        print(f"     - ... 还有 {len(self_aliases) - 5} 个")
else:
    print("   ✓ 没有发现频道将自身作为别名的情况")

print()

# 验证山东教育频道的别名
try:
    print("3. 验证山东教育频道的别名：")
    iptv_aliases = IPTV.CHANNEL_MAPPING.get("山东教育", [])
    print(f"   ✓ 山东教育频道的别名: {sorted(iptv_aliases)}")
except Exception as e:
    print(f"   ✗ 验证山东教育频道时出错: {e}")

print()

print("=== 验证完成 ===")
