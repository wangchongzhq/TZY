#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查扩展后的4K频道识别效果
"""

import os
from collections import defaultdict

def check_4k_channels():
    """检查4K频道的识别情况"""
    
    # 检查TXT格式文件
    txt_file = "output/iptv.txt"
    if os.path.exists(txt_file):
        print("=== 检查 TXT 格式文件 (output/iptv.txt) ===")
        
        # 统计不同类型的4K频道数量
        counts = {
            "4K": 0,
            "4k": 0,
            "8K": 0,
            "8k": 0,
            "超高清": 0,
            "2160": 0
        }
        
        # 收集不同类型的4K频道示例
        examples = defaultdict(list)
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                channel_name = line.split(',')[0] if ',' in line else line
                
                for key in counts.keys():
                    if key in channel_name:
                        counts[key] += 1
                        if len(examples[key]) < 3:  # 每个类型最多显示3个示例
                            examples[key].append(channel_name)
        
        # 输出统计结果
        print("不同类型4K频道的识别数量:")
        total = 0
        for key, count in counts.items():
            print(f"- {key}: {count}个频道")
            total += count
        print(f"总计: {total}个频道")
        
        # 输出示例
        print("\n不同类型4K频道的示例:")
        for key, ex_list in examples.items():
            if ex_list:
                print(f"- {key}:")
                for ex in ex_list:
                    print(f"  {ex}")
    else:
        print(f"文件 {txt_file} 不存在")
    
    # 检查M3U格式文件
    m3u_file = "output/iptv.m3u"
    if os.path.exists(m3u_file):
        print("\n=== 检查 M3U 格式文件 (output/iptv.m3u) ===")
        
        # 统计4K频道分类中的频道数量
        channel_count = 0
        
        with open(m3u_file, 'r', encoding='utf-8') as f:
            for line in f:
                if 'group-title="4K频道"' in line:
                    channel_count += 1
        
        print(f"4K频道分类中包含 {channel_count} 个频道")
        
        # 检查不同类型的4K频道是否都被归类到4K频道
        print("\n检查不同类型的4K频道分类情况:")
        
        # 读取文件内容
        with open(m3u_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查各种类型的4K频道
        types_to_check = [
            "4K", "4k", "8K", "8k", "超高清", "2160"
        ]
        
        for type_key in types_to_check:
            # 搜索包含该类型的频道行
            lines = content.split('\n')
            found = False
            
            for i, line in enumerate(lines):
                if type_key in line and i > 0:
                    # 检查前一行是否包含4K频道分类
                    prev_line = lines[i-1]
                    if 'group-title="4K频道"' in prev_line:
                        print(f"✓ {type_key} 类型的频道被正确归类到4K频道")
                        found = True
                        break
            
            if not found:
                print(f"? 未找到 {type_key} 类型的频道归类信息")
    else:
        print(f"文件 {m3u_file} 不存在")

if __name__ == "__main__":
    check_4k_channels()
