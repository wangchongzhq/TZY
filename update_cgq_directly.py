#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接更新CGQ.TXT文件的脚本
"""

import os
import time

# 输出文件
OUTPUT_FILE = 'CGQ.TXT'

# 基于提供的直播源数据构建频道列表
def main():
    # 创建频道数据
    categorized_channels = {
        "4K央视频道": [
            ("CCTV-4K超高清", "https://tv.cctv.com/live/cctv4k/", True),
            ("CCTV16奥林匹克", "https://tv.cctv.com/live/cctv16/", True)
        ],
        "4K超高清频道": [
            ("北京卫视4K", "https://www.shqsy.com/zgst.php?id=btv4k", True),
            ("东方卫视4K", "https://www.shqsy.com/zgst.php?id=sh4k", True),
            ("江苏卫视4K", "https://www.shqsy.com/zgst.php?id=js4k", True),
            ("浙江卫视4K", "https://www.shqsy.com/zgst.php?id=zj4k", True),
            ("广东卫视4K", "https://www.shqsy.com/zgst.php?id=gd4k", True)
        ],
        "高清频道": [
            ("河南卫视", "http://tvcdn.stream3.hndt.com/tv/65c4a6d5017e1000b2b6ea2500000000_transios/playlist.m3u8", False),
            ("新闻频道", "http://tvcdn.stream3.hndt.com/tv/65bb6966017e100059b75a8500000000_transios/playlist.m3u8", False),
            ("都市频道", "http://tvcdn.stream3.hndt.com/tv/65c3fbc5017e1000fde13faa00000000_transios/playlist.m3u8", False)
        ],
        "央视": [
            ("CCTV-1综合", "http://124.116.183.146:9901/tsfile/live/0001_1.m3u8", False),
            ("CCTV-2财经", "http://112.6.239.227:8207/hls/2/index.m3u8", False),
            ("CCTV-3综艺", "http://112.6.239.227:8207/hls/3/index.m3u8", False),
            ("CCTV-4中文国际", "http://1.24.39.180:9003/hls/4/index.m3u8", False),
            ("CCTV-5体育", "http://112.6.239.227:8207/hls/5/index.m3u8", False),
            ("CCTV-6电影", "http://124.116.183.146:9901/tsfile/live/0006_1.m3u8", False),
            ("CCTV-7国防军事", "http://sh.lnott.top:880/dx07.m3u8", False),
            ("CCTV-8电视剧", "http://112.6.239.227:8207/hls/8/index.m3u8", False)
        ],
        "卫视": [
            ("湖南卫视", "https://migu.188766.xyz/?migutoken=ec3b1ac9e5deea00bcb769b2185aa27b&id=HUNANTV&type=yy", False),
            ("浙江卫视", "https://migu.188766.xyz/?migutoken=ec3b1ac9e5deea00bcb769b2185aa27b&id=ZJTV&type=yy", False),
            ("江苏卫视", "https://migu.188766.xyz/?migutoken=ec3b1ac9e5deea00bcb769b2185aa27b&id=JSTV&type=yy", False),
            ("东方卫视", "https://migu.188766.xyz/?migutoken=ec3b1ac9e5deea00bcb769b2185aa27b&id=DONGFANG&type=yy", False),
            ("北京卫视", "https://migu.188766.xyz/?migutoken=ec3b1ac9e5deea00bcb769b2185aa27b&id=BTV&type=yy", False)
        ]
    }
    
    # 生成文件内容
    lines = []
    
    # 添加文件头信息
    lines.append(f"# 超高清直播源列表")
    lines.append(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    total_channels = sum(len(channels) for channels in categorized_channels.values())
    lines.append(f"# 共包含 {total_channels} 个频道")
    lines.append("")
    
    # 按照优先级排序分类
    category_order = ["4K央视频道", "4K超高清频道", "高清频道", "央视", "卫视"]
    
    for category in category_order:
        if category in categorized_channels:
            # 添加分类标记
            lines.append(f"{category},#genre#")
            
            # 按频道名称排序
            channels = sorted(categorized_channels[category], key=lambda x: x[0])
            
            for name, url, _ in channels:
                lines.append(f"{name},{url}")
            
            # 分类之间添加空行
            lines.append("")
    
    # 写入文件
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✓ 成功生成 {OUTPUT_FILE} 文件")
        print(f"共写入 {len(lines)} 行数据，包含 {total_channels} 个频道")
        return 0
    except Exception as e:
        print(f"✗ 写入文件失败: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
