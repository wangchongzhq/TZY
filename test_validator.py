#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试直播源验证工具
"""

import os
import sys
import time

# 添加validator目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'validator'))

from iptv_validator import IPTVValidator


def test_file_validation():
    """测试文件验证功能"""
    # 测试文件路径
    test_file = r"C:\Users\Administrator\Documents\GitHub\TZY\109  live 1205 直播源 -减.txt"
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return False
    
    print(f"开始测试文件验证: {test_file}")
    
    # 创建验证器实例
    validator = IPTVValidator(test_file, max_workers=10, timeout=3, debug=True)
    
    # 定义进度回调函数
    def progress_callback(data):
        print(f"进度更新: {data['progress']}% - {data.get('message', '')}")
        if data.get('channel'):
            channel = data['channel']
            if 'url' in channel:
                print(f"  频道: {channel['name']} - {channel['url']}")
            else:
                print(f"  频道: {channel['name']}")
    
    try:
        # 解析文件
        start_time = time.time()
        if validator.file_type == 'm3u':
            channels, categories = validator.read_m3u_file(progress_callback)
        elif validator.file_type == 'json':
            channels, categories = validator.read_json_file(progress_callback)
        else:
            channels, categories = validator.read_txt_file(progress_callback)
        
        parse_time = time.time() - start_time
        print(f"文件解析完成，耗时: {parse_time:.2f}秒")
        print(f"解析到 {len(channels)} 个频道，{len(categories)} 个分类")
        
        # 验证频道
        start_time = time.time()
        valid_channels = validator.validate_channels(progress_callback)
        
        validation_time = time.time() - start_time
        print(f"频道验证完成，耗时: {validation_time:.2f}秒")
        print(f"有效频道: {len(valid_channels)}/{len(channels)}")
        
        # 生成输出文件
        output_file = validator.generate_output_files()
        print(f"输出文件已生成: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"验证过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=== 直播源验证工具测试 ===")
    success = test_file_validation()
    if success:
        print("\n测试成功!")
    else:
        print("\n测试失败!")
    sys.exit(0 if success else 1)
