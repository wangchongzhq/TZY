#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查输出文件中被错误分类为4K频道的频道
"""

def parse_m3u_file(file_path):
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='gbk') as f:
            content = f.read()
    
    # 按#EXTINF分割文件内容
    sections = content.split('#EXTINF:')
    # 收集错误分类的频道信息
    wrong_4k_channels = []
    
    # 遍历每个频道部分
    for section in sections[1:]:
        if 'group-title="4K频道"' in section:
            # 提取频道名称
            lines = section.split('\n')
            if len(lines) < 2:
                continue
                
            info_line = lines[0].strip()
            if ',' not in info_line:
                continue
                
            channel_name = info_line.split(',')[-1].strip()
            
            # 检查频道名称是否包含4K相关关键词
            name_lower = channel_name.lower()
            has_4k_keyword = any(keyword in name_lower for keyword in ['4k', '8k', '超高清', '2160'])
            
            if not has_4k_keyword:
                # 提取URL
                url = ''
                for line in lines[1:]:
                    line = line.strip()
                    if line.startswith('http://') or line.startswith('https://'):
                        url = line
                        break
                        
                wrong_4k_channels.append((channel_name, url))
    
    return wrong_4k_channels

def main():
    file_path = './output/iptv_ipv4.m3u'
    wrong_4k_channels = parse_m3u_file(file_path)
    
    # 将结果保存到文件
    with open('wrong_4k_channels.txt', 'w', encoding='utf-8') as f:
        if wrong_4k_channels:
            f.write(f"发现 {len(wrong_4k_channels)} 个错误分类的4K频道（名称不含4K/8K/超高清/2160关键词）:\n")
            for i, (channel_name, url) in enumerate(wrong_4k_channels):
                f.write(f"  {i+1}. 频道名称: {channel_name}, URL: {url}\n")
            print(f"\n发现 {len(wrong_4k_channels)} 个错误分类的4K频道，结果已保存到 wrong_4k_channels.txt 文件中。")
        else:
            f.write("没有发现错误分类的4K频道。\n")
            print("没有发现错误分类的4K频道，结果已保存到 wrong_4k_channels.txt 文件中。")

if __name__ == "__main__":
    main()