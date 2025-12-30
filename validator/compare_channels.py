#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较原始文件和验证后文件，找出被标记为无效的频道
"""

import sys
import os
import re
from urllib.parse import urlparse

def read_channels(file_path):
    """读取频道文件，返回包含URL和名称的字典"""
    channels = {}
    with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('#'):
                continue
            if ',' in line:
                try:
                    # 使用与iptv_validator.py相同的解析逻辑
                    # 首先检查是否包含URL协议
                    url_pattern = r'(http[s]?://|rtsp://|rtmp://|mms://|udp://|rtp://)'
                    url_match = re.search(url_pattern, line)
                    if url_match:
                        # 找到URL的起始位置，前面的都是频道名称
                        url_start = url_match.start()
                        name = line[:url_start].rstrip(',').strip()
                        url = line[url_start:].strip()
                    else:
                        # 没有找到明确的URL协议，使用最后一个逗号分割
                        name, url = line.rsplit(',', 1)
                        name = name.strip()
                        url = url.strip()
                    
                    # 处理包含$符号的URL
                    if '$' in url:
                        url = url.split('$')[0]
                    
                    if name and url:
                        channels[url.strip()] = name.strip()
                except ValueError:
                    continue
    return channels

def validate_file_path(file_path):
    """验证文件路径的安全性"""
    if not file_path:
        return False
    
    # 检查路径长度
    if len(file_path) > 255:
        raise ValueError(f"文件路径过长: {file_path}")
    
    # 检查是否包含危险字符
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        if char in file_path:
            raise ValueError(f"文件路径包含危险字符 '{char}': {file_path}")
    
    # 检查是否尝试访问上级目录
    if '..' in file_path:
        raise ValueError(f"文件路径包含上级目录访问: {file_path}")
    
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='比较原始文件和验证后文件，找出被标记为无效的频道',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python compare_channels.py original.m3u valid.m3u
  python compare_channels.py channels.txt valid_channels.txt
        """
    )
    
    parser.add_argument('original_file', help='原始频道文件路径')
    parser.add_argument('valid_file', help='验证后的频道文件路径')
    parser.add_argument('--output', '-o', help='输出文件路径（可选）')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='显示详细的格式检查信息')
    
    try:
        args = parser.parse_args()
        
        # 验证输入文件路径
        try:
            validate_file_path(args.original_file)
            validate_file_path(args.valid_file)
        except ValueError as e:
            print(f"错误: 文件路径验证失败 - {e}")
            sys.exit(1)
        
        # 检查文件是否存在
        if not os.path.exists(args.original_file):
            print(f"错误: 原始文件 '{args.original_file}' 不存在")
            sys.exit(1)
        
        if not os.path.exists(args.valid_file):
            print(f"错误: 验证后的文件 '{args.valid_file}' 不存在")
            sys.exit(1)
        
        # 检查文件是否为普通文件
        if not os.path.isfile(args.original_file):
            print(f"错误: '{args.original_file}' 不是普通文件")
            sys.exit(1)
        elif not os.path.isfile(args.valid_file):
            print(f"错误: '{args.valid_file}' 不是普通文件")
            sys.exit(1)
    
        # 读取两个文件的频道
        original_channels = read_channels(args.original_file)
        valid_channels = read_channels(args.valid_file)
        
        print(f"原始频道数: {len(original_channels)}")
        print(f"有效频道数: {len(valid_channels)}")
        
        # 找出无效频道
        invalid_channels = {}
        for url, name in original_channels.items():
            found = False
            for valid_url in valid_channels.keys():
                # 比较基础URL（忽略可能的参数差异）
                if url in valid_url or valid_url in url:
                    found = True
                    break
            if not found:
                invalid_channels[url] = name
        
        print(f"无效频道数: {len(invalid_channels)}")
        
        # 打印无效频道
        if invalid_channels:
            print("\n无效频道列表:")
            output_lines = []
            for url, name in invalid_channels.items():
                line = f"{name},{url}"
                print(line)
                output_lines.append(line)
                
                # 分析为什么被标记为无效
                if args.verbose:
                    try:
                        parsed_url = urlparse(url)
                        print(f"  格式检查: scheme={parsed_url.scheme}, netloc={parsed_url.netloc}")
                    except Exception as e:
                        print(f"  格式解析错误: {e}")
            
            # 如果指定了输出文件，写入结果
            if args.output:
                try:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write("# 被标记为无效的频道\n")
                        f.write("# 频道名称,URL\n")
                        for line in output_lines:
                            f.write(line + "\n")
                    print(f"\n无效频道列表已保存到: {args.output}")
                except OSError as e:
                    print(f"错误: 无法写入输出文件 '{args.output}': {e}")
        else:
            print("\n所有频道都被标记为有效！")
            
    except KeyboardInterrupt:
        print("\n操作被用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()