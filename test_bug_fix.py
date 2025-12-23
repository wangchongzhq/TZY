#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目目录到系统路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'validator'))

from iptv_validator import IPTVValidator

def test_file_parsing():
    print("测试文件解析功能...")
    test_file = "test_bug_check.m3u"
    
    try:
        # 创建验证器实例
        validator = IPTVValidator(test_file, debug=True)
        
        # 解析文件
        if test_file.endswith('.m3u'):
            channels, categories = validator.read_m3u_file()
        else:
            channels, categories = validator.read_txt_file()
        
        print(f"解析到 {len(channels)} 个频道")
        for channel in channels:
            print(f"频道: {channel['name']}, URL: {channel['url']}, 分辨率(从名称): {channel.get('resolution_from_name')}")
            
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== 测试IPTV验证器功能 ===")
    test_file_parsing()
