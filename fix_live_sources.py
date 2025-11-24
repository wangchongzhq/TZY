#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版本直播源获取脚本
专门解决新增直播源不显示的问题
"""

import os
import re
import time
import sys
from urllib.parse import urlparse
from urllib.request import urlopen, Request
import ssl

# 确保UTF-8编码
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

print("开始执行修复版直播源获取脚本...")

# 配置参数
OUTPUT_FILE = 'CGQ.TXT'
TIMEOUT = 10  # 秒，降低超时时间提高效率

# 请求头，模拟浏览器行为
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
}

# 禁用SSL验证
ssl._create_default_https_context = ssl._create_unverified_context

# 直播源URL列表 - 包含新增的直播源
LIVE_SOURCES = [
    # 可靠的直播源
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "https://raw.githubusercontent.com/MeooPlayer/China-M3U-List/main/China_UHD.m3u",
    "https://raw.githubusercontent.com/MeooPlayer/China-M3U-List/main/China_HD.m3u",
    # 其他直播源
    "https://ghcy.eu.org/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt",
    "https://ghfast.top/raw.githubusercontent.com/ffmking/tv1/main/888.txt",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/kimwang1978/collect-txt/refs/heads/main/bbxx.txt",
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

# 超高清关键词
UHD_KEYWORDS = ['4K', '4k', '超高清', '2160', '2160p', '8K', '8k']
HD_KEYWORDS = ['HD', '1080p', '高清']

# 频道分类
CHANNEL_CATEGORIES = {
    "央视": ['CCTV', '中央电视台'],
    "卫视": ['卫视', '湖南卫视', '浙江卫视', '江苏卫视', '东方卫视', '北京卫视', '广东卫视'],
    "电影": ['电影', 'CHC', 'Movie', 'Film'],
    "体育": ['体育', '足球', '篮球', 'NBA', 'CCTV5', 'sports'],
    "儿童": ['少儿', '卡通', '动画', 'Cartoon', 'Kids'],
    "4K央视频道": ['CCTV', '4K'],
    "4K超高清频道": ['4K超高清', '4K专区'],
    "高清频道": ['HD', '1080p'],
}

def is_valid_url(url):
    """验证URL是否有效，更宽松的验证策略"""
    try:
        result = urlparse(url)
        return bool(result.scheme) and bool(result.netloc)
    except:
        return False

def clean_url(url):
    """清理URL中的异常格式"""
    # 处理重复协议前缀
    if 'https://https://' in url:
        url = url.replace('https://https://', 'https://')
    elif 'http://https://' in url:
        url = url.replace('http://https://', 'https://')
    elif 'https://http://' in url:
        url = url.replace('https://http://', 'http://')
    elif 'http://http://' in url:
        url = url.replace('http://http://', 'http://')
    
    # 去除首尾空白字符
    url = url.strip()
    return url

def get_source_content(url):
    """获取直播源内容，增加错误处理和重试机制"""
    print(f"正在获取直播源: {url}")
    
    # 清理URL
    url = clean_url(url)
    
    for retry in range(2):  # 最多重试1次
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=TIMEOUT) as response:
                content = response.read()
                print(f"  成功获取，大小: {len(content)} 字节")
                
                # 尝试解码
                try:
                    return content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        return content.decode('latin-1')
                    except:
                        print(f"  解码失败，跳过此源")
                        return None
        except Exception as e:
            print(f"  获取失败 (尝试 {retry+1}/2): {str(e)}")
            if retry == 0:
                print("  正在重试...")
                time.sleep(1)
    
    return None

def is_uhd_content(name, url):
    """判断是否为超高清内容"""
    combined = (name + ' ' + url).lower()
    for keyword in UHD_KEYWORDS:
        if keyword.lower() in combined:
            return True
    return False

def extract_channels_from_m3u(content):
    """从M3U格式内容提取频道"""
    channels = []
    if not content:
        return channels
    
    lines = content.split('\n')
    extinf_line = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            extinf_line = line
        elif line.startswith(('http://', 'https://', 'udp://', 'rtmp://', 'rtsp://')) and extinf_line:
            # 提取频道名称
            try:
                channel_name = extinf_line.split(',')[-1].strip()
                url = line
                is_uhd = is_uhd_content(channel_name, url)
                channels.append((channel_name, url, is_uhd))
            except:
                pass
            extinf_line = None
    
    return channels

def extract_channels_from_txt(content):
    """从简单文本格式提取频道"""
    channels = []
    if not content:
        return channels
    
    lines = content.split('\n')
    
    # 尝试多种格式：name\nurl 或 name,url
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('#'):
            i += 1
            continue
        
        # 尝试name,url格式
        if ',' in line and line.count(',') == 1:
            try:
                name, url = line.split(',', 1)
                name = name.strip()
                url = url.strip()
                if name and is_valid_url(url):
                    is_uhd = is_uhd_content(name, url)
                    channels.append((name, url, is_uhd))
            except:
                pass
        # 尝试name\nurl格式
        elif i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith(('http://', 'https://', 'udp://', 'rtmp://', 'rtsp://')):
                name = line
                url = next_line
                if name and is_valid_url(url):
                    is_uhd = is_uhd_content(name, url)
                    channels.append((name, url, is_uhd))
                i += 1
        
        i += 1
    
    return channels

def categorize_channel(channel_name):
    """对频道进行分类"""
    for category, keywords in CHANNEL_CATEGORIES.items():
        for keyword in keywords:
            if keyword in channel_name:
                return category
    return "其他频道"

def process_all_live_sources():
    """处理所有直播源"""
    all_channels = []
    
    print(f"\n开始处理 {len(LIVE_SOURCES)} 个直播源...")
    
    for i, url in enumerate(LIVE_SOURCES, 1):
        print(f"\n[{i}/{len(LIVE_SOURCES)}] 处理: {url}")
        
        if not is_valid_url(url):
            print(f"  URL格式无效，跳过")
            continue
        
        content = get_source_content(url)
        if not content:
            print(f"  未获取到内容，跳过")
            continue
        
        # 尝试不同格式提取频道
        channels = []
        if '#EXTM3U' in content:
            print(f"  检测到M3U格式")
            channels = extract_channels_from_m3u(content)
        else:
            print(f"  检测到文本格式")
            channels = extract_channels_from_txt(content)
        
        if channels:
            print(f"  成功提取 {len(channels)} 个频道")
            all_channels.extend(channels)
        else:
            print(f"  未提取到任何有效频道")
    
    print(f"\n总共获取到 {len(all_channels)} 个原始频道")
    
    # 去重 - 使用更宽松的策略，保留不同URL的同一频道
    print("\n开始去重处理...")
    unique_channels = {}
    for name, url, is_uhd in all_channels:
        # 使用名称和URL的组合作为去重键
        key = f"{name}|{url}"
        if key not in unique_channels:
            unique_channels[key] = (name, url, is_uhd)
    
    all_channels = list(unique_channels.values())
    print(f"去重后剩余 {len(all_channels)} 个唯一频道")
    
    # 按分类组织频道
    categorized = {}
    for name, url, is_uhd in all_channels:
        cat = categorize_channel(name)
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append((name, url, is_uhd))
    
    print(f"\n频道分类结果:")
    for cat, chans in categorized.items():
        print(f"  {cat}: {len(chans)} 个频道")
    
    return categorized

def write_to_file(categorized_channels):
    """将频道写入CGQ.TXT文件"""
    try:
        lines = []
        
        # 文件头
        lines.append(f"# 超高清直播源列表")
        lines.append(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"# 共包含 {sum(len(chans) for chans in categorized_channels.values())} 个频道")
        lines.append("")
        
        # 分类排序优先级
        category_order = ["4K央视频道", "4K超高清频道", "高清频道", "央视", "卫视", "体育", "电影", "儿童", "其他频道"]
        
        # 写入每个分类
        for category in category_order:
            if category in categorized_channels:
                # 添加分类标记
                lines.append(f"{category},#genre#")
                
                # 排序频道：UHD优先，然后按名称排序
                channels = sorted(categorized_channels[category], key=lambda x: (not x[2], x[0]))
                
                for name, url, is_uhd in channels:
                    if is_valid_url(url):
                        lines.append(f"{name},{url}")
                
                # 分类之间空行
                lines.append("")
        
        # 写入文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"\n✓ 成功写入 {OUTPUT_FILE}")
        print(f"  共 {len(lines)} 行数据")
        return True
    except Exception as e:
        print(f"\n✗ 写入文件失败: {str(e)}")
        return False

def main():
    """主函数"""
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")
    
    start_time = time.time()
    
    try:
        # 处理所有直播源
        categorized_channels = process_all_live_sources()
        
        # 如果没有获取到频道，提供一些默认频道
        if not categorized_channels:
            print("\n警告: 未能从网络获取到直播源数据")
            categorized_channels = {
                "4K央视频道": [("CCTV-4K超高清", "https://tv.cctv.com/live/cctv4k/", True)],
                "高清频道": [
                    ("CCTV-1综合", "https://tv.cctv.com/live/cctv1/", False),
                    ("CCTV-2财经", "https://tv.cctv.com/live/cctv2/", False),
                ]
            }
        
        # 写入文件
        if write_to_file(categorized_channels):
            elapsed = time.time() - start_time
            print(f"\n🎉 直播源更新完成！")
            print(f"总耗时: {elapsed:.2f} 秒")
            return 0
        else:
            return 1
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        return 130
    except Exception as e:
        print(f"\n程序错误: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        import traceback
        print("详细错误堆栈:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
