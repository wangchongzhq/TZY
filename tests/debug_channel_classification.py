#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本，用于跟踪特定频道的分类过程
"""

import sys
import os

# 将当前目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from IPTV import normalize_channel_name, get_channel_category

def debug_channel_classification(channel_name, channel_url):
    """调试单个频道的分类过程"""
    print(f"\n调试频道: {channel_name}")
    print(f"URL: {channel_url}")
    
    # 1. 测试原始频道名的4K判断
    has_4k_in_original = any(keyword in channel_name for keyword in ['4K', '4k', '8K', '8k', '超高清', '2160'])
    print(f"原始名称是否包含4K关键词: {has_4k_in_original}")
    
    # 2. 测试normalize_channel_name函数
    normalized = normalize_channel_name(channel_name)
    print(f"normalized_name: {normalized}")
    
    # 3. 测试规范化后名称的4K判断
    has_4k_in_normalized = any(keyword in normalized for keyword in ['4K', '4k', '8K', '8k', '超高清', '2160'])
    print(f"规范化后名称是否包含4K关键词: {has_4k_in_normalized}")
    
    # 4. 测试get_channel_category函数
    category = get_channel_category(normalized)
    print(f"分类结果: {category}")
    
    return category

# 测试用户提供的问题频道
problem_channels = [
    ("靖天映画", "https://cdn.iptv8k.top/dl/jrys.php?id=320&time=20240926215313&ip=111.229.253.40"),
    ("靖天戏剧", "https://cdn.iptv8k.top/dl/jrys.php?id=318&time=20240926215313&ip=111.229.253.40"),
    ("经典电影", "https://cdn.iptv8k.top/dl/jrys.php?id=396&time=20240926215313&ip=111.229.253.40"),
    ("天映经典", "https://cdn.iptv8k.top/dl/jrys.php?id=71&time=20240926215313&ip=111.229.253.40"),
    ("星空", "https://cdn.iptv8k.top/dl/jrys.php?id=21&time=20240926215313&ip=111.229.253.40"),
    ("东森电影", "https://cdn.iptv8k.top/dl/jrys.php?id=231&time=20240926215313&ip=111.229.253.40"),
    ("东森洋片", "https://cdn.iptv8k.top/dl/jrys.php?id=232&time=20240926215313&ip=111.229.253.40"),
    ("东森超视", "https://cdn.iptv8k.top/dl/jrys.php?id=216&time=20240926215313&ip=111.229.253.40#rtmp://f13h.mine.nu/sat/tv331#rtmp://f13h.mine.nu/sat/tv331"),
    ("CN卡通", "https://cdn.iptv8k.top/dl/jrys.php?id=364&time=20240926215313&ip=111.229.253.40"),
    ("北京新闻", "https://ls.qingting.fm/live/339/64k.m3u8"),
    ("睢宁综合", "https://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8"),
    ("辽宁都市", "https://ls.qingting.fm/live/1099/64k.m3u8"),
    ("武汉一台新闻综合", "https://ls.qingting.fm/live/20198/64k.m3u8"),
    ("灌阳新闻综合", "https://ls.qingting.fm/live/5043/64k.m3u8"),
    ("三明新闻综合", "https://ls.qingting.fm/live/5022100/64k.m3u8"),
    ("河北农民", "https://ls.qingting.fm/live/1650/64k.m3u8"),
    ("安顺新闻", "https://ls.qingting.fm/live/5022203/64k.m3u8"),
    ("铜陵新闻综合", "https://ls.qingting.fm/live/21303/64k.m3u8"),
    ("宁夏经济", "https://ls.qingting.fm/live/1841/64k.m3u8"),
    ("内蒙经济", "https://ls.qingting.fm/live/1885/64k.m3u8"),
    ("内蒙古经济生活", "https://ls.qingting.fm/live/1885/64k.m3u8"),
    ("黑龙江新闻法治", "https://ls.qingting.fm/live/4974/64k.m3u8"),
    ("黑龙江少儿", "https://ls.qingting.fm/live/4972/64k.m3u8"),
    ("黑龙江新闻", "https://ls.qingting.fm/live/4974/64k.m3u8"),
    ("翡翠", "https://cdn.iptv8k.top/dl/jrys.php?id=3&time=20240926215313&ip=111.229.253.40『线路08』"),
    ("翡翠", "https://cdn.iptv8k.top/dl/jrys.php?id=3&time=20240926215313&ip=111.229.253.40"),
    ("凤凰中文", "https://cdn.iptv8k.top/dl/jrys.php?id=19&time=20240926215313&ip=111.229.253.40"),
]

def main():
    print("开始调试频道分类过程...")
    print("=" * 60)
    
    # 测试各个频道的分类
    for channel_name, channel_url in problem_channels:
        debug_channel_classification(channel_name, channel_url)
    
    print("\n" + "=" * 60)
    print("调试完成！")

if __name__ == "__main__":
    main()
