# -*- coding: utf-8 -*-

# 读取文件内容
with open('collect_ipzy_clean.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找所有的三引号字符串
lines = content.split('\n')
triple_quote_stack = []  # 存储未关闭的三引号位置和类型

for line_num, line in enumerate(lines, 1):
    # 查找三引号
    quotes = []
    i = 0
    while i < len(line):
        if line[i:i+3] == '"""':
            quotes.append((i, '"""'))
            i += 3
        elif line[i:i+3] == "'''":
            quotes.append((i, "'''"))
            i += 3
        else:
            i += 1
    
    # 处理找到的三引号
    for pos, quote_type in quotes:
        if triple_quote_stack and triple_quote_stack[-1]['type'] == quote_type:
            # 关闭一个三引号
            open_line = triple_quote_stack.pop()
            print(f"找到匹配的三引号: 第{open_line['line']}行位置{open_line['pos']}到第{line_num}行位置{pos}")
        else:
            # 打开一个新的三引号
            triple_quote_stack.append({
                'line': line_num,
                'pos': pos,
                'type': quote_type
            })

# 检查是否有未关闭的三引号
if triple_quote_stack:
    print("\n发现未关闭的三引号字符串:")
    for open_quote in triple_quote_stack:
        print(f"  类型: {open_quote['type']}, 第{open_quote['line']}行位置{open_quote['pos']}")
        # 显示该位置的上下文
        if open_quote['line'] <= len(lines):
            print(f"    上下文: {lines[open_quote['line']-1]}")
else:
    print("\n所有三引号字符串都已正确关闭")
