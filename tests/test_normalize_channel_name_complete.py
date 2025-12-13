#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试频道名称标准化功能
直接使用core.channel_utils中的normalize_channel_name函数
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.channel_utils import normalize_channel_name

# 测试用例：涵盖各种常见情况和边缘情况
test_cases = [
    # 基本测试
    ("北京卫视", "北京卫视"),
    ("湖南卫视", "湖南卫视"),
    ("CCTV4", "CCTV4"),
    ("东方卫视", "东方卫视"),
    ("江苏卫视", "江苏卫视"),
    ("浙江卫视", "浙江卫视"),
    
    # 带HD/高清的测试
    ("北京卫视 HD", "北京卫视"),
    ("北京卫视高清", "北京卫视"),
    ("北京卫视高清频道", "北京卫视"),
    ("湖南卫视HD", "湖南卫视"),
    ("湖南卫视高清", "湖南卫视"),
    ("CCTV4 HD", "CCTV4"),
    ("CCTV4高清", "CCTV4"),
    
    # 带特殊字符的测试
    ("北京卫视-HD", "北京卫视"),
    ("北京卫视_HD", "北京卫视"),
    ("北京卫视.HD", "北京卫视"),
    ("北京卫视 (HD)", "北京卫视"),
    ("北京卫视 [HD]", "北京卫视"),
    ("北京卫视【HD】", "北京卫视"),
    
    # 带前后空格的测试
    (" 北京卫视 HD  ", "北京卫视"),
    (" 湖南卫视高清  ", "湖南卫视"),
    ("  CCTV4  ", "CCTV4"),
    
    # 带其他前缀后缀的测试
    ("直播北京卫视", "北京卫视"),
    ("北京卫视直播", "北京卫视"),
    ("正在直播北京卫视", "北京卫视"),
    ("北京卫视正在直播", "北京卫视"),
    
    # 凤凰相关频道的测试（重点测试）
    ("凤凰卫视", "凤凰卫视"),
    ("凤凰卫视中文台", "凤凰卫视中文台"),
    ("凤凰卫视资讯台", "凤凰卫视资讯台"),
    ("凤凰卫视电影台", "凤凰卫视电影台"),
    ("凤凰卫视香港台", "凤凰卫视香港台"),
    ("凤凰卫视美洲台", "凤凰卫视美洲台"),
    ("凤凰卫视欧洲台", "凤凰卫视欧洲台"),
    ("凤凰卫视HD", "凤凰卫视"),
    ("凤凰卫视高清", "凤凰卫视"),
    ("凤凰卫视中文台HD", "凤凰卫视中文台"),
    ("凤凰卫视资讯台高清", "凤凰卫视资讯台"),
    
    # 央视频道测试
    ("CCTV-1", "CCTV1"),
    ("CCTV-1 HD", "CCTV1"),
    ("CCTV-2", "CCTV2"),
    ("CCTV-13新闻", "CCTV13"),
    ("CCTV13新闻", "CCTV13"),
    ("CCTV-5+体育赛事", "CCTV5+"),
    
    # 其他卫视测试
    ("广东卫视", "广东卫视"),
    ("深圳卫视", "深圳卫视"),
    ("安徽卫视", "安徽卫视"),
    ("山东卫视", "山东卫视"),
    ("辽宁卫视", "辽宁卫视"),
    ("湖北卫视", "湖北卫视"),
    ("四川卫视", "四川卫视"),
    ("重庆卫视", "重庆卫视"),
    
    # 特殊情况测试
    ("", None),  # 空字符串
    (None, None),  # None值
    ("    ", None),  # 仅空格
    ("测试频道", "测试频道"),  # 未映射的频道
    ("测试频道 HD", "测试频道"),  # 未映射的带HD频道
    
    # 复杂组合测试
    ("  凤凰卫视中文台_HD  ", "凤凰卫视中文台"),
    ("CCTV-13-新闻 HD", "CCTV13"),
    ("广东卫视(高清)", "广东卫视"),
    ("深圳卫视【高清】", "深圳卫视"),
    ("正在直播-湖南卫视_HD", "湖南卫视"),
]

def run_tests():
    """运行所有测试用例"""
    print("=" * 60)
    print("完整测试频道名称标准化功能")
    print("=" * 60)
    
    passed = 0
    failed = 0
    total = len(test_cases)
    
    for i, (input_name, expected) in enumerate(test_cases, 1):
        try:
            result = normalize_channel_name(input_name)
            if result == expected:
                status = "✓ PASS"
                passed += 1
            else:
                status = "✗ FAIL"
                failed += 1
                
            # 格式化输出
            input_str = repr(input_name).ljust(25)
            expected_str = repr(expected).ljust(20)
            result_str = repr(result).ljust(20)
            
            print(f"{i:2d}. {status} | 输入: {input_str} | 期望: {expected_str} | 实际: {result_str}")
            
        except Exception as e:
            status = "✗ ERROR"
            failed += 1
            print(f"{i:2d}. {status} | 输入: {repr(input_name)} | 错误: {str(e)}")
    
    print("=" * 60)
    print(f"测试完成: 共 {total} 个测试用例, 通过 {passed} 个, 失败 {failed} 个")
    print("=" * 60)
    
    if failed > 0:
        return False
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
