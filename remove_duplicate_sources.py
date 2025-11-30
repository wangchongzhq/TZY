#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用于去除tzydauto.txt文件中重复的直播源
保留每个频道的唯一直播源，保持原始的频道分类和结构
"""

import os


def remove_duplicate_sources(input_file, output_file=None):
    """
    去除文件中重复的直播源
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径，如果为None则覆盖输入文件
    """
    if output_file is None:
        output_file = input_file
    
    # 读取文件内容
    print(f"正在读取文件: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"文件总行数: {len(lines)}")
    
    # 处理文件内容，去除重复的直播源
    processed_lines = []
    current_channel = None
    channel_sources = set()  # 用于存储当前频道的直播源
    duplicate_count = 0
    
    for line in lines:
        line = line.strip()
        
        # 如果是空行，直接添加
        if not line:
            processed_lines.append("")
            continue
        
        # 如果是分类行（以#开头但不是##）
        if line.startswith('#') and not line.startswith('##'):
            # 保存之前的频道信息（如果有）
            if current_channel and channel_sources:
                processed_lines.extend(channel_sources)
                channel_sources = set()
                current_channel = None
            processed_lines.append(line)
            continue
        
        # 如果是频道名称行（以##开头）
        if line.startswith('##'):
            # 保存之前的频道信息（如果有）
            if current_channel and channel_sources:
                processed_lines.extend(channel_sources)
                channel_sources = set()
            processed_lines.append(line)
            current_channel = line[2:]  # 提取频道名称（去除##前缀）
            continue
        
        # 如果是直播源行（包含逗号）
        if ',' in line:
            # 检查是否为重复的直播源
            if line not in channel_sources:
                channel_sources.add(line)
            else:
                duplicate_count += 1
            continue
        
        # 其他类型的行，直接添加
        processed_lines.append(line)
    
    # 添加最后一个频道的直播源
    if current_channel and channel_sources:
        processed_lines.extend(channel_sources)
    
    # 计算去重后的行数
    total_processed_lines = len(processed_lines)
    print(f"去重后行数: {total_processed_lines}")
    print(f"去除的重复行数: {duplicate_count}")
    print(f"减少的百分比: {duplicate_count / len(lines) * 100:.2f}%")
    
    # 写入处理后的内容
    print(f"正在写入文件: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in processed_lines:
            f.write(line + '\n')
    
    print("去重操作完成！")


if __name__ == "__main__":
    # 处理tzydauto.txt文件，去除重复的直播源
    input_file = "tzydauto.txt"
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 文件 {input_file} 不存在")
        exit(1)
    
    # 执行去重操作
    remove_duplicate_sources(input_file)
