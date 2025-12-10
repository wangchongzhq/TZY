import sys
import os
import importlib.util
import re

# 确保使用UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 测试1：直接测试should_exclude_resolution函数
print("测试1：直接测试should_exclude_resolution函数")
print("="*50)
try:
    from core.channel_utils import should_exclude_resolution
    
    # 测试不同的频道名称和分辨率
    test_cases = [
        ("CCTV1", "http://streaming.tv/cctv1.m3u8", "1920x1080", False),  # 没有分辨率标识
        ("CCTV1 (720p)", "http://streaming.tv/cctv1.m3u8", "1920x1080", True),  # 低于最小分辨率
        ("CCTV1 (1080p)", "http://streaming.tv/cctv1.m3u8", "1920x1080", False),  # 等于最小分辨率
        ("CCTV1 (2160p)", "http://streaming.tv/cctv1.m3u8", "1920x1080", False),  # 高于最小分辨率
    ]
    
    for channel_name, url, min_resolution, expected in test_cases:
        result = should_exclude_resolution(url, channel_name, min_resolution)
        status = "✅" if result == expected else "❌"
        print(f"{status} {channel_name} (min: {min_resolution}) -> {result}")
        
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试2：测试配置获取
print("\n测试2：测试配置获取")
print("="*50)
try:
    from core.config import config_manager
    
    config = config_manager.get_all()
    print(f"配置类型: {type(config)}")
    print(f"配置内容: {config}")
    
    # 测试获取质量配置
    quality_config = config.get('quality', {})
    print(f"\n质量配置: {quality_config}")
    
    # 测试获取最小分辨率和开启状态
    min_resolution = quality_config.get('min_resolution', '1920x1080')
    open_filter_resolution = quality_config.get('open_filter_resolution', True)
    print(f"最小分辨率: {min_resolution}")
    print(f"开启分辨率过滤: {open_filter_resolution}")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试3：直接测试should_exclude_url函数
print("\n测试3：直接测试should_exclude_url函数")
print("="*50)
try:
    # 动态导入IP-TV模块
    spec = importlib.util.spec_from_file_location("ip_tv", "IP-TV.py")
    ip_tv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ip_tv)
    
    # 测试不同的URL
    test_urls = [
        ("CCTV1", "http://streaming.tv/cctv1.m3u8"),
        ("CCTV2", "http://demo.streaming.tv/cctv2.m3u8"),  # 包含demo
        ("CCTV3", "http://sample.streaming.tv/cctv3.m3u8"),  # 包含sample
        ("CCTV4", "http://example.com/cctv4.m3u8"),  # 包含example.com
    ]
    
    for channel_name, url in test_urls:
        result = ip_tv.should_exclude_url(url, channel_name)
        print(f"{channel_name} ({url}) -> {result}")
        
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n所有测试完成")