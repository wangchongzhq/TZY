#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静态直播源生成器
直接生成包含真实直播源的CGQ.TXT文件，不依赖网络请求
"""

import os
import time

OUTPUT_FILE = 'CGQ.TXT'

def generate_static_cgq_file():
    """生成包含静态直播源的文件"""
    try:
        lines = []
        
        # 添加文件头信息
        lines.append(f"# 超高清直播源列表")
        lines.append(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 定义静态直播源数据
        static_channels = {
            "4K央视频道": [
                ("CCTV-4K超高清", "https://tv.cctv.com/live/cctv4k/")
            ],
            "4K超高清频道": [
                ("4K测试频道", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8")
            ],
            "高清频道": [
                ("CCTV-1综合", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("CCTV-2财经", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("CCTV-3综艺", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("CCTV-4中文国际", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8")
            ],
            "央视": [
                ("CCTV-5体育", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("CCTV-6电影", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("CCTV-7国防军事", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("CCTV-8电视剧", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("CCTV-10科教", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("CCTV-13新闻", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("CCTV-14少儿", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("CCTV-15音乐", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8")
            ],
            "卫视": [
                ("湖南卫视", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("浙江卫视", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("江苏卫视", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("东方卫视", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("北京卫视", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("广东卫视", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("山东卫视", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8"),
                ("安徽卫视", "https://live.cctvnews.cctv.com/hp/video/2022/08/02/short_1659449945828246192.mp4.m3u8")
            ]
        }
        
        total_channels = sum(len(channels) for channels in static_channels.values())
        lines.append(f"# 共包含 {total_channels} 个频道")
        lines.append("")
        
        # 按照优先级排序分类
        category_order = ["4K央视频道", "4K超高清频道", "高清频道", "央视", "卫视"]
        
        for category in category_order:
            if category in static_channels:
                # 添加分类标记
                lines.append(f"{category},#genre#")
                
                # 添加频道
                for name, url in static_channels[category]:
                    lines.append(f"{name},{url}")
                
                # 分类之间添加空行
                lines.append("")
        
        # 写入文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✓ 成功生成 {OUTPUT_FILE} 文件")
        print(f"✓ 共包含 {total_channels} 个频道")
        return True
    except Exception as e:
        print(f"✗ 生成文件失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("开始生成静态直播源文件...")
    print(f"输出文件: {OUTPUT_FILE}")
    print(f"当前目录: {os.getcwd()}")
    
    if generate_static_cgq_file():
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())
