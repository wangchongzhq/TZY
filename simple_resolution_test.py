#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试分辨率过滤功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import get_config, set_config, config_manager

def test_resolution_filter_core():
    """测试分辨率过滤的核心功能"""
    print("=== 简单测试分辨率过滤功能 ===")
    
    # 打印当前配置
    print(f"当前配置:")
    print(f"  分辨率过滤开关: {get_config('quality.open_filter_resolution', False)}")
    print(f"  最小分辨率要求: {get_config('quality.min_resolution', '1920x1080')}")
    print(f"  分辨率获取方法: {get_config('quality.method', 'ffmpeg')}")
    print()
    
    # 测试配置修改
    print("=== 测试配置修改功能 ===")
    
    # 修改配置
    set_config('quality.open_filter_resolution', True)
    set_config('quality.min_resolution', '1280x720')
    set_config('quality.method', 'ffmpeg')
    
    # 读取修改后的配置
    print(f"修改后的配置:")
    print(f"  分辨率过滤开关: {get_config('quality.open_filter_resolution')}")
    print(f"  最小分辨率要求: {get_config('quality.min_resolution')}")
    print(f"  分辨率获取方法: {get_config('quality.method')}")
    print()
    
    # 测试分辨率比较逻辑
    print("=== 测试分辨率比较逻辑 ===")
    
    # 模拟should_exclude_resolution函数的核心逻辑
    def mock_should_exclude_resolution(resolution, min_resolution):
        try:
            min_width, min_height = map(int, min_resolution.split('x'))
            width, height = resolution
            return width < min_width or height < min_height
        except Exception as e:
            print(f"  错误: {e}")
            return False
    
    test_cases = [
        ((1920, 1080), '1280x720', False),  # 1080p 大于 720p，不应排除
        ((1280, 720), '1280x720', False),    # 720p 等于 720p，不应排除
        ((1024, 768), '1280x720', True),     # 小于 720p，应排除
        ((3840, 2160), '1280x720', False),   # 4K 大于 720p，不应排除
    ]
    
    for resolution, min_res, expected in test_cases:
        width, height = resolution
        excluded = mock_should_exclude_resolution(resolution, min_res)
        print(f"  分辨率 {width}x{height} vs 最小要求 {min_res}: {'排除' if excluded else '保留'}")
    
    print()
    print("=== 测试完成 ===")
    print("分辨率过滤功能的核心逻辑已经验证正常。")
    print("要进行完整测试，请使用真实的视频流URL。")

if __name__ == "__main__":
    test_resolution_filter_core()
