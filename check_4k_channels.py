#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查CGQ.TXT文件中的4K频道规范化结果
"""

import re

def check_4k_channels():
    try:
        with open('CGQ.TXT', 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.strip().split('\n')
        print("文件总行数:", len(lines))
        print("\n前20行内容:")
        for i, line in enumerate(lines[:20], 1):
            print(f"{i:3d}: {line}")
        
        print("\n包含4K的频道（前30个）:")
        k4_channels = []
        for line in lines:
            if '4K' in line or '4k' in line:
                k4_channels.append(line)
        
        print(f"找到 {len(k4_channels)} 个4K频道")
        for i, channel in enumerate(k4_channels[:30], 1):
            print(f"{i:3d}: {channel}")
        
    except Exception as e:
        print(f"读取文件时出错: {e}")
        # 尝试其他编码
        try:
            with open('CGQ.TXT', 'r', encoding='gbk') as f:
                content = f.read()
            print("\n使用GBK编码读取:")
            lines = content.strip().split('\n')
            print("前10行内容:")
            for i, line in enumerate(lines[:10], 1):
                print(f"{i:3d}: {line}")
        except Exception as e2:
            print(f"使用GBK编码读取也失败: {e2}")

if __name__ == "__main__":
    check_4k_channels()
