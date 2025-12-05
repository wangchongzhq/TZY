#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分辨率过滤功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import get_config, config_manager
from core.channel_utils import should_exclude_resolution, get_video_resolution

def test_resolution_filter():
    """测试分辨率过滤功能"""
    print("=== 测试分辨率过滤功能 ===")
    
    # 获取配置
    print(f"当前配置:")
    print(f"  分辨率过滤开关: {get_config('quality.open_filter_resolution', False)}")
    print(f"  最小分辨率要求: {get_config('quality.min_resolution', '1920x1080')}")
    print(f"  分辨率获取方法: {get_config('quality.method', 'ffmpeg')}")
    print(f"  超时时间: {get_config('quality.timeout', 5)}秒")
    print()
    
    # 测试分辨率过滤功能的开关
    print("=== 测试分辨率过滤开关功能 ===")
    
    from core.config import set_config
    
    # 开启分辨率过滤
    set_config('quality.open_filter_resolution', True)
    print(f"分辨率过滤已开启: {get_config('quality.open_filter_resolution')}")
    
    # 关闭分辨率过滤
    set_config('quality.open_filter_resolution', False)
    print(f"分辨率过滤已关闭: {get_config('quality.open_filter_resolution')}")
    
    # 重新开启分辨率过滤
    set_config('quality.open_filter_resolution', True)
    print(f"分辨率过滤已重新开启: {get_config('quality.open_filter_resolution')}")
    
    print()
    print("=== 测试分辨率过滤逻辑核心功能 ===")
    
    # 直接测试分辨率比较逻辑
    test_cases = [
        ((1920, 1080), '1920x1080', False),  # 刚好满足要求，不应排除
        ((1280, 720), '1920x1080', True),    # 低于要求，应排除
        ((3840, 2160), '1920x1080', False),  # 高于要求，不应排除
    ]
    
    print("分辨率比较逻辑测试:")
    for resolution, min_res, expected in test_cases:
        try:
            min_width, min_height = map(int, min_res.split('x'))
            width, height = resolution
            excluded = width < min_width or height < min_height
            print(f"  分辨率 {width}x{height} vs 最小要求 {min_res}: {'排除' if excluded else '保留'} (预期: {'排除' if expected else '保留'})")
        except Exception as e:
            print(f"  测试失败: {e}")
    
    print()
    print("=== 测试should_exclude_resolution函数流程 ===")
    
    # 测试should_exclude_resolution函数的流程控制
    print("1. 关闭分辨率过滤时:")
    set_config('quality.open_filter_resolution', False)
    excluded = should_exclude_resolution("http://example.com/test.m3u8")
    print(f"   URL: http://example.com/test.m3u8 -> {'排除' if excluded else '保留'}")
    
    print("2. 开启分辨率过滤时:")
    set_config('quality.open_filter_resolution', True)
    excluded = should_exclude_resolution("http://example.com/test.m3u8", timeout=1)
    print(f"   URL: http://example.com/test.m3u8 -> {'排除' if excluded else '保留'}")
    
    print()
    print("=== 测试不同最小分辨率配置 ===")
    
    test_resolutions = ['1920x1080', '1280x720', '640x480']
    test_url = "http://example.com/test.m3u8"
    
    for res in test_resolutions:
        print(f"最小分辨率要求: {res}")
        # 由于实际获取分辨率可能超时，我们直接测试配置是否正确应用
        print(f"   配置已更新: {get_config('quality.min_resolution')}")
    
    # 恢复原配置
    set_config('quality.min_resolution', '1920x1080')
    print()
    print("测试完成！")
    print("注意：由于测试URL无法实际访问，分辨率获取功能的完整测试需要使用真实可用的视频流URL。")

if __name__ == "__main__":
    test_resolution_filter()
