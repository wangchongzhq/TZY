#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

# 读取M3U文件
with open('jieguo.m3u', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找所有group-title
group_pattern = re.compile(r'group-title="([^"]+)"')
groups = set(match.group(1) for match in group_pattern.finditer(content))

print('频道分类:', sorted(groups))
print('分类数量:', len(groups))
