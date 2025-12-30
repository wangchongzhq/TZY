#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析M3U8播放列表的具体内容格式
"""

import requests
import re
from urllib.parse import urlparse, urljoin

def analyze_m3u8_content(url, timeout=10):
    """分析M3U8内容的详细格式"""
    print(f"\n分析URL: {url}")
    print("-" * 80)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        if response.status_code != 200:
            print(f"❌ 无法访问，状态码: {response.status_code}")
            return
        
        content = response.text
        print(f"内容长度: {len(content)} 字符")
        print(f"Content-Type: {response.headers.get('content-type', '未知')}")
        print("\n完整内容:")
        print("=" * 60)
        print(content)
        print("=" * 60)
        
        if not content.startswith('#EXTM3U'):
            print("❌ 非M3U8格式")
            return
        
        lines = content.splitlines()
        print(f"\n分析结果:")
        print(f"总行数: {len(lines)}")
        
        # 分析各种类型的行
        extinf_lines = []
        stream_inf_lines = []
        url_lines = []
        other_lines = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('#EXTINF:'):
                extinf_lines.append((i, line))
            elif line.startswith('#EXT-X-STREAM-INF:'):
                stream_inf_lines.append((i, line))
            elif line.startswith('#'):
                other_lines.append((i, line))
            else:
                url_lines.append((i, line))
        
        print(f"#EXTINF行数: {len(extinf_lines)}")
        for line_num, line in extinf_lines[:3]:  # 只显示前3个
            print(f"  行{line_num}: {line}")
        
        print(f"\n#EXT-X-STREAM-INF行数: {len(stream_inf_lines)}")
        for line_num, line in stream_inf_lines[:3]:  # 只显示前3个
            print(f"  行{line_num}: {line}")
            
            # 提取分辨率信息
            resolution_match = re.search(r'RESOLUTION=(\d+)x(\d+)', line, re.IGNORECASE)
            if resolution_match:
                print(f"    → 找到分辨率: {resolution_match.group(1)}x{resolution_match.group(2)}")
        
        print(f"\nURL行数: {len(url_lines)}")
        for line_num, line in url_lines[:5]:  # 只显示前5个
            print(f"  行{line_num}: {line}")
            
            # 分析URL类型
            if line.startswith('http://') or line.startswith('https://'):
                url_type = "绝对URL"
            elif line.startswith('/'):
                url_type = "根路径URL"
            else:
                url_type = "相对URL"
            print(f"    → {url_type}")
            
        print(f"\n其他注释行数: {len(other_lines)}")
        for line_num, line in other_lines[:3]:  # 只显示前3个
            print(f"  行{line_num}: {line}")
        
        # 检查当前解析逻辑的问题
        print(f"\n当前解析逻辑问题分析:")
        
        # 检查是否包含媒体片段URL
        has_media_urls = any(line.startswith('http://') or line.startswith('https://') or line.startswith('/') for _, line in url_lines)
        print(f"是否包含可识别的媒体URL: {'是' if has_media_urls else '否'}")
        
        if not has_media_urls and len(url_lines) > 0:
            print("⚠ URL行存在但格式异常，可能包含特殊字符或编码问题")
            print("URL行详情:")
            for line_num, line in url_lines:
                print(f"  行{line_num} ({len(line)}字符): '{line}'")
                print(f"    十六进制: {line.encode('utf-8').hex()}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

def main():
    """主函数"""
    # 测试几个典型的URL
    test_urls = [
        "北京卫视4K, http://yp.qqqtv.top/1/api.php?id=%E5%8C%97%E4%BA%AC%E5%8D%AB%E8%A7%864K&auth=666858",
        "CCTV4K, http://btjg.net:809/hls/141/index.m3u8",
        "翡翠台4K, http://cdn6.163189.xyz/163189/fct4k",
        "深圳卫视4K, https://cdn3.163189.xyz/163189/szws4k",
        "CCTV2, http://112.123.206.32:808/hls/2/index.m3u8",
        "CCTV1, http://112.27.235.94:8000/hls/1/index.m3u8",
        "CCTV1, https://www.freetv.top/migu/608807420.m3u8?migutoken=5b04cf0d91179ab2d3d71703f0a8bc3d32dd02f7d8fb55ee70e05c216b8a9d1a73d911fbde798459fb66d94934157c996f8306c0dd37917775f2ed73dcc22cf84b25ca500bff5c636ff48d6344$%E8%AE%A2%E9%98%85%E6%BA%90",
        "CCTV11, http://61.184.46.85:9901/tsfile/live/0011_1.m3u8?key=txiptv&playlive=1&authid=0",
        "CCTV8, http://sh.lnott.top:880/dx08.m3u8",
        "江苏卫视, http://cx.li13313000882.cn:24280/hls/21/index.m3u8",
        "KoreaTV, https://hlive.ktv.go.kr/live/klive_h.stream/chunklist_w667562990.m3u8"
    ]
    
    print("开始分析M3U8播放列表格式...")
    
    for i, test_line in enumerate(test_urls, 1):
        print(f"\n\n{'='*20} URL {i} {'='*20}")
        
        # 提取URL
        if ',' in test_line:
            channel_name, url = test_line.split(',', 1)
            channel_name = channel_name.strip()
            url = url.strip()
            print(f"频道: {channel_name}")
        else:
            url = test_line.strip()
        
        analyze_m3u8_content(url)

if __name__ == "__main__":
    main()