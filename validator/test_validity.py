#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试URL验证逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from iptv_validator import IPTVValidator

# 测试URL验证逻辑
def test_url_validity():
    print("测试URL验证逻辑...")
    
    # 创建验证器实例
    validator = IPTVValidator("test.txt", debug=True)
    
    # 测试各种URL格式
    test_urls = [
        # 常见协议的URL
        "http://example.com/stream.m3u8",
        "https://example.com/stream.m3u8",
        "rtsp://example.com/stream",
        "rtmp://example.com/stream",
        "mms://example.com/stream",
        "udp://@239.255.1.1:5000",
        "rtp://example.com/stream",
        
        # IP地址+端口格式
        "192.168.1.1:8080",
        "239.255.1.1:5000",
        
        # 包含特殊字符的URL
        "http://example.com/stream.m3u8$tv",
        "http://example.com/stream.m3u8?id=123&token=abc",
        
        # 包含动态参数的URL
        "http://example.com/stream.m3u8?psid={PSID}",
        "http://example.com/stream.m3u8?targetopt={TARGETOPT}",
        "http://example.com/stream.m3u8?psid=%7BPSID%7D",
        
        # 边缘情况
        "example.com/stream.m3u8",
        "www.example.com/stream.m3u8",
        "http://",
        "",
        "invalid_url",
    ]
    
    for url in test_urls:
        valid = validator.check_url_validity(url)
        print(f"URL: {url}")
        print(f"有效: {valid}")
        print()

if __name__ == "__main__":
    test_url_validity()
