#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单测试脚本：只测试文件写入功能
"""

import sys
import os

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

def test_file_write():
    """测试文件写入功能"""
    print("=== 测试文件写入功能 ===")
    try:
        test_content = "#EXTM3U\n\n# 测试频道分类\n# 频道数量: 2\n\n#EXTINF:-1 tvg-name=\"测试频道1\" group-title=\"测试分类\",测试频道1\nhttp://example.com/test1.m3u8\n\n#EXTINF:-1 tvg-name=\"测试频道2\" group-title=\"测试分类\",测试频道2\nhttp://example.com/test2.m3u8\n"
        
        with open('test_cgq_write.txt', 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # 验证文件是否写入成功
        if os.path.exists('test_cgq_write.txt'):
            size = os.path.getsize('test_cgq_write.txt')
            print(f"✅ 文件写入成功")
            print(f"✅ 文件名: test_cgq_write.txt")
            print(f"✅ 文件大小: {size} 字节")
            
            # 读取文件内容验证
            with open('test_cgq_write.txt', 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"✅ 文件内容长度: {len(content)} 字符")
                print(f"✅ 文件内容前50字符: {content[:50]}...")
            return True
        else:
            print("❌ 文件写入失败，文件不存在")
            
    except Exception as e:
        print(f"❌ 文件写入异常: {e}")
    return False

def test_get_cgq_functionality():
    """测试CGQ.TXT的基本功能模拟"""
    print("\n=== 测试CGQ.TXT功能模拟 ===")
    try:
        # 模拟一些频道数据
        categorized_channels = {
            "4K央视频道": [
                ("CCTV-4K", "http://example.com/cctv4k.m3u8"),
                ("CCTV-1 4K", "http://example.com/cctv14k.m3u8")
            ],
            "高清频道": [
                ("湖南卫视高清", "http://example.com/hunanhd.m3u8"),
                ("浙江卫视高清", "http://example.com/zhejianghd.m3u8")
            ]
        }
        
        # 写入CGQ.TXT文件
        with open('CGQ.TXT', 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n\n")
            
            for category, channels in categorized_channels.items():
                f.write(f"# 频道分类: {category}\n")
                f.write(f"# 频道数量: {len(channels)}\n\n")
                
                for channel_name, channel_url in sorted(channels, key=lambda x: x[0]):
                    f.write(f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"{category}\",{channel_name}\n")
                    f.write(f"{channel_url}\n\n")
        
        print("✅ CGQ.TXT 文件重写成功")
        print("✅ 添加了模拟的频道数据")
        
        # 检查文件内容
        with open('CGQ.TXT', 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"✅ CGQ.TXT 内容长度: {len(content)} 字符")
            print(f"✅ 文件内容预览:")
            print(content[:200] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ CGQ.TXT 测试失败: {e}")
    return False

def main():
    print("开始简单功能测试...")
    
    # 测试基本文件写入
    test_file_write()
    
    # 测试CGQ.TXT功能
    test_get_cgq_functionality()
    
    print("\n测试完成！")
    return 0

if __name__ == "__main__":
    sys.exit(main())
