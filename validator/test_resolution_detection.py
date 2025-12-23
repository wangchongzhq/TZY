#!/usr/bin/env python3
"""
测试分辨率检测功能的脚本
"""

import sys
import os
import re

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from iptv_validator import IPTVValidator

def test_resolution_extraction_from_name():
    """测试从频道名称中提取分辨率"""
    print("=== 测试从频道名称中提取分辨率 ===")
    
    # 测试各种格式的频道名称
    test_names = [
        "CCTV1[1920*1080]",
        "CCTV2[1280*720]",
        "北京卫视4K[3840*2160]",
        "东方卫视[720*480]",
        "体育频道",  # 没有分辨率信息
        "电影频道[1024*576]高清",
        "综艺频道[854*480]标清"
    ]
    
    # 使用正则表达式测试
    for name in test_names:
        match = re.search(r'\[(\d+\*\d+)\]', name)
        resolution = match.group(1) if match else "未找到"
        print(f"频道名: {name} -> 分辨率: {resolution}")

def test_m3u_resolution_detection():
    """测试M3U文件中的分辨率检测"""
    print("\n=== 测试M3U文件中的分辨率检测 ===")
    
    test_file_path = "test_resolution.m3u"
    
    try:
        validator = IPTVValidator(test_file_path, debug=True)
        
        print(f"文件类型检测结果: {validator.file_type}")
        
        # 读取M3U文件
        channels, categories = validator.read_m3u_file()
        
        print(f"提取到的频道数量: {len(channels)}")
        print(f"分类列表: {categories}")
        
        # 输出频道信息，重点关注分辨率
        for channel in channels:
            print(f"频道: {channel['name']} - URL: {channel['url']} - 分类: {channel['category']} - 分辨率(从名称): {channel.get('resolution_from_name', '未找到')}")
        
        print("=== M3U分辨率检测测试成功 ===")
        return True
        
    except Exception as e:
        print(f"=== M3U分辨率检测测试失败: {str(e)} ===")
        import traceback
        traceback.print_exc()
        return False

def test_json_resolution_detection():
    """测试JSON文件中的分辨率检测"""
    print("\n=== 测试JSON文件中的分辨率检测 ===")
    
    # 创建一个包含分辨率信息的测试JSON文件
    test_data = {
        "channels": [
            {"name": "CCTV1[1920*1080]", "url": "http://example.com/cctv1", "category": "央视"},
            {"name": "CCTV2[1280*720]", "url": "http://example.com/cctv2", "category": "央视"},
            {"name": "体育频道", "url": "http://example.com/sports", "category": "体育"}
        ]
    }
    
    test_file_path = "test_resolution.json"
    with open(test_file_path, "w", encoding="utf-8") as f:
        import json
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    try:
        validator = IPTVValidator(test_file_path, debug=True)
        
        print(f"文件类型检测结果: {validator.file_type}")
        
        # 读取JSON文件
        channels, categories = validator.read_json_file()
        
        print(f"提取到的频道数量: {len(channels)}")
        print(f"分类列表: {categories}")
        
        # 输出频道信息，重点关注分辨率
        for channel in channels:
            print(f"频道: {channel['name']} - URL: {channel['url']} - 分类: {channel['category']} - 分辨率(从名称): {channel.get('resolution_from_name', '未找到')}")
        
        print("=== JSON分辨率检测测试成功 ===")
        return True
        
    except Exception as e:
        print(f"=== JSON分辨率检测测试失败: {str(e)} ===")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_txt_resolution_detection():
    """测试TXT文件中的分辨率检测"""
    print("\n=== 测试TXT文件中的分辨率检测 ===")
    
    # 创建一个包含分辨率信息的测试TXT文件
    test_content = """CCTV1[1920*1080],http://example.com/cctv1
CCTV2[1280*720],http://example.com/cctv2
体育频道,http://example.com/sports"""
    
    test_file_path = "test_resolution.txt"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    
    try:
        validator = IPTVValidator(test_file_path, debug=True)
        
        print(f"文件类型检测结果: {validator.file_type}")
        
        # 读取TXT文件
        channels, categories = validator.read_txt_file()
        
        print(f"提取到的频道数量: {len(channels)}")
        print(f"分类列表: {categories}")
        
        # 输出频道信息，重点关注分辨率
        for channel in channels:
            print(f"频道: {channel['name']} - URL: {channel['url']} - 分类: {channel['category']} - 分辨率(从名称): {channel.get('resolution_from_name', '未找到')}")
        
        print("=== TXT分辨率检测测试成功 ===")
        return True
        
    except Exception as e:
        print(f"=== TXT分辨率检测测试失败: {str(e)} ===")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == "__main__":
    print("开始测试分辨率检测功能...")
    
    test_resolution_extraction_from_name()
    m3u_result = test_m3u_resolution_detection()
    json_result = test_json_resolution_detection()
    txt_result = test_txt_resolution_detection()
    
    print(f"\n=== 测试结果 ===")
    print(f"M3U分辨率检测: {'成功' if m3u_result else '失败'}")
    print(f"JSON分辨率检测: {'成功' if json_result else '失败'}")
    print(f"TXT分辨率检测: {'成功' if txt_result else '失败'}")
    
    if m3u_result and json_result and txt_result:
        print("所有分辨率检测测试通过!")
        sys.exit(0)
    else:
        print("部分分辨率检测测试失败!")
        sys.exit(1)