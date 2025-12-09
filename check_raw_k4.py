#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查原始M3U文件中的4K频道
"""

import os
import re

def check_raw_k4_channels():
    print("=== 检查原始M3U文件中的4K频道 ===")
    
    # 获取所有临时M3U文件
    temp_files = [f for f in os.listdir('.') if f.endswith('.m3u') and f != 'jieguo.m3u' and f != 'IPTV.m3u']
    
    print(f"找到 {len(temp_files)} 个临时M3U文件")
    
    # 用户关心的频道关键词
    user_channels = ['北京卫视', '浙江卫视', '湖南卫视', '山东卫视', '南国都市']
    
    # 检查每个文件
    for file in temp_files[:5]:  # 只检查前5个文件
        print(f"\n=== 检查文件: {file} ===")
        
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找所有频道
            channels = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*?)\n', content, re.DOTALL)
            print(f"文件包含 {len(channels)} 个频道")
            
            # 检查4K频道
            k4_channels = []
            for name, url in channels:
                if '4K' in name or '4k' in name:
                    k4_channels.append((name, url))
            
            print(f"文件包含 {len(k4_channels)} 个4K频道")
            
            # 显示4K频道
            for i, (name, url) in enumerate(k4_channels[:10], 1):  # 只显示前10个
                print(f"  {i}. {name}")
            
            # 检查用户关心的频道
            print("\n=== 用户关心的频道 ===")
            found_user_channels = []
            for name, url in channels:
                if any(keyword in name for keyword in user_channels):
                    found_user_channels.append((name, url))
            
            print(f"找到 {len(found_user_channels)} 个用户关心的频道")
            for name, url in found_user_channels:
                print(f"  - {name}")
                
        except Exception as e:
            print(f"处理文件时出错: {e}")
            continue

if __name__ == "__main__":
    check_raw_k4_channels()