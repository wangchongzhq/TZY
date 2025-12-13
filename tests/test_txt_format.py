#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试生成TXT文件的分类标题格式
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from IP-TV import generate_txt_file
from collections import defaultdict

# 创建一个简单的测试数据
test_channels = defaultdict(list)
test_channels["央视频道"].append(("CCTV1", "http://example.com/cctv1"))
test_channels["卫视频道"].append(("湖南卫视", "http://example.com/hunan"))
test_channels["其他"].append(("未知频道", "http://example.com/unknown"))

# 生成测试文件
test_file_path = "test_output.txt"
if generate_txt_file(test_channels, test_file_path):
    print(f"✅ 测试文件生成成功：{test_file_path}")
    # 查看文件内容
    print("\n文件内容：")
    with open(test_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
    # 检查分类标题格式
    print("\n检查分类标题格式：")
    lines = content.split('\n')
    for line in lines:
        if line.startswith('#') and '#,#genre#' in line:
            print(f"✅ 正确格式：{line}")
        elif line.startswith('#') and '#genre#' in line and '#,#genre#' not in line:
            print(f"❌ 错误格式：{line}")
    # 删除测试文件
    os.remove(test_file_path)
    print(f"\n✅ 测试文件已删除")
else:
    print(f"❌ 测试文件生成失败")
