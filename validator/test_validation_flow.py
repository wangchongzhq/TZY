#!/usr/bin/env python3
"""
测试验证流程的脚本，用于验证JSON文件的处理是否正常
"""

import sys
import os
import json

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from iptv_validator import IPTVValidator

def test_json_validation():
    """测试JSON文件验证流程"""
    print("=== 测试JSON验证流程 ===")
    
    # 创建一个简单的测试JSON文件
    test_data = {
        "channels": [
            {"name": "测试频道1", "url": "http://example.com/stream1", "category": "新闻"},
            {"name": "测试频道2", "url": "http://example.com/stream2", "category": "体育"},
            {"name": "测试频道3", "url": "http://example.com/stream3", "category": "电影"}
        ]
    }
    
    test_file_path = "test_flow_json.json"
    with open(test_file_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    try:
        # 初始化验证器
        validator = IPTVValidator(test_file_path, max_workers=2, timeout=2, debug=True)
        
        print(f"文件类型检测结果: {validator.file_type}")
        
        # 定义进度回调
        def progress_callback(progress_data):
            print(f"进度: {progress_data.get('progress')}% - 处理频道: {progress_data.get('channel', {}).get('name', '未知')}")
        
        # 读取JSON文件
        validator.read_json_file(progress_callback=progress_callback)
        
        print(f"提取到的频道数量: {len(validator.channels)}")
        print(f"分类列表: {validator.categories}")
        
        # 输出频道信息
        for channel in validator.channels:
            print(f"频道: {channel['name']} - URL: {channel['url']} - 分类: {channel['category']}")
        
        print("=== JSON验证流程测试成功 ===")
        return True
        
    except Exception as e:
        print(f"=== JSON验证流程测试失败: {str(e)} ===")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_m3u_validation():
    """测试M3U文件验证流程"""
    print("\n=== 测试M3U验证流程 ===")
    
    # 创建一个简单的测试M3U文件
    test_content = """#EXTM3U
#EXTINF:-1 group-title=\"新闻\",测试频道1
http://example.com/stream1
#EXTINF:-1 group-title=\"体育\",测试频道2
http://example.com/stream2
#EXTINF:-1 group-title=\"电影\",测试频道3
http://example.com/stream3"""
    
    test_file_path = "test_flow_m3u.m3u"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    
    try:
        # 初始化验证器
        validator = IPTVValidator(test_file_path, max_workers=2, timeout=2, debug=True)
        
        print(f"文件类型检测结果: {validator.file_type}")
        
        # 定义进度回调
        def progress_callback(progress_data):
            print(f"进度: {progress_data.get('progress')}% - 处理频道: {progress_data.get('channel', {}).get('name', '未知')}")
        
        # 读取M3U文件
        validator.read_m3u_file(progress_callback=progress_callback)
        
        print(f"提取到的频道数量: {len(validator.channels)}")
        print(f"分类列表: {validator.categories}")
        
        # 输出频道信息
        for channel in validator.channels:
            print(f"频道: {channel['name']} - URL: {channel['url']} - 分类: {channel['category']}")
        
        print("=== M3U验证流程测试成功 ===")
        return True
        
    except Exception as e:
        print(f"=== M3U验证流程测试失败: {str(e)} ===")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == "__main__":
    print("开始测试验证流程...")
    
    json_result = test_json_validation()
    m3u_result = test_m3u_validation()
    
    print(f"\n=== 测试结果 ===")
    print(f"JSON验证: {'成功' if json_result else '失败'}")
    print(f"M3U验证: {'成功' if m3u_result else '失败'}")
    
    if json_result and m3u_result:
        print("所有测试通过!")
        sys.exit(0)
    else:
        print("部分测试失败!")
        sys.exit(1)
