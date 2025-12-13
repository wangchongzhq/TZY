#!/usr/bin/env python3

import sys
import os
import re
import requests

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入IPTV模块
import IPTV

# 测试URL - 这个URL看起来是错误分类频道的来源
url = "https://cdn.iptv8k.top/dl/jrys.php?id=320&time=20240926215313&ip=111.229.253.40"

print("测试URL的内容：")
print("=" * 50)

try:
    # 获取URL内容
    response = requests.get(url, timeout=10)
    response.encoding = response.apparent_encoding
    content = response.text
    
    print(f"URL: {url}")
    print(f"状态码: {response.status_code}")
    print(f"内容类型: {response.headers.get('Content-Type')}")
    print(f"内容长度: {len(content)} 字符")
    print(f"内容前500字符: {content[:500]}...")
    
    # 尝试解析为M3U
    if '#EXTINF:' in content:
        print("\n检测到M3U格式内容，尝试解析：")
        channels = IPTV.extract_channels_from_m3u(content)
        for group_title, channel_list in channels.items():
            print(f"\n分组: {group_title}")
            for name, u in channel_list[:10]:  # 只显示前10个
                print(f"  频道: {name}, URL: {u}")
                # 测试4K检测
                has_4k = ("4K" in name or "4k" in name or "8K" in name or "8k" in name or "超高清" in name or "2160" in name)
                print(f"  名称包含4K: {has_4k}")
            if len(channel_list) > 10:
                print(f"  ... 还有 {len(channel_list) - 10} 个频道")
    else:
        print("\n未检测到M3U格式内容")
        print(f"完整内容: {content}")
        
except Exception as e:
    print(f"获取URL内容时出错: {e}")

print("\n" + "=" * 50)
print("测试结束")
