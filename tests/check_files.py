import os

# 查看当前目录结构
print("当前目录文件结构:")
for file in os.listdir('.'):
    print(f"  {file}")

# 检查输出目录
print("\n输出目录文件结构:")
if os.path.exists('output'):
    for file in os.listdir('output'):
        print(f"  {file}")
else:
    print("  输出目录不存在")

# 检查是否生成了wrong_4k_channels.txt文件
print("\n检查wrong_4k_channels.txt是否存在:")
if os.path.exists('wrong_4k_channels.txt'):
    print("  文件存在")
    with open('wrong_4k_channels.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"  文件内容长度: {len(content)} 字符")
    print("  文件前500字符:")
    print(content[:500])
else:
    print("  文件不存在")