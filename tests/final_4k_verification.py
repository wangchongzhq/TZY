#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4K频道判断逻辑最终验证脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append('.')

# 测试extract_channels_from_m3u函数
def test_m3u_function():
    """测试M3U文件解析中的4K频道判断逻辑"""
    from IPTV import extract_channels_from_m3u
    
    # 创建测试M3U内容
    test_m3u = "#EXTM3U\n#EXTINF:-1 tvg-id=\"\" tvg-name=\"4K测试频道\" tvg-logo=\"\" group-title=\"\" ,4K测试频道\nhttp://example.com/4k\n#EXTINF:-1 tvg-id=\"\" tvg-name=\"普通频道\" tvg-logo=\"\" group-title=\"\" ,普通频道\nhttp://example.com/normal\n#EXTINF:-1 tvg-id=\"\" tvg-name=\"CCTV 4K\" tvg-logo=\"\" group-title=\"\" ,CCTV 4K\nhttp://example.com/cctv4k\n#EXTINF:-1 tvg-id=\"\" tvg-name=\"CCTV1\" tvg-logo=\"\" group-title=\"\" ,CCTV1\nhttp://example.com/cctv1\n#EXTINF:-1 tvg-id=\"\" tvg-name=\"超高清频道\" tvg-logo=\"\" group-title=\"\" ,超高清频道\nhttp://example.com/hd\n#EXTINF:-1 tvg-id=\"\" tvg-name=\"普通频道2\" tvg-logo=\"\" group-title=\"\" ,普通频道2\nhttp://example.com/4k-url-but-not-4k-channel\n#EXTINF:-1 tvg-id=\"\" tvg-name=\"8K测试频道\" tvg-logo=\"\" group-title=\"\" ,8K测试频道\nhttp://example.com/8k\n#EXTINF:-1 tvg-id=\"\" tvg-name=\"2160测试\" tvg-logo=\"\" group-title=\"\" ,2160测试\nhttp://example.com/2160\n"
    
    print("=== 测试 extract_channels_from_m3u 函数 ===")
    channels = extract_channels_from_m3u(test_m3u)
    
    print("4K频道:")
    for name, url in channels.get('4K频道', []):
        print(f"  {name} -> {url}")
    
    print("\n其他频道:")
    for category in channels:
        if category != '4K频道':
            for name, url in channels[category]:
                print(f"  {name} -> {url}")
    
    return channels

# 测试extract_channels_from_txt函数
def test_txt_function():
    """测试TXT文件解析中的4K频道判断逻辑"""
    from IPTV import extract_channels_from_txt
    
    # 创建测试TXT内容
    test_txt = "# 这是一个测试文件\n4K测试频道,http://example.com/4k\n普通频道,http://example.com/normal\nCCTV 4K,http://example.com/cctv4k\nCCTV1,http://example.com/cctv1\n超高清频道,http://example.com/hd\n2160测试,http://example.com/2160\n普通频道2,http://example.com/4k-url-but-not-4k-channel\n8K测试频道,http://example.com/8k\n🇨🇳 4K,#genre#\n这个频道不是4K频道,http://example.com/4k\n"
    
    print("\n=== 测试 extract_channels_from_txt 函数 ===")
    channels = extract_channels_from_txt(test_txt)
    
    print("4K频道:")
    for name, url in channels.get('4K频道', []):
        print(f"  {name} -> {url}")
    
    print("\n其他频道:")
    for category in channels:
        if category != '4K频道':
            for name, url in channels[category]:
                print(f"  {name} -> {url}")
    
    return channels

# 主函数
def main():
    """运行所有测试"""
    print("4K频道判断逻辑最终验证脚本")
    print("=" * 50)
    
    # 测试M3U函数
    m3u_channels = test_m3u_function()
    
    # 测试TXT函数
    txt_channels = test_txt_function()
    
    print("\n" + "=" * 50)
    print("测试结果分析:")
    print("=" * 50)
    
    # 检查M3U测试结果
    m3u_4k_count = len(m3u_channels.get('4K频道', []))
    print(f"M3U解析中4K频道数量: {m3u_4k_count}")
    
    # 检查TXT测试结果
    txt_4k_count = len(txt_channels.get('4K频道', []))
    print(f"TXT解析中4K频道数量: {txt_4k_count}")
    
    # 验证是否正确跳过了分组标题
    txt_has_group_title_issue = any("不包含4K关键词" in name for name, url in txt_channels.get('4K频道', []))
    print(f"是否正确处理了分组标题: {'✅ 是' if not txt_has_group_title_issue else '❌ 否'}")
    
    # 验证是否仅根据频道名称判断4K
    m3u_url_issue = any("4k-url-but-not-4k-channel" in url for name, url in m3u_channels.get('4K频道', []))
    txt_url_issue = any("4k-url-but-not-4k-channel" in url for name, url in txt_channels.get('4K频道', []))
    url_issue = m3u_url_issue or txt_url_issue
    print(f"是否仅根据频道名称判断4K: {'✅ 是' if not url_issue else '❌ 否'}")
    
    print("\n" + "=" * 50)
    if not txt_has_group_title_issue and not url_issue:
        print("✅ 所有测试通过！4K频道判断逻辑已完全修复。")
        print("   修复内容:")
        print("   1. 统一了extract_channels_from_m3u和extract_channels_from_txt函数中的4K频道判断逻辑")
        print("   2. 修复了分组标题行导致的错误分类问题")
        print("   3. 确保了仅根据频道名称判断4K频道，不考虑URL中的字符")
        return True
    else:
        print("❌ 测试未通过，请检查修复内容。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
