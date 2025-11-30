#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用于解决tzydauto.txt文件中的Git合并冲突
保留去重后的内容，移除所有冲突标记
"""

import os


def resolve_merge_conflicts(input_file, output_file=None):
    """
    解决文件中的Git合并冲突
    
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
    
    # 处理冲突并去重
    processed_lines = []
    current_section = None  # None, 'ours', 'theirs', 'common'
    channel_sources = set()  # 用于存储当前频道的直播源
    conflict_count = 0
    
    for line in lines:
        line = line.rstrip()  # 去除行尾的换行符和空格
        
        # 处理冲突标记
        if line.startswith('<<<<<<<'):
            current_section = 'ours'
            conflict_count += 1
            continue
        elif line.startswith('======='):
            current_section = 'theirs'
            continue
        elif line.startswith('>>>>>>>'):
            current_section = 'common'
            # 添加当前频道的直播源到结果中
            if channel_sources:
                processed_lines.extend(channel_sources)
                channel_sources = set()
            continue
        
        # 如果是空行，直接添加
        if not line:
            processed_lines.append("")
            continue
        
        # 如果是分类行（以#开头但不是##）
        if line.startswith('#') and not line.startswith('##'):
            # 保存之前的频道信息（如果有）
            if channel_sources:
                processed_lines.extend(channel_sources)
                channel_sources = set()
            processed_lines.append(line)
            continue
        
        # 如果是频道名称行（以##开头）
        if line.startswith('##'):
            # 保存之前的频道信息（如果有）
            if channel_sources:
                processed_lines.extend(channel_sources)
                channel_sources = set()
            processed_lines.append(line)
            continue
        
        # 如果是直播源行（包含逗号）
        if ',' in line:
            # 将直播源添加到集合中（自动去重）
            channel_sources.add(line)
            continue
        
        # 其他类型的行，直接添加
        processed_lines.append(line)
    
    # 添加最后一个频道的直播源
    if channel_sources:
        processed_lines.extend(channel_sources)
    
    # 计算处理后的行数
    total_processed_lines = len(processed_lines)
    print(f"解决的冲突数: {conflict_count}")
    print(f"处理后行数: {total_processed_lines}")
    print(f"减少的行数: {len(lines) - total_processed_lines}")
    print(f"减少的百分比: {(len(lines) - total_processed_lines) / len(lines) * 100:.2f}%")
    
    # 写入处理后的内容
    print(f"正在写入文件: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in processed_lines:
            f.write(line + '\n')
    
    print("冲突解决完成！")


if __name__ == "__main__":
    # 处理tzydauto.txt文件，解决合并冲突
    input_file = "tzydauto.txt"
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 文件 {input_file} 不存在")
        exit(1)
    
    # 执行冲突解决操作
    resolve_merge_conflicts(input_file)
