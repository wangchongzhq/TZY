#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查直播源URL数量的简单脚本
"""

import re

# 读取get_cgq_sources.py文件
with open('get_cgq_sources.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 使用正则表达式查找所有的URL
live_sources = re.findall(r'"(https://[^"]+)"', content)

# 打印结果
print(f'找到的直播源URL数量: {len(live_sources)}')
print(f'是否满足最小50个的要求: {len(live_sources) >= 50}')

# 打印前10个URL作为示例
print('\n前10个URL示例:')
for i, url in enumerate(live_sources[:10], 1):
    print(f'{i}. {url}')
