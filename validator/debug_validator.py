#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：测试直播源验证逻辑
"""

import os
import sys
import re
from iptv_validator import IPTVValidator

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_check_url_validity():
    """测试URL有效性检查逻辑"""
    validator = IPTVValidator(None, debug=True)  # 使用None作为输入文件，仅测试URL验证功能
    
    print("=== 测试URL有效性检查 ===")
    
    # 测试用例
    test_urls = [
        "http://example.com/stream.m3u8",
        "https://live.example.com/channel1",
        "rtmp://server/live/stream",
        "http://example.com/stream.m3u8$param=value",
        "http://example.com/stream?param=value&other={PSID}",
        "",  # 空URL
        "   ",  # 空白URL
        "http://example.com/stream%20with%20spaces",
    ]
    
    for url in test_urls:
        print(f"\n测试URL: '{url}'")
        result = validator.check_url_validity(url)
        print(f"结果: {'有效' if result else '无效'}")

def test_process_channel():
    """测试单个频道处理逻辑"""
    # 创建一个临时测试文件
    with open("test_channels.txt", "w", encoding="utf-8") as f:
        f.write("频道1,http://example.com/stream1.m3u8\n")
        f.write("频道2,https://example.com/stream2.m3u8\n")
        f.write("频道3,rtmp://example.com/stream3\n")
        f.write("频道4,http://example.com/stream4.m3u8$token=abc123\n")
        f.write("频道5,http://example.com/stream5?param={PSID}\n")
    
    try:
        validator = IPTVValidator("test_channels.txt", debug=True)
        validator.read_txt_file()
        
        print(f"\n=== 测试频道处理逻辑 ===")
        print(f"共解析到 {len(validator.channels)} 个频道")
        
        for i, channel in enumerate(validator.channels):
            print(f"\n频道 {i+1}: {channel['name']}")
            print(f"URL: {channel['url']}")
            
            # 测试URL有效性检查
            valid = validator.check_url_validity(channel['url'])
            print(f"URL有效性检查结果: {'有效' if valid else '无效'}")
            
            # 测试完整频道处理
            result = validator.process_channel(channel, 1)
            print(f"频道处理结果: {'有效' if result['valid'] else '无效'}")
            print(f"状态: {result['status']}")
            print(f"分辨率: {result['resolution']}")
            
    finally:
        # 清理测试文件
        if os.path.exists("test_channels.txt"):
            os.remove("test_channels.txt")

def test_m3u_parsing():
    """测试M3U文件解析"""
    # 创建一个临时测试M3U文件
    with open("test_channels.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#EXTINF:-1 group-title=\"新闻\",央视新闻\n")
        f.write("http://example.com/cctv1.m3u8\n")
        f.write("#EXTINF:-1 group-title=\"体育\",CCTV5\n")
        f.write("https://example.com/cctv5.m3u8\n")
        f.write("#EXTINF:-1 group-title=\"电影\",电影频道\n")
        f.write("rtmp://example.com/movie\n")
    
    try:
        validator = IPTVValidator("test_channels.m3u", debug=True)
        channels, categories = validator.read_m3u_file()
        
        print(f"\n=== 测试M3U文件解析 ===")
        print(f"共解析到 {len(channels)} 个频道")
        print(f"分类: {categories}")
        
        for i, channel in enumerate(channels):
            print(f"\n频道 {i+1}:")
            print(f"  名称: {channel['name']}")
            print(f"  URL: {channel['url']}")
            print(f"  分类: {channel.get('category', '未分类')}")
            
            # 测试URL有效性检查
            valid = validator.check_url_validity(channel['url'])
            print(f"  URL有效性: {'有效' if valid else '无效'}")
            
            # 测试完整频道处理
            result = validator.process_channel(channel, 1)
            print(f"  处理结果: {'有效' if result['valid'] else '无效'}")
            
    finally:
        # 清理测试文件
        if os.path.exists("test_channels.m3u"):
            os.remove("test_channels.m3u")

def main():
    """主函数"""
    print("直播源验证调试脚本")
    print("=" * 50)
    
    # 测试URL有效性检查
    test_check_url_validity()
    
    # 测试TXT文件解析和频道处理
    test_process_channel()
    
    # 测试M3U文件解析
    test_m3u_parsing()
    
    print("\n" + "=" * 50)
    print("调试完成")

if __name__ == "__main__":
    main()
