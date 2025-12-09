#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试4K频道分类问题
"""

import re
import json
from collections import defaultdict

# 读取配置文件中的4K频道映射
def read_channel_mapping():
    with open('IP-TV.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找CHANNEL_MAPPING的定义
    mapping_match = re.search(r'CHANNEL_MAPPING = \{([^}]+)\}', content, re.DOTALL)
    if not mapping_match:
        print("未找到CHANNEL_MAPPING定义")
        return {}
    
    mapping_content = mapping_match.group(1)
    print("=== CHANNEL_MAPPING中的4K频道映射 ===")
    
    # 查找4K/8K相关的映射
    for line in mapping_content.split('\n'):
        line = line.strip()
        if '4K' in line or '8K' in line:
            print(line)

# 检查jieguo.m3u中的频道

def check_jieguo_m3u():
    print("\n=== 检查jieguo.m3u中的频道 ===")
    
    # 读取jieguo.m3u文件
    try:
        with open('jieguo.m3u', 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取jieguo.m3u失败: {e}")
        return
    
    # 查找所有频道条目
    channel_entries = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*?)\n', content, re.DOTALL)
    print(f"共找到 {len(channel_entries)} 个频道")
    
    # 统计4K频道数量
    k4_channels = []
    for name, url in channel_entries:
        if '4K' in name or '4k' in name or '8K' in name or '8k' in name:
            k4_channels.append(name)
    
    print(f"\n共找到 {len(k4_channels)} 个4K/8K频道")
    
    # 显示所有4K频道
    print("\n所有4K/8K频道名称:")
    for i, name in enumerate(k4_channels[:20], 1):  # 只显示前20个
        print(f"  {i}. {name}")
    
    if len(k4_channels) > 20:
        print(f"  ... 还有 {len(k4_channels) - 20} 个频道")
    
    # 检查用户提到的特定频道
    user_channels = ['北京卫视4K', '浙江卫视4K', '湖南卫视4K', '山东卫视4K', '南国都市4K']
    print("\n=== 检查用户提到的特定频道 ===")
    
    for user_channel in user_channels:
        found = False
        for name, url in channel_entries:
            # 检查频道名称是否包含用户提到的频道名称
            if user_channel in name:
                found = True
                print(f"✅ 找到频道: {name}")
                break
        
        if not found:
            # 尝试模糊匹配
            for name, url in channel_entries:
                channel_name = name.split(',')[-1].strip()
                if any(keyword in channel_name for keyword in [user_channel.split('4K')[0], '4K', '超高清']):
                    print(f"⚠️  可能匹配到: {channel_name}")
                    break
            else:
                print(f"❌ 未找到频道: {user_channel}")

if __name__ == "__main__":
    read_channel_mapping()
    check_jieguo_m3u()