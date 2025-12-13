import json

# 读取配置文件
with open('config/config.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 修复4K频道分类：只保留真正的4K频道
fixed_4k_channels = []
for channel in data['channels']['categories']['4K频道']:
    if any(kw in channel for kw in ['4K', '4k', '8K', '8k', '超高清']) or channel.startswith('CCTV16'):
        fixed_4k_channels.append(channel)

# 更新配置
print(f"修复前4K频道数量: {len(data['channels']['categories']['4K频道'])}")
print(f"修复后4K频道数量: {len(fixed_4k_channels)}")
print(f"移除的非4K频道: {len(data['channels']['categories']['4K频道']) - len(fixed_4k_channels)}")

data['channels']['categories']['4K频道'] = fixed_4k_channels

# 保存修复后的配置
with open('config/config.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n修复后的4K频道列表:")
for channel in fixed_4k_channels:
    print(f"  - {channel}")
