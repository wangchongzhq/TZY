#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为所有TXT文件进行直播源重复检查
完全相同的直播源仅保留一个即可，其他舍弃
"""

import os
import chardet
import sys

def detect_file_encoding(file_path):
    """检测文件编码"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(1024)
        result = chardet.detect(raw_data)
        return result['encoding']

def deduplicate_live_sources(file_path):
    """对指定文件进行直播源去重"""
    try:
        # 检测文件编码
        encoding = detect_file_encoding(file_path)
        print(f"处理文件: {file_path} (编码: {encoding})")
        
        # 读取文件内容
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        print(f"原始行数: {total_lines}")
        
        # 存储分类行和频道标题行
        result_lines = []
        # 存储已处理的直播源URL，用于去重
        unique_urls = set()
        
        # 处理每一行
        for line in lines:
            line = line.strip()
            
            # 保留空行、分类行和频道标题行
            if not line or line.startswith('#'):
                result_lines.append(line)
                continue
            
            # 处理直播源行 (频道名称,URL)
            if ',' in line:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    channel_name, url = parts
                    
                    # 检查URL是否已存在
                    if url not in unique_urls:
                        unique_urls.add(url)
                        result_lines.append(line)
        
        # 计算去重结果
        deduplicated_lines = len(result_lines)
        removed_lines = total_lines - deduplicated_lines
        
        # 写入去重后的内容
        with open(file_path, 'w', encoding=encoding) as f:
            f.write('\n'.join(result_lines))
        
        # 输出结果
        print(f"去重后行数: {deduplicated_lines}")
        print(f"移除重复行数: {removed_lines}")
        if total_lines > 0:
            print(f"减少比例: {removed_lines / total_lines:.2%}\n")
        
        return removed_lines
        
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return 0

def main():
    """主函数"""
    # 需要处理的TXT文件列表
    txt_files = [
        '4K_uhd_channels.txt',
        'CGQ.TXT', 
        'ipzy.txt',
        'ipzy_channels.txt',
        'ipzyauto.txt',
        'tzydayauto.txt'
    ]
    
    print("开始处理所有TXT文件的直播源去重...\n")
    
    total_removed = 0
    
    # 处理每个文件
    for file_name in txt_files:
        file_path = os.path.abspath(file_name)
        if os.path.exists(file_path):
            removed = deduplicate_live_sources(file_path)
            total_removed += removed
        else:
            print(f"文件不存在: {file_path}\n")
    
    print(f"\n去重完成! 总共移除 {total_removed} 行重复内容。")

if __name__ == "__main__":
    main()
