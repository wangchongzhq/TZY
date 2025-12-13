import os

# 检查output/iptv.txt文件是否存在
file_path = 'output/iptv.txt'

if os.path.exists(file_path):
    print(f"文件 '{file_path}' 存在")
    print(f"文件大小: {os.path.getsize(file_path)} 字节")
    print(f"最后修改时间: {os.path.getmtime(file_path)}")
    
    # 查看文件的前几行内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"文件内容长度: {len(content)} 字符")
        print("\n文件前几行内容:")
        lines = content.split('\n')[:10]
        for i, line in enumerate(lines, 1):
            print(f"{i}: {line}")
    except Exception as e:
        print(f"读取文件内容时出错: {e}")
else:
    print(f"文件 '{file_path}' 不存在")
