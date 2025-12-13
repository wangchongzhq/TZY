#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查输出文件中被错误分类为4K频道的频道
"""

from typing import List, Dict

# 解析M3U文件并筛选错误分类的4K频道
def parse_m3u_file(file_path: str) -> List[Dict[str, str]]:
    """解析本地M3U文件，返回所有被错误分类为4K频道的频道信息"""
    wrong_channels = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # 如果UTF-8解码失败，尝试使用GBK
        with open(file_path, 'r', encoding='gbk') as f:
            lines = f.readlines()
    
    current_name = None
    current_url = None
    in_4k_group = False
    
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            # 提取频道名称
            if "," in line:
                current_name = line.split(",", 1)[1].strip()
            else:
                current_name = None
            # 检查是否在4K频道分组
            in_4k_group = "group-title=\"4K频道\"" in line
        elif line.startswith("http://") or line.startswith("https://"):
            if current_name and in_4k_group:
                current_url = line
                # 检查频道名称中是否包含4K关键词
                name_lower = current_name.lower()
                if "4k" not in name_lower and "8k" not in name_lower and "超高清" not in current_name and "2160" not in current_name:
                    wrong_channels.append({"name": current_name, "url": current_url})
            current_name = None
            current_url = None
            in_4k_group = False
    
    return wrong_channels

# 主函数
def main():
    try:
        # 设置本地文件路径
        local_file_path = "./output/iptv_ipv4.m3u"
        
        # 解析并筛选错误分类的频道
        print(f"正在解析本地文件: {local_file_path}")
        wrong_channels = parse_m3u_file(local_file_path)
        
        # 输出结果
        print(f"\n发现 {len(wrong_channels)} 个被错误分类为4K频道的频道:")
        print("=" * 60)
        for i, channel in enumerate(wrong_channels[:20]):  # 只显示前20个
            print(f"{i+1}. 频道名称: {channel['name']}")
            print(f"   URL: {channel['url']}")
            print()
        
        if len(wrong_channels) > 20:
            print(f"... 还有 {len(wrong_channels) - 20} 个错误分类的频道未显示")
            
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
    
