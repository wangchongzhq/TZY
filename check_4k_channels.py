# 查看4K频道部分的内容
with open('output/iptv.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找4K频道部分
start_pos = content.find('#4K频道#')
if start_pos != -1:
    # 提取4K频道部分的前100行
    lines = content[start_pos:].split('\n')
    print("=== 4K频道部分内容 ===")
    for i, line in enumerate(lines[:100]):
        print(f"{i+1}: {line}")
    print(f"... 共 {len(lines)} 行")
else:
    print("未找到4K频道部分")

# 统计4K频道数量
fourk_lines = [line for line in content.split('\n') if line and not line.startswith('#') and ('4K' in line or '4k' in line)]
print(f"\n=== 统计信息 ===")
print(f"包含4K/4k的频道数量: {len(fourk_lines)}")
