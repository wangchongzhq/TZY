#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 极简版直播源更新脚本
# 仅包含基本的文件写入功能

import os
import sys
import time

def main():
    try:
        # 确保输出编码为UTF-8
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
            sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)
        
        output_file = 'CGQ.TXT'
        print(f"正在更新 {output_file}...")
        
        # 构建文件内容
        content = []
        content.append("# 超高清直播源列表")
        content.append(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("# 极简更新工具")
        content.append("")
        
        # 央视分类
        content.append("央视,#genre#")
        content.append("CCTV-1综合,https://raw.githubusercontent.com/Supprise0901/tvlist/main/live.txt")
        content.append("CCTV-2财经,https://raw.githubusercontent.com/ffmking/TVlist/main/live.txt")
        content.append("CCTV-3综艺,https://raw.githubusercontent.com/qingtingjjjjjjj/tvlist1/main/live.txt")
        content.append("CCTV-4中文国际,https://raw.githubusercontent.com/zhonghu32/live/main/888.txt")
        content.append("CCTV-5体育,https://raw.githubusercontent.com/cuijian01/dianshi/main/888.txt")
        content.append("CCTV-6电影,https://raw.githubusercontent.com/xyy0508/iptv/main/888.txt")
        content.append("CCTV-7国防军事,https://raw.githubusercontent.com/zhonghu32/live/main/live.txt")
        content.append("CCTV-8电视剧,https://raw.githubusercontent.com/cuijian01/dianshi/main/live.txt")
        content.append("")
        
        # 4K央视频道
        content.append("4K央视频道,#genre#")
        content.append("CCTV-4K超高清,https://raw.githubusercontent.com/Supprise0901/tvlist/main/live.txt")
        content.append("")
        
        # 新增直播源
        content.append("新增直播源,#genre#")
        content.append("新源1,https://raw.githubusercontent.com/Supprise0901/tvlist/main/live.txt")
        content.append("新源2,https://raw.githubusercontent.com/ffmking/TVlist/main/live.txt")
        content.append("新源3,https://raw.githubusercontent.com/qingtingjjjjjjj/tvlist1/main/live.txt")
        content.append("新源4,https://raw.githubusercontent.com/zhonghu32/live/main/888.txt")
        content.append("新源5,https://raw.githubusercontent.com/cuijian01/dianshi/main/888.txt")
        content.append("新源6,https://raw.githubusercontent.com/xyy0508/iptv/main/888.txt")
        content.append("新源7,https://raw.githubusercontent.com/zhonghu32/live/main/live.txt")
        content.append("新源8,https://raw.githubusercontent.com/cuijian01/dianshi/main/live.txt")
        content.append("")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        print(f"✓ 成功更新 {output_file}")
        print(f"  共 {len(content)} 行数据")
        print(f"  更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return 0
    except Exception as e:
        print(f"✗ 更新失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
