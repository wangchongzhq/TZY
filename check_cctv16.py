#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查CCTV16 4K频道的情况
"""

import re

# 读取jieguo.m3u文件
try:
    with open('jieguo.m3u', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=== 检查CCTV16相关频道 ===")
    
    # 搜索CCTV16相关频道
    cctv16_channels = re.findall(r'#EXTINF:.*?,(.*?CCTV16.*?)\n(http.*?)\n', content, re.DOTALL | re.IGNORECASE)
    
    if cctv16_channels:
        print(f'找到 {len(cctv16_channels)} 个CCTV16相关频道:')
        for name, url in cctv16_channels:
            print(f'  - {name}')
    else:
        print('未找到CCTV16相关频道')
        
        # 搜索所有CCTV频道
        print("\n=== 检查所有CCTV频道 ===")
        cctv_channels = re.findall(r'#EXTINF:.*?,(.*?CCTV.*?)\n(http.*?)\n', content, re.DOTALL | re.IGNORECASE)
        print(f'找到 {len(cctv_channels)} 个CCTV频道')
        
        # 按频道号排序
        cctv_channels.sort()
        
        # 显示前30个CCTV频道
        print("\n前30个CCTV频道:")
        for i, (name, url) in enumerate(cctv_channels[:30], 1):
            print(f'  {i}. {name}')
    
    # 检查4K频道
    print("\n=== 检查4K频道 ===")
    k4_channels = re.findall(r'#EXTINF:.*?,(.*?4K.*?)\n(http.*?)\n', content, re.DOTALL | re.IGNORECASE)
    print(f'找到 {len(k4_channels)} 个4K频道')
    
    # 显示包含CCTV的4K频道
    print("\n包含CCTV的4K频道:")
    for name, url in k4_channels:
        if 'CCTV' in name:
            print(f'  - {name}')
    
    # 搜索所有4K频道
    print("\n所有4K频道列表（前20个）:")
    for i, (name, url) in enumerate(k4_channels[:20], 1):
        print(f'  {i}. {name}')

except Exception as e:
    print(f'读取文件失败: {e}')
    import traceback
    traceback.print_exc()
