# -*- coding: utf-8 -*-

import re

# 读取文件内容
with open('collect_ipzy.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找所有非ASCII字符和非打印字符
print("查找非打印字符和无效字符:")
for i, char in enumerate(content):
    char_ord = ord(char)
    # 检查非ASCII字符和特定的无效字符
    if (char_ord < 32 and char_ord != 10 and char_ord != 13 and char_ord != 9) or char_ord > 126:
        print(f"位置 {i}: 字符 {repr(char)}, ASCII值 {char_ord}")

# 特别检查U+E576字符
ue576_count = content.count('\uE576')
print(f"\nU+E576字符的数量: {ue576_count}")

# 创建一个没有无效字符的新版本
clean_content = re.sub(r'[\uE000-\uF8FF]', '', content)  # 删除所有私有使用区字符

# 保存清理后的文件
with open('collect_ipzy_clean.py', 'w', encoding='utf-8') as f:
    f.write(clean_content)

print("\n清理后的文件已保存为 collect_ipzy_clean.py")
