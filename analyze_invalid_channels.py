#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析被验证工具标记为无效的频道
比较原始文件和有效文件，找出被误判的频道
"""

import re
import os

def extract_base_url(url):
    """从URL中提取基础URL，去除$符号及其后面的内容"""
    if '$' in url:
        return url.split('$')[0]
    return url

def read_channels(file_path):
    """从文件中读取频道信息，返回字典 {base_url: name} """
    channels = {}
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('//'):
                    continue
                if ',' in line:
                    name, url = line.split(',', 1)
                    name = name.strip()
                    url = url.strip()
                    base_url = extract_base_url(url)
                    channels[base_url] = name
    except (IOError, OSError) as e:
        print(f"读取文件 {file_path} 时出错: 文件操作错误 - {e}")
    except (ValueError, TypeError) as e:
        print(f"读取文件 {file_path} 时出错: 数据格式错误 - {e}")
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: 未知错误 - {e}")
    return channels

def analyze_invalid_channels(original_file, valid_file):
    """分析无效频道"""
    # 读取原始文件和有效文件中的频道
    original_channels = read_channels(original_file)
    valid_channels = read_channels(valid_file)
    
    # 找出未通过验证的频道
    invalid_channels = {}
    for base_url, name in original_channels.items():
        if base_url not in valid_channels:
            invalid_channels[base_url] = name
    
    print(f"原始频道总数: {len(original_channels)}")
    print(f"有效频道数: {len(valid_channels)}")
    print(f"无效频道数: {len(invalid_channels)}")
    
    # 分析无效频道的类型
    print("\n无效频道类型分析:")
    protocol_counts = {}
    for base_url, name in invalid_channels.items():
        if 'http://' in base_url:
            protocol = 'http'
        elif 'https://' in base_url:
            protocol = 'https'
        elif 'rtsp://' in base_url:
            protocol = 'rtsp'
        elif 'rtmp://' in base_url:
            protocol = 'rtmp'
        elif 'udp://' in base_url:
            protocol = 'udp'
        elif 'rtp://' in base_url:
            protocol = 'rtp'
        elif 'mms://' in base_url:
            protocol = 'mms'
        else:
            protocol = 'unknown'
        
        protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
    
    for protocol, count in protocol_counts.items():
        print(f"  {protocol}: {count} 个频道")
    
    # 检查是否包含动态参数
    print("\n包含动态参数的无效频道:")
    dynamic_param_pattern = re.compile(r'(\{[A-Z_]+\}|%7B[A-Z_]+%7D)')
    dynamic_count = 0
    for base_url, name in invalid_channels.items():
        if dynamic_param_pattern.search(base_url):
            dynamic_count += 1
            print(f"  {name}: {base_url}")
    print(f"\n总共有 {dynamic_count} 个包含动态参数的无效频道")
    
    # 检查是否包含IPv6地址
    print("\n包含IPv6地址的无效频道:")
    ipv6_count = 0
    for base_url, name in invalid_channels.items():
        if ':' in base_url and '://' in base_url:
            hostname_part = base_url.split('://')[1].split('/')[0]
            if (':' in hostname_part and not hostname_part.startswith('[') and not hostname_part.replace('.', '').replace(':', '').isdigit()) or (hostname_part.startswith('[') and hostname_part.endswith(']')):
                ipv6_count += 1
                print(f"  {name}: {base_url}")
    print(f"\n总共有 {ipv6_count} 个包含IPv6地址的无效频道")
    
    # 将无效频道保存到文件
    invalid_file = "invalid_channels.txt"
    with open(invalid_file, 'w', encoding='utf-8') as f:
        f.write("# 被标记为无效的频道\n")
        f.write("# 频道名称,原始URL\n")
        for base_url, name in invalid_channels.items():
            f.write(f"{name},{base_url}\n")
    
    print(f"\n无效频道列表已保存到 {invalid_file}")
    return invalid_channels

if __name__ == "__main__":
    import sys
    import argparse
    
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
    
    parser = argparse.ArgumentParser(
        description='分析被验证工具标记为无效的频道',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python analyze_invalid_channels.py original.m3u outputs/original_valid.m3u
  python analyze_invalid_channels.py channels.txt valid_channels.txt
        """
    )
    
    parser.add_argument('original_file', help='原始频道文件路径')
    parser.add_argument('valid_file', help='有效频道文件路径')
    parser.add_argument('--output', '-o', default='invalid_channels.txt', 
                       help='输出文件名 (默认: invalid_channels.txt)')
    
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
        elif not os.path.exists(args.valid_file):
            print(f"错误: 有效文件 '{args.valid_file}' 不存在")
            sys.exit(1)
        
        # 检查文件是否为普通文件
        if not os.path.isfile(args.original_file):
            print(f"错误: '{args.original_file}' 不是普通文件")
            sys.exit(1)
        elif not os.path.isfile(args.valid_file):
            print(f"错误: '{args.valid_file}' 不是普通文件")
            sys.exit(1)
        
        # 验证输出目录
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                print(f"错误: 无法创建输出目录 '{output_dir}': {e}")
                sys.exit(1)
        
        # 执行分析
        invalid_channels = analyze_invalid_channels(args.original_file, args.valid_file)
        
        # 将无效频道保存到指定文件
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write("# 被标记为无效的频道\n")
                f.write("# 频道名称,原始URL\n")
                for base_url, name in invalid_channels.items():
                    f.write(f"{name},{base_url}\n")
            print(f"\n无效频道列表已保存到 {args.output}")
        except OSError as e:
            print(f"错误: 无法写入输出文件 '{args.output}': {e}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n操作被用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
