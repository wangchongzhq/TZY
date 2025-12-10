#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试4K频道处理修复
"""
import requests
from core.parser import parse_m3u_content

def test_4k_channels_from_source():
    """测试从用户提供的源文件中获取4K频道"""
    url = "https://ghproxy.it/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt"
    
    print(f"正在获取源文件: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        content = response.text
        
        print(f"获取到源文件，长度: {len(content)} 字符")
        
        # 使用core/parser.py中的解析函数来获取完整的频道信息
        channel_infos = parse_m3u_content(content)
        
        print(f"解析到 {len(channel_infos)} 个频道")
        
        # 查找4K相关频道
        print("\n=== 4K相关频道 ===")
        fourk_channels = []
        for channel_info in channel_infos:
            name = channel_info.name
            group = channel_info.group
            url = channel_info.url
            
            # 检查是否为4K频道
            is_4k = ('4K' in name or '4k' in name or '8K' in name or '8k' in name or 
                    '4K' in group or '4k' in group or '8K' in group or '8k' in group)
            
            if is_4k:
                fourk_channels.append((name, group, url))
                print(f"频道: {name}, 分组: {group}, URL: {url}")
        
        print(f"\n共找到 {len(fourk_channels)} 个4K相关频道")
        
        # 检查用户提到的特定4K频道是否存在
        target_channels = ['北京卫视4K', '东方卫视4K', '湖南卫视4K', '广东卫视4K']
        print("\n=== 检查特定4K频道 ===")
        for target in target_channels:
            found = any(target in name for name, _, _ in fourk_channels)
            print(f"{target}: {'找到' if found else '未找到'}")
            
    except Exception as e:
        print(f"出错了: {e}")

if __name__ == "__main__":
    test_4k_channels_from_source()
