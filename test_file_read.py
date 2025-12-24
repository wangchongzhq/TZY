#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试读取直播源文件的脚本
"""

import os
import sys
import logging

# 添加validator目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'validator'))

from iptv_validator import IPTVValidator

def test_read_file(file_path):
    """测试读取指定的直播源文件"""
    print(f"开始测试读取文件: {file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        return False
    
    try:
        # 创建验证器实例
        validator = IPTVValidator(file_path)
        
        # 读取文件
        validator.read_file()
        
        print(f"成功读取文件，共找到 {len(validator.channels)} 个频道")
        
        # 输出前5个频道作为示例
        if validator.channels:
            print("\n前5个频道示例:")
            for i, channel in enumerate(validator.channels[:5]):
                print(f"[{i+1}] {channel['name']} - {channel['url']}")
        
        return True
        
    except Exception as e:
        print(f"读取文件时发生错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.DEBUG)
    
    # 使用用户指定的测试文件路径
    test_file = r"C:\Users\Administrator\Documents\GitHub\TZY\109  live 1205 直播源 -减.txt"
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    
    test_read_file(test_file)