#!/usr/bin/env python3
"""
测试增强功能的简单脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from IPTV import TemplateDrivenProcessor, extract_channels_from_m3u
import config

def test_template_processor():
    """测试TemplateDrivenProcessor类"""
    print("🔧 测试TemplateDrivenProcessor增强功能...")
    
    # 初始化处理器
    processor = TemplateDrivenProcessor()
    
    # 测试URL黑名单检查
    print("\n1. 测试URL黑名单检查:")
    test_urls = [
        "http://epg.pw/stream/test.m3u8",
        "http://goodurl.com/test.m3u8",
        "http://103.40.13.71:12390/test.m3u8"
    ]
    
    for url in test_urls:
        is_blacklisted = processor.is_url_blacklisted(url)
        print(f"  URL: {url}")
        print(f"  在黑名单中: {'是' if is_blacklisted else '否'}")
    
    # 测试模糊匹配
    print("\n2. 测试模糊匹配:")
    test_pairs = [
        ("CCTV1", "CCTV-1"),
        ("CCTV5", "CCTV5体育"),
        ("湖南卫视", "湖南卫视HD"),
        ("江苏卫视", "江苏卫视高清")
    ]
    
    for name1, name2 in test_pairs:
        similarity = processor.fuzzy_match(name1, name2)
        print(f"  '{name1}' vs '{name2}': 相似度 {similarity:.2f} ({'匹配' if similarity >= processor.fuzzy_threshold else '不匹配'})")
    
    # 测试分辨率检查
    print("\n3. 测试分辨率检查:")
    test_resolution_urls = [
        "http://example.com/4k/test.m3u8",
        "http://example.com/1080p/test.m3u8", 
        "http://example.com/720p/test.m3u8",
        "http://cctv.com/live.m3u8"
    ]
    
    for url in test_resolution_urls:
        is_valid = processor.is_valid_resolution(url)
        print(f"  URL: {url}")
        print(f"  分辨率有效: {'是' if is_valid else '否'}")
    
    print("\n✅ TemplateDrivenProcessor测试完成")

def test_extract_channels():
    """测试频道提取功能"""
    print("\n🔍 测试频道提取功能...")
    
    # 模拟M3U内容
    test_m3u = """#EXTM3U
#EXTINF:-1 tvg-id="CCTV1" tvg-name="CCTV-1综合",CCTV1
http://example.com/cctv1.m3u8
#EXTINF:-1 tvg-id="HUNAN1" tvg-name="湖南卫视HD",湖南卫视
http://example.com/hunan.m3u8
#EXTINF:-1 tvg-id="EPG_TEST" tvg-name="测试购物频道",购物频道
http://epg.pw/stream/test.m3u8
#EXTINF:-1 tvg-id="TEST4K" tvg-name="4K测试频道",CCTV4K
http://example.com/4k/test.m3u8
"""
    
    try:
        channels = extract_channels_from_m3u(test_m3u)
        print(f"  提取到 {len(channels)} 个分类的频道")
        
        for category, channel_list in channels.items():
            print(f"  📺 {category}: {len(channel_list)} 个频道")
            for channel_name, url in channel_list[:3]:  # 只显示前3个
                print(f"    - {channel_name}: {url[:50]}...")
        
        print("\n✅ 频道提取测试完成")
        
    except Exception as e:
        print(f"❌ 频道提取测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_ipv6_support():
    """测试IPv6支持"""
    print("\n🌐 测试IPv6支持...")
    
    # 检查IPv6支持
    try:
        import socket
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('google.com', 80, 0, 0))
        ipv6_supported = (result == 0)
        sock.close()
        
        print(f"  系统IPv6支持: {'是' if ipv6_supported else '否'}")
        print(f"  IPv6优先级设置: {getattr(config, 'ip_version_priority', '未设置')}")
        
    except Exception as e:
        print(f"  IPv6支持检查失败: {e}")
    
    print("\n✅ IPv6支持测试完成")

if __name__ == "__main__":
    print("🚀 开始测试恢复后的复杂功能")
    print("=" * 50)
    
    test_template_processor()
    test_extract_channels()
    test_ipv6_support()
    
    print("\n" + "=" * 50)
    print("🎉 所有测试完成！")