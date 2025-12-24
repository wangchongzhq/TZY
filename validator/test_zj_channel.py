#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证浙江卫视4K频道是否能被正确解析
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from iptv_validator import IPTVValidator

# 测试文件路径
test_file = r"C:\Users\Administrator\Documents\GitHub\TZY\109  live 1205 直播源 -减.txt"

def test_zj_channel():
    """测试浙江卫视4K频道解析"""
    print(f"测试文件：{test_file}")
    
    # 创建验证器实例
    validator = IPTVValidator(test_file, debug=True)
    
    # 解析文件
    channels, categories = validator.read_txt_file()
    
    print(f"\n解析到的频道总数：{len(channels)}")
    print(f"解析到的分类总数：{len(categories)}")
    
    # 查找浙江卫视4K频道
    zj_channels = [channel for channel in channels if "浙江卫视4K" in channel["name"]]
    
    if zj_channels:
        print(f"\n找到 {len(zj_channels)} 个浙江卫视4K频道：")
        for i, channel in enumerate(zj_channels):
            print(f"  {i+1}. 名称：{channel['name']}")
            print(f"     URL：{channel['url']}")
            print(f"     分类：{channel.get('category', '未分类')}")
    else:
        print("\n未找到浙江卫视4K频道！")
    
    # 打印前10个频道，看看是否包含浙江卫视4K
    print("\n前10个频道：")
    for i, channel in enumerate(channels[:10]):
        print(f"  {i+1}. {channel['name']} -> {channel['url']}")

if __name__ == "__main__":
    test_zj_channel()
