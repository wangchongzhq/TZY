#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import re

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 复制IPTVValidator类中的正则表达式定义
re_group_title = re.compile(r'group-title="([^"]+)"')
re_resolution = re.compile(r'(\d+p)')


def debug_m3u_parse(file_path):
    """调试M3U文件解析"""
    print(f"开始调试M3U文件解析: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        return
    
    total_channels = 0
    parsed_channels = 0
    channel_buffer = {}
    
    # 第一次遍历：计算总频道数
    print("\n=== 第一次遍历：计算总频道数 ===")
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip().startswith('#EXTINF:'):
                    total_channels += 1
                    if total_channels <= 5:
                        print(f"第{line_num}行: {line.strip()}")
        print(f"总频道数: {total_channels}")
    except Exception as e:
        print(f"第一次遍历出错: {str(e)}")
        return
    
    # 第二次遍历：解析频道信息
    print("\n=== 第二次遍历：解析频道信息 ===")
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                print(f"第{line_num}行: {repr(line)}")
                
                # 解析EXTINF行
                if line.startswith('#EXTINF:'):
                    print("  -> 是EXTINF行")
                    # 提取频道名称
                    try:
                        name_part = line.split(',', 1)[1]
                        channel_buffer['name'] = name_part.strip()
                        print(f"  -> 频道名称: {channel_buffer['name']}")
                    except IndexError:
                        print("  -> 解析频道名称失败")
                        channel_buffer.clear()
                        continue
                    
                    # 提取分类信息
                    category_match = re_group_title.search(line)
                    if category_match:
                        channel_buffer['category'] = category_match.group(1)
                        print(f"  -> 分类: {channel_buffer['category']}")
                    else:
                        print("  -> 未找到分类信息")
                        channel_buffer['category'] = '未分类'
                    
                # 解析URL行
                elif not line.startswith('#') and channel_buffer.get('name'):
                    print("  -> 是URL行")
                    channel_buffer['url'] = line.strip().strip('`')
                    print(f"  -> URL: {channel_buffer['url']}")
                    
                    parsed_channels += 1
                    print(f"  -> 成功解析第{parsed_channels}个频道")
                    
                    # 重置缓冲区
                    channel_buffer.clear()
                    
                    if parsed_channels >= 5:
                        print("  -> 已解析5个频道，停止输出详情")
                    elif parsed_channels > 0 and parsed_channels % 100 == 0:
                        print(f"  -> 已解析{parsed_channels}个频道")
                
    except Exception as e:
        print(f"第二次遍历出错: {str(e)}")
    
    print(f"\n=== 解析完成 ===")
    print(f"总频道数: {total_channels}")
    print(f"成功解析频道数: {parsed_channels}")
    
    if parsed_channels == 0:
        print("\n问题分析:")
        print("1. 检查文件编码是否正确")
        print("2. 检查EXTINF行格式是否标准")
        print("3. 检查URL行是否紧跟在EXTINF行之后")

if __name__ == "__main__":
    file_path = "C:\\Users\\Administrator\\Documents\\GitHub\\TZY\\jieguo.m3u"
    debug_m3u_parse(file_path)
