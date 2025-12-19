#!/usr/bin/env python3

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入配置
import IPTV

print("=== 验证IPTV频道配置 ===")
print()

# 验证 CHANNEL_CATEGORIES
print("1. 验证 CHANNEL_CATEGORIES：")
if isinstance(IPTV.CHANNEL_CATEGORIES, dict):
    print(f"   ✓ CHANNEL_CATEGORIES 已定义，包含 {len(IPTV.CHANNEL_CATEGORIES)} 个类别")
    for category, channels in IPTV.CHANNEL_CATEGORIES.items():
        print(f"     - {category}: {len(channels)} 个频道")
else:
    print("   ✗ CHANNEL_CATEGORIES 不是有效的字典类型")

print()

# 验证 CHANNEL_MAPPING
print("2. 验证 CHANNEL_MAPPING：")
if isinstance(IPTV.CHANNEL_MAPPING, dict):
    print(f"   ✓ CHANNEL_MAPPING 已定义，包含 {len(IPTV.CHANNEL_MAPPING)} 个频道映射")
    
    # 检查自别名
    missing_self_aliases = []
    for channel, aliases in IPTV.CHANNEL_MAPPING.items():
        if channel not in aliases:
            missing_self_aliases.append(channel)
    
    if missing_self_aliases:
        print(f"   ✗ 以下频道缺少自别名: {missing_self_aliases[:10]}")
        if len(missing_self_aliases) > 10:
            print(f"     ... 共 {len(missing_self_aliases)} 个频道")
    else:
        print("   ✓ 所有频道都包含自别名")
else:
    print("   ✗ CHANNEL_MAPPING 不是有效的字典类型")

print()

# 验证山东教育频道的别名
try:
    print("3. 验证山东教育频道的别名：")
    iptv_aliases = IPTV.CHANNEL_MAPPING.get("山东教育", [])
    if iptv_aliases:
        print(f"   ✓ 山东教育频道的别名已定义")
        print(f"     别名: {sorted(iptv_aliases)}")
    else:
        print(f"   ✗ 山东教育频道的别名未定义或为空")
except Exception as e:
    print(f"   ✗ 验证山东教育频道时出错: {e}")

print()

print("=== 验证完成 ===")
