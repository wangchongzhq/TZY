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

# 输出URL数量
print(len(live_sources))
print(len(live_sources) >= 50)
