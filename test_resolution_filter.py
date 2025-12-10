import sys
import os
import re

# 确保使用UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 动态导入IP-TV.py
import importlib.util
spec = importlib.util.spec_from_file_location("ip_tv", "IP-TV.py")
ip_tv = importlib.util.module_from_spec(spec)
sys.modules["ip_tv"] = ip_tv
spec.loader.exec_module(ip_tv)

print("IP-TV模块导入成功")

# 查看质量配置
quality_config = ip_tv.get_config('quality', {})
print(f"\n质量配置: {quality_config}")

# 测试should_exclude_url函数
print("\n测试should_exclude_url函数:")

# 测试不同分辨率标识的频道
channels_to_test = [
    ("CCTV1 (1080p)", "http://streaming.tv/cctv1.m3u8"),
    ("CCTV1 (720p)", "http://streaming.tv/cctv1.m3u8"),
    ("CCTV1 (576p)", "http://streaming.tv/cctv1.m3u8"),
    ("CCTV1", "http://streaming.tv/cctv1.m3u8"),  # 没有分辨率标识
    ("CCTV1 HD", "http://streaming.tv/cctv1.m3u8"),  # 只有HD标识
    ("CCTV1 SD", "http://streaming.tv/cctv1.m3u8"),  # 只有SD标识
    ("CCTV4K", "http://streaming.tv/cctv4k.m3u8"),  # 4K频道
    ("CCTV8K", "http://streaming.tv/cctv8k.m3u8")   # 8K频道
]

for channel_name, url in channels_to_test:
    excluded = ip_tv.should_exclude_url(url, channel_name)
    print(f"  '{channel_name}' -> {'排除' if excluded else '保留'}")

# 检查should_exclude_resolution函数（如果存在）
print("\n检查should_exclude_resolution函数:")
try:
    from core.channel_utils import should_exclude_resolution
    print("  函数存在")
    
    # 测试不同分辨率
    test_cases = [
        ("CCTV1 (1080p)", "http://example.com/cctv1.m3u8", "1920x1080"),
        ("CCTV1 (720p)", "http://example.com/cctv1.m3u8", "1920x1080"),
        ("CCTV1 (576p)", "http://example.com/cctv1.m3u8", "1920x1080"),
        ("CCTV1", "http://example.com/cctv1.m3u8", "1920x1080"),
        ("CCTV1 (1080p)", "http://example.com/cctv1.m3u8", "1280x720"),
    ]
    
    for channel_name, url, min_resolution in test_cases:
        excluded = should_exclude_resolution(url, channel_name, min_resolution)
        print(f"  '{channel_name}' (最小分辨率: {min_resolution}) -> {'排除' if excluded else '保留'}")
        
except ImportError:
    print("  函数不存在或无法导入")
except Exception as e:
    print(f"  测试出错: {e}")

print("\n测试完成")