import os

# 检查output/iptv.txt文件是否存在
file_path = 'output/iptv.txt'

if os.path.exists(file_path):
    print("文件存在")
    print("文件大小:", os.path.getsize(file_path), "字节")
    # 只读取第一行
    with open(file_path, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
    print("第一行内容:", first_line)
else:
    print("文件不存在")
