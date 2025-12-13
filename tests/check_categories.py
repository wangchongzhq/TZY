import json

with open('config/config.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 检查频道分类配置
categories = data['channels']['categories']
print('可用分类:', list(categories.keys()))

# 检查4K频道分类
if '4K频道' in categories:
    print('\n4K频道分类包含', len(categories['4K频道']), '个频道:')
    for channel in categories['4K频道'][:15]:
        print(f'  - {channel}')
    if len(categories['4K频道']) > 15:
        print(f'  ... 还有{len(categories['4K频道']) - 15}个频道')

# 检查央视频道分类
if '央视频道' in categories:
    print('\n央视频道分类包含', len(categories['央视频道']), '个频道:')
    for channel in categories['央视频道'][:10]:
        print(f'  - {channel}')
