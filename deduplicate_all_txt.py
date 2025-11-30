#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为所有TXT文件进行直播源重复检查
完全相同的直播源仅保留一个即可，其他舍弃
"""

import os
import chardet

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
        
        # 读取文件内容
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()
        
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
        
        # 写入去重后的内容
        with open(file_path, 'w', encoding=encoding) as f:
            f.write('\n'.join(result_lines))
        
        return True
        
    except:
        return False

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
    
    # 处理每个文件
    for file_name in txt_files:
        file_path = os.path.abspath(file_name)
        if os.path.exists(file_path):
            deduplicate_live_sources(file_path)

if __name__ == "__main__":
    main()
