#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版直播源更新脚本
这个脚本只使用Python标准库，避免复杂依赖，适用于环境受限的情况
"""

import os
import sys
import time
from datetime import datetime

# 确保使用UTF-8编码输出
try:
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)
except:
    pass  # 忽略编码设置失败

# 输出文件
OUTPUT_FILE = 'CGQ.TXT'

# 静态直播源数据（避免网络依赖）
STATIC_CHANNELS = {
    "4K央视频道": [
        {"name": "CCTV-4K超高清", "url": "https://tv.cctv.com/live/cctv4k/"},
    ],
    "央视": [
        {"name": "CCTV1", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226346/1.m3u8?"},
        {"name": "CCTV2", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226230/1.m3u8?"},
        {"name": "CCTV3", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226471/1.m3u8?"},
        {"name": "CCTV4", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226335/1.m3u8?"},
        {"name": "CCTV5", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226405/1.m3u8?"},
        {"name": "CCTV5+", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226407/1.m3u8?"},
        {"name": "CCTV6", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226438/1.m3u8?"},
        {"name": "CCTV7", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226411/1.m3u8?"},
        {"name": "CCTV8", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226352/1.m3u8?"},
        {"name": "CCTV9", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226416/1.m3u8?"},
    ],
    "4K超高清频道": [
        {"name": "北京卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.51:5140"},
        {"name": "湖南卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.63:5140"},
        {"name": "浙江卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.65:5140"},
        {"name": "江苏卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.64:5140"},
    ],
    "高清频道": [
        {"name": "湖南卫视HD", "url": "http://example.com/hunan_hd"},
        {"name": "浙江卫视HD", "url": "http://example.com/zhejiang_hd"},
        {"name": "江苏卫视HD", "url": "http://example.com/jiangsu_hd"},
    ]
}

def write_static_channels():
    """将静态频道数据写入文件"""
    try:
        lines = []
        total_channels = 0
        
        # 添加文件头
        lines.append("# 超高清直播源列表")
        lines.append("# 更新时间: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        lines.append("# 此文件由简化版脚本生成，适用于环境受限情况")
        lines.append("")
        
        # 按照优先级排序分类
        category_order = ["4K央视频道", "4K超高清频道", "央视", "高清频道"]
        
        for category in category_order:
            if category in STATIC_CHANNELS:
                # 添加分类标记
                lines.append("{},#genre#".format(category))
                
                # 添加该分类下的所有频道
                for channel in STATIC_CHANNELS[category]:
                    lines.append("{},{}".format(channel["name"], channel["url"]))
                    total_channels += 1
                
                # 分类之间添加空行
                lines.append("")
        
        # 写入文件
        with open(OUTPUT_FILE, 'w') as f:
            f.write('\n'.join(lines))
        
        print("✓ 成功生成 {} 文件".format(OUTPUT_FILE))
        print("总共包含 {} 个频道".format(total_channels))
        print("更新时间: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        return True
    except Exception as e:
        print("✗ 生成文件失败: {}".format(str(e)))
        return False

def main():
    """主函数"""
    print("=== 简化版直播源更新脚本 ===")
    print("此脚本使用静态数据，无需网络连接")
    print("适用于Python环境受限的情况")
    print("")
    
    start_time = time.time()
    
    # 直接使用静态数据生成文件
    if write_static_channels():
        elapsed_time = time.time() - start_time
        print("\n✅ 更新完成！")
        print("总耗时: {:.2f} 秒".format(elapsed_time))
        print("生成文件: {}".format(os.path.abspath(OUTPUT_FILE)))
        return 0
    else:
        print("\n❌ 更新失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
