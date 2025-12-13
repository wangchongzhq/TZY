with open('output/iptv.txt', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')[:100]  # 读取前100行

print('=== 输出文件前100行内容 ===')
for line in lines:
    if line:
        print(line)

# 检查特定频道名称
print('\n=== 检查特定频道名称 ===')
channel_names = []
for line in content.split('\n'):
    if 'EXTINF' in line:
        name = line.split(',')[-1]
        channel_names.append(name)

# 显示包含特定关键词的频道
keywords = ['CCTV1', 'CCTV2', '北京卫视', '湖南卫视', '4K']
for name in sorted(list(set(channel_names))):
    for keyword in keywords:
        if keyword in name:
            print(name)
            break
