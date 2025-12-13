#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# 测试IPTV.py中的正则表达式
print("=== 测试IPTV.py中的正则表达式 ===")
test_cases = ["CCTV4K", "CCTV 4K", "CCTV-4K", "CCTV4", "CCTV16"]

# 测试CCTV-数字格式的正则表达式
print("\n1. 测试CCTV-数字格式的正则表达式：")
cctv_pattern = re.compile(r'^[Cc][Cc][Tt][Vv][\s\-]?(\d+|4K|8K)', re.IGNORECASE)
for test_case in test_cases:
    match = cctv_pattern.match(test_case)
    if match:
        print(f"  '{test_case}' 匹配成功，分组1: '{match.group(1)}'")
    else:
        print(f"  '{test_case}' 匹配失败")

# 测试带中文的CCTV频道正则表达式
print("\n2. 测试带中文的CCTV频道正则表达式：")
chinese_cctv_pattern = re.compile(r'^(?:CCTV|cctv)[\-_]?(\d+|4K|8K)(?:综合|财经|综艺|中文国际|体育|电影|国防军事|电视剧|纪录|科教|戏曲|社会与法|新闻|少儿|音乐|农业农村|奥林匹克)?', re.IGNORECASE)
for test_case in test_cases:
    match = chinese_cctv_pattern.search(test_case)
    if match:
        print(f"  '{test_case}' 匹配成功，分组1: '{match.group(1)}'")
    else:
        print(f"  '{test_case}' 匹配失败")

# 直接测试core/channel_utils.py中的正则表达式
print("\n=== 测试core/channel_utils.py中的正则表达式 ===")
cctv_pattern_core = re.compile(r'cctv\s*(\d+|4k|8k)\s*([+]?)', re.IGNORECASE)
for test_case in test_cases:
    test_case_lower = test_case.lower()
    match = cctv_pattern_core.search(test_case_lower)
    if match:
        print(f"  '{test_case}' -> 匹配成功，分组1: '{match.group(1)}'，分组2: '{match.group(2)}'")
    else:
        print(f"  '{test_case}' -> 匹配失败")

# 测试实际函数调用
print("\n=== 测试实际函数调用 ===")
print("\n3. 测试IPTV.py中的normalize_channel_name函数：")
from IPTV import normalize_channel_name
for test_case in test_cases:
    result = normalize_channel_name(test_case)
    print(f"  '{test_case}' -> '{result}'")

print("\n4. 测试core/channel_utils.py中的normalize_channel_name函数：")
from core.channel_utils import normalize_channel_name as normalize_channel_name_core
for test_case in test_cases:
    result = normalize_channel_name_core(test_case)
    print(f"  '{test_case}' -> '{result}'")

# 测试正则表达式的调试
print("\n=== 调试正则表达式匹配过程 ===")
def debug_regex_matching():
    test_str = "CCTV4K"
    print(f"测试字符串: '{test_str}'")
    
    # 测试不同的正则表达式
    patterns = [
        ("r'cctv\\s*(\\d+|4k|8k)\\s*([+]?)'", re.compile(r'cctv\s*(\d+|4k|8k)\s*([+]?)', re.IGNORECASE)),
        ("r'cctv\\s*(\\d+(?:4k|8k)?)\\s*([+]?)'", re.compile(r'cctv\s*(\d+(?:4k|8k)?)\s*([+]?)', re.IGNORECASE)),
        ("r'cctv\\s*(\\d{1,3}|4k|8k)\\s*'", re.compile(r'cctv\s*(\d{1,3}|4k|8k)\s*', re.IGNORECASE)),
    ]
    
    for name, pattern in patterns:
        match = pattern.search(test_str.lower())
        if match:
            print(f"  模式 {name}: 匹配成功")
            for i in range(match.lastindex + 1):
                print(f"    分组 {i}: '{match.group(i)}'")
        else:
            print(f"  模式 {name}: 匹配失败")

debug_regex_matching()

# 测试extract_channels_from_m3u函数的CCTV4K/CCTV8K处理逻辑
print("\n=== 测试extract_channels_from_m3u函数的CCTV4K/CCTV8K处理逻辑 ===")
def test_extract_channels_from_m3u_logic():
    from collections import defaultdict
    import logging
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 测试数据：包含CCTV4K和CCTV8K的URL
    test_cases = [
        {
            'channel_name': 'CCTV4',
            'url': 'http://phb888.myds.me:35455/nptv/cctv4k.m3u8'
        },
        {
            'channel_name': 'CCTV8',
            'url': 'http://yemingjkl.x3322.net:35455/nptv/cctv8k.m3u8'
        },
        {
            'channel_name': 'CCTV4K测试',
            'url': 'http://example.com/cctv4k.m3u8'
        },
        {
            'channel_name': 'CCTV8K测试',
            'url': 'http://example.com/cctv8k.m3u8'
        },
        {
            'channel_name': '普通CCTV4',
            'url': 'http://example.com/cctv4.m3u8'
        }
    ]
    
    channels = defaultdict(list)
    
    for test_case in test_cases:
        channel_name = test_case['channel_name']
        url = test_case['url']
        
        logger.info(f"测试: 频道名称={channel_name}, URL={url}")
        
        # 首先检查URL中是否包含cctv4k或cctv8k，无论频道名称是什么
        if re.search(r'cctv4k', url.lower()):
            # 直接设置为CCTV4K，不再调用normalize_channel_name
            display_name = "CCTV4K"
            channels["4K频道"].append((display_name, url))
            logger.info(f"✓ 匹配CCTV4K: {display_name}, {url}")
        elif re.search(r'cctv8k', url.lower()):
            # 直接设置为CCTV8K，不再调用normalize_channel_name
            display_name = "CCTV8K"
            channels["4K频道"].append((display_name, url))
            logger.info(f"✓ 匹配CCTV8K: {display_name}, {url}")
        else:
            logger.info(f"✗ 未匹配4K: {channel_name}, {url}")
    
    logger.info("\n测试结果:")
    for group, channel_list in channels.items():
        logger.info(f"频道组: {group}")
        for name, url in channel_list:
            logger.info(f"  - {name}: {url}")

# 运行测试
test_extract_channels_from_m3u_logic()

# 测试实际的extract_channels_from_m3u函数
print("\n=== 测试实际的extract_channels_from_m3u函数 ===")
def test_actual_extract_function():
    from IPTV import extract_channels_from_m3u
    import logging
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 创建一个简单的M3U文件内容进行测试
    m3u_content = """#EXTM3U
#EXTINF:-1 tvg-id="CCTV4" tvg-name="CCTV4" tvg-logo="https://example.com/cctv4.png",CCTV4
http://phb888.myds.me:35455/nptv/cctv4k.m3u8
#EXTINF:-1 tvg-id="CCTV8" tvg-name="CCTV8" tvg-logo="https://example.com/cctv8.png",CCTV8
http://yemingjkl.x3322.net:35455/nptv/cctv8k.m3u8
#EXTINF:-1 tvg-id="CCTV4" tvg-name="CCTV4" tvg-logo="https://example.com/cctv4.png",CCTV4
http://example.com/cctv4.m3u8
"""
    
    logger.info("正在测试extract_channels_from_m3u函数...")
    channels = extract_channels_from_m3u(m3u_content)
    
    logger.info("\n函数返回结果:")
    for group, channel_list in channels.items():
        logger.info(f"频道组: {group}")
        for name, url in channel_list:
            logger.info(f"  - {name}: {url}")

# 运行实际函数测试
test_actual_extract_function()
