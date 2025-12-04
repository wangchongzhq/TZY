# -*- coding: utf-8 -*-

# 读取文件内容
with open('collect_ipzy.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找parse_m3u_content函数的位置
parse_m3u_content_index = content.find('def parse_m3u_content')
if parse_m3u_content_index == -1:
    print('未找到parse_m3u_content函数')
    exit(1)

# 检查函数定义前后的字符
start_index = max(0, parse_m3u_content_index - 10)
end_index = min(len(content), parse_m3u_content_index + 50)

print('检查parse_m3u_content函数附近的字符:')
for i in range(start_index, end_index):
    char = content[i]
    char_ord = ord(char)
    if char_ord < 32 or char_ord > 126:
        print(f'位置 {i}: 字符 {repr(char)}, ASCII值 {char_ord} (非打印字符)')
    else:
        print(f'位置 {i}: 字符 {repr(char)}, ASCII值 {char_ord}')