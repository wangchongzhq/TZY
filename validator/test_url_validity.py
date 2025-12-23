#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门测试URL验证逻辑的简单脚本
"""

import os
import re

def check_url_validity(url):
    """检查URL的有效性，实现非空即有效的逻辑"""
    try:
        # 处理包含特殊字符的URL，如$符号（通常是电视端的标识）
        if '$' in url:
            # 移除$符号及其后面的内容，只保留前面的URL部分
            url = url.split('$')[0]
            print(f"[调试] 处理包含$符号的URL: {url}")

        # 检测是否包含动态参数（如{PSID}、{TARGETOPT}等，包括URL编码形式%7BPSID%7D）
        has_dynamic_params = re.search(r'(\{[A-Z_]+\}|%7B[A-Z_]+%7D)', url)
        if has_dynamic_params:
            print(f"[调试] 检测到包含动态参数的URL: {url}")

        # 根据用户要求，文件中的线路都是电视上能打开播放的频道线路
        # 所以我们对URL验证更加宽松，只要URL不为空就视为有效
        if url.strip():
            print(f"[调试] URL不为空，视为有效: {url}")
            return True
        
        # 只有空URL才视为无效
        print(f"[调试] URL为空，视为无效: {url}")
        return False
    except Exception as e:
        print(f"[调试] 检查URL有效性时出错: {type(e).__name__}: {e}")
        # 如果发生任何异常，只要URL不为空就视为有效
        if url.strip():
            print(f"[调试] 异常处理中URL不为空，视为有效: {url}")
            return True
        return False

# 测试用的URL列表
test_urls = [
    "http://example.com/stream.m3u8",
    "https://live.example.com/channel1",
    "rtmp://server/live/stream",
    "http://example.com/stream.m3u8$param=value",  # 含$参数
    "http://example.com/stream?param={PSID}",  # 含动态参数
    "",  # 空URL
    "   ",  # 空白URL
    "rtsp://example.com/stream",  # RTSP协议
    "mms://example.com/stream",  # MMS协议
    "udp://@239.255.1.1:1234",  # UDP协议
]

print("=== 测试URL验证逻辑 ===")
for url in test_urls:
    result = check_url_validity(url)
    print(f"URL: {repr(url)}")
    print(f"验证结果: {'有效' if result else '无效'}")
    print("-" * 50)