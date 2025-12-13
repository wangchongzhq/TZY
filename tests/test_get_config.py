#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import get_config

# 测试获取output配置
output_config = get_config('output', {})
print(f"Output配置: {output_config}")
print(f"m3u_file: {output_config.get('m3u_file', '未找到')}")
print(f"txt_file: {output_config.get('txt_file', '未找到')}")
print(f"m3u_filename: {output_config.get('m3u_filename', '未找到')}")
print(f"txt_filename: {output_config.get('txt_filename', '未找到')}")

# 测试获取所有配置
all_config = get_config('')
print(f"\n所有配置: {list(all_config.keys())}")
if 'output' in all_config:
    print(f"Output配置详情: {all_config['output']}")