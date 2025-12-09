import re

# 打开文件并读取内容
with open('jieguo.m3u', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# 搜索CCTV16相关内容
print('=== 检查CCTV16 4K频道 ===')

# 统计所有CCTV16频道
cctv16_pattern = re.compile(r'#EXTINF:.*CCTV16.*\n', re.IGNORECASE)
cctv16_matches = cctv16_pattern.findall(content)
print(f'找到 {len(cctv16_matches)} 个CCTV16相关频道')

# 搜索包含4K的CCTV16频道
cctv16_4k_pattern = re.compile(r'#EXTINF:.*CCTV16.*4K.*\n|#EXTINF:.*4K.*CCTV16.*\n', re.IGNORECASE)
cctv16_4k_matches = cctv16_4k_pattern.findall(content)
print(f'找到 {len(cctv16_4k_matches)} 个CCTV16 4K相关频道')

# 显示前几个CCTV16 4K频道
if cctv16_4k_matches:
    print('\n前几个CCTV16 4K频道:')
    for match in cctv16_4k_matches[:5]:
        print(match.strip())

# 搜索4K频道分组
print('\n=== 检查4K频道分组 ===')
group_pattern = re.compile(r'group-title=["\'].*4K.*["\']', re.IGNORECASE)
group_matches = group_pattern.findall(content)
if group_matches:
    print(f'找到 {len(set(group_matches))} 种4K频道分组:')
    for group in set(group_matches):
        print(f'  - {group}')

print('\n检查完成！')
