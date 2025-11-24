#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
静态更新CGQ.TXT文件的脚本
直接将新增的直播源添加到文件中，避免复杂的处理逻辑
"""

import os
import sys

# 确保使用UTF-8编码
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 配置
OUTPUT_FILE = "CGQ.TXT"

# 新增的直播源URL
NEW_LIVE_SOURCES = [
    # 新增的直播源
    "https://raw.githubusercontent.com/Supprise0901/tvlist/main/live.txt",
    "https://raw.githubusercontent.com/ffmking/TVlist/main/live.txt",
    "https://raw.githubusercontent.com/qingtingjjjjjjj/tvlist1/main/live.txt",
    "https://raw.githubusercontent.com/zhonghu32/live/main/888.txt",
    "https://raw.githubusercontent.com/cuijian01/dianshi/main/888.txt",
    "https://raw.githubusercontent.com/xyy0508/iptv/main/888.txt",
    "https://raw.githubusercontent.com/zhonghu32/live/main/live.txt",
    "https://raw.githubusercontent.com/cuijian01/dianshi/main/live.txt",
]

# 原有直播源URL
ORIGINAL_LIVE_SOURCES = [
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "https://raw.githubusercontent.com/MeooPlayer/China-M3U-List/main/China_UHD.m3u",
    "https://raw.githubusercontent.com/MeooPlayer/China-M3U-List/main/China_HD.m3u",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt",
    "https://ghfast.top/raw.githubusercontent.com/ffmking/tv1/main/888.txt",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/kimwang1978/collect-txt/refs/heads/main/bbxx.txt",
]

def main():
    print(f"[静态更新] 开始更新 {OUTPUT_FILE}")
    
    # 合并所有直播源（保留原有顺序，在末尾添加新源）
    all_sources = ORIGINAL_LIVE_SOURCES.copy()
    all_sources.extend(NEW_LIVE_SOURCES)
    
    print(f"[静态更新] 总共包含 {len(all_sources)} 个直播源URL")
    print(f"[静态更新] 原有直播源: {len(ORIGINAL_LIVE_SOURCES)} 个")
    print(f"[静态更新] 新增直播源: {len(NEW_LIVE_SOURCES)} 个")
    
    # 创建文件内容
    file_content = "# 超高清直播源\n# 更新时间: 静态更新\n\n"
    file_content += "[央视频道]\n"
    file_content += "CCTV-1|https://example.com/cctv1\n"
    file_content += "CCTV-2|https://example.com/cctv2\n"
    file_content += "CCTV-3|https://example.com/cctv3\n"
    file_content += "CCTV-4|https://example.com/cctv4\n"
    file_content += "CCTV-5|https://example.com/cctv5\n"
    
    file_content += "\n[4K超高清频道]\n"
    file_content += "CCTV-4K|https://example.com/cctv4k\n"
    file_content += "CCTV-16 奥林匹克4K|https://example.com/cctv16-4k\n"
    
    file_content += "\n[直播源URL列表]\n"
    for i, source in enumerate(all_sources, 1):
        file_content += f"{i}. {source}\n"
    
    # 写入文件
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(file_content)
        print(f"[静态更新] 成功写入 {OUTPUT_FILE}")
        print(f"[静态更新] 文件内容预览:")
        print("--- 文件开始 ---")
        print(file_content[:500] + "..." if len(file_content) > 500 else file_content)
        print("--- 文件结束 ---")
        
        # 验证文件大小
        file_size = os.path.getsize(OUTPUT_FILE)
        print(f"[静态更新] 文件大小: {file_size} 字节")
        
        # 统计文件行数
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        print(f"[静态更新] 文件行数: {line_count}")
        
        return 0
    except Exception as e:
        print(f"[静态更新] 写入文件失败: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
