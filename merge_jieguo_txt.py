#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并jieguo_i4.txt和jieguo_i6.txt生成jieguo.txt
"""

import os
import datetime

def merge_jieguo_txt():
    """合并jieguo_i4.txt和jieguo_i6.txt生成jieguo.txt"""
    
    # 定义文件路径，支持新旧文件名
    ipv4_file = "jieguo_i4.txt"
    ipv6_file = "jieguo_i6.txt"
    output_file = "jieguo.txt"
    
    # 检查文件是否存在，支持新旧文件名
    if not os.path.exists(ipv4_file):
        # 尝试使用新的文件名
        ipv4_file = "ip-tv_i4.txt"
        if not os.path.exists(ipv4_file):
            print(f"错误: jieguo_i4.txt 或 ip-tv_i4.txt 文件不存在")
            return False
    
    if not os.path.exists(ipv6_file):
        # 尝试使用新的文件名
        ipv6_file = "ip-tv_i6.txt"
        if not os.path.exists(ipv6_file):
            print(f"错误: jieguo_i6.txt 或 ip-tv_i6.txt 文件不存在")
            return False
    
    # 读取ipv4文件内容
    with open(ipv4_file, 'r', encoding='utf-8') as f:
        ipv4_content = f.readlines()
    
    # 读取ipv6文件内容
    with open(ipv6_file, 'r', encoding='utf-8') as f:
        ipv6_content = f.readlines()
    
    # 解析文件头
    header = []
    for line in ipv4_content:
        if line.strip().startswith('#'):
            header.append(line)
        else:
            break
    
    # 更新生成时间
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for i, line in enumerate(header):
        if "生成时间" in line:
            header[i] = f"# 生成时间: {current_time}\n"
            break
    
    # 解析频道数据
    def parse_channels(content):
        """解析频道数据，返回分类到频道的字典"""
        channels = {}
        current_category = None
        for line in content:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#') and line.endswith(',genre#'):
                # 找到分类
                category = line[1:-7]  # 去掉#和,genre#
                # 处理分类名称后面可能存在的#号
                if category.endswith('#'):
                    category = category[:-1]
                current_category = category
                if category not in channels:
                    channels[category] = set()
            elif current_category and ',' in line and not line.startswith('#'):
                # 找到频道
                channels[current_category].add(line)
        return channels
    
    ipv4_channels = parse_channels(ipv4_content)
    ipv6_channels = parse_channels(ipv6_content)
    
    # 合并频道数据
    merged_channels = {}
    for category in ipv4_channels:
        merged_channels[category] = ipv4_channels[category].copy()
    
    for category in ipv6_channels:
        if category not in merged_channels:
            merged_channels[category] = set()
        merged_channels[category].update(ipv6_channels[category])
    
    # 按照要求的分类顺序排序
    required_order = [
        "4K频道", "央视频道", "卫视频道", "北京专属频道", "山东专属频道", 
        "港澳频道", "电影频道", "儿童频道", "iHOT频道", "综合频道", 
        "体育频道", "剧场频道", "其他频道"
    ]
    
    # 确保所有分类都在required_order中
    for category in list(merged_channels.keys()):
        if category not in required_order:
            required_order.append(category)
    
    # 生成输出内容
    output_lines = header
    
    for category in required_order:
        if category in merged_channels and merged_channels[category]:
            output_lines.append(f"#{category}#,genre#\n")
            # 按频道名称排序
            sorted_channels = sorted(merged_channels[category])
            for channel in sorted_channels:
                output_lines.append(f"{channel}\n")
            output_lines.append("\n")
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.writelines(output_lines)
    
    print(f"✅ 成功生成 {output_file}")
    print(f"   包含 {sum(len(channels) for channels in merged_channels.values())} 个频道")
    print(f"   包含 {len(merged_channels)} 个分类")
    
    # 同时生成新的文件名作为兼容
    new_output_file = "ip-tv.txt"
    with open(new_output_file, 'w', encoding='utf-8-sig') as f:
        f.writelines(output_lines)
    print(f"✅ 同时生成兼容的 {new_output_file}")
    
    return True

if __name__ == "__main__":
    merge_jieguo_txt()