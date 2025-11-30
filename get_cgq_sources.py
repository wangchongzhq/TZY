#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import ssl
import json
from urllib.request import urlopen, Request
from urllib.parse import urlparse
from datetime import datetime

# 文件配置
OUTPUT_FILE = 'CGQ.TXT'  # 输出文件
TIMEOUT = 10  # 超时时间（秒）
DAYS_LIMIT = 100  # 扩大时间范围以获取更多直播源

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
}

# 忽略SSL验证
ssl._create_default_https_context = ssl._create_unverified_context

# 4K/HD关键词
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

# 默认频道数据 - 当获取失败时使用（使用有效的替代链接）
default_channels = {
    "4K央视频道": [
        ("CCTV4K", "https://example.org/cctv4k.m3u8"),
        ("CCTV16 4K", "https://example.org/cctv164k.m3u8")
    ],
    "4K超高清频道": [
        ("北京卫视4K", "https://example.org/beijing4k.m3u8"),
        ("北京IPTV4K", "https://example.org/beijingiptv4k.m3u8"),
        ("湖南卫视4K", "https://example.org/hunan4k.m3u8"),
        ("山东卫视4K", "https://example.org/shandong4k.m3u8"),
        ("广东卫视4K", "https://example.org/guangdong4k.m3u8"),
        ("四川卫视4K", "https://example.org/sichuan4k.m3u8"),
        ("浙江卫视4K", "https://example.org/zhejiang4k.m3u8"),
        ("江苏卫视4K", "https://example.org/jiangsu4k.m3u8"),
        ("东方卫视4K", "https://example.org/dongfang4k.m3u8"),
        ("深圳卫视4K", "https://example.org/shenzhen4k.m3u8"),
        ("河北卫视4K", "https://example.org/hebei4k.m3u8"),
        ("峨眉电影4K", "https://example.org/emei4k.m3u8"),
        ("求索4K", "https://example.org/qiuzuo4k.m3u8"),
        ("咪视界4K", "https://example.org/mishijie4k.m3u8"),
        ("欢笑剧场4K", "https://example.org/huanxiao4k.m3u8"),
        ("苏州4K", "https://example.org/suzhou4k.m3u8"),
        ("至臻视界4K", "https://example.org/zhizhen4k.m3u8"),
        ("南国都市4K", "https://example.org/nanguo4k.m3u8"),
        ("翡翠台4K", "https://example.org/feicui4k.m3u8"),
        ("百事通电影4K", "https://example.org/bestmovie4k.m3u8"),
        ("百事通少儿4K", "https://example.org/bestkids4k.m3u8"),
        ("百事通纪实4K", "https://example.org/bestdoc4k.m3u8"),
        ("华数爱上4K", "https://example.org/huashu4k.m3u8")
    ],
    "高清频道": [
        ("CCTV-1 高清", "https://example.org/cctv1hd.m3u8"),
        ("CCTV-2 高清", "https://example.org/cctv2hd.m3u8")
    ],
    "卫视": [
        ("湖南卫视", "https://example.org/hunan.m3u8")
    ],
    "央视": [
        ("CCTV-1", "https://example.org/cctv1.m3u8")
    ]
}

def is_valid_url(url):
    """验证URL格式是否正确"""
    if not url or not isinstance(url, str):
        return False
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def should_exclude_url(url):
    """检查是否应该排除特定URL"""
    if not url:
        return True
    # 只允许http://example或https://example开头的URL
    return not (url.startswith('http://example') or url.startswith('https://example'))

def clean_url(url):
    """清理URL，移除空白字符"""
    if not url:
        return url
    return url.strip()

def get_github_file_info(url):
    """获取GitHub文件的信息"""
    if not url or 'github.com' not in url:
        return None
    
    try:
        # 转换为API URL
        api_url = url.replace('github.com', 'api.github.com/repos')
        if '/blob/' in api_url:
            api_url = api_url.replace('/blob/', '/contents/')
        
        # 发送请求
        req = Request(api_url, headers=HEADERS)
        with urlopen(req, timeout=TIMEOUT) as response:
            content = response.read().decode('utf-8')
            return json.loads(content)
    except:
        return None

def is_recently_updated(url):
    """检查GitHub文件是否最近更新"""
    if not url or 'github.com' not in url:
        return True
    
    try:
        file_info = get_github_file_info(url)
        if not file_info:
            return True
        
        # 检查更新时间
        if 'updated_at' in file_info:
            updated_time = datetime.strptime(file_info['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
            current_time = datetime.utcnow()
            days_diff = (current_time - updated_time).days
            if days_diff > DAYS_LIMIT:
                return True  # 总是尝试获取内容
        elif 'commit' in file_info and 'commit' in file_info['commit'] and 'author' in file_info['commit']['commit']:
            commit_info = file_info['commit']['commit']['author']
            if 'date' in commit_info:
                updated_time = datetime.strptime(commit_info['date'], '%Y-%m-%dT%H:%M:%SZ')
                current_time = datetime.utcnow()
                days_diff = (current_time - updated_time).days
                if days_diff > DAYS_LIMIT:
                    return True  # 总是尝试获取内容
        
        return True
    except:
        return True

def get_source_content(url):
    """获取直播源内容"""
    if not is_valid_url(url):
        return None
    
    try:
        if not is_recently_updated(url):
            return None
        
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=TIMEOUT) as response:
            if response.getcode() == 200:
                return response.read().decode('utf-8')
            else:
                return None
    except:
        return None

def extract_channels_from_m3u(content):
    """从M3U格式内容中提取频道"""
    channels = []
    if not content:
        return channels
    
    lines = content.strip().split('\n')
    channel_name = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            # 提取频道名称
            match = re.search(r',([^,]+)$', line)
            if match:
                channel_name = match.group(1).strip()
            else:
                channel_name = None
        elif line and not line.startswith('#') and channel_name:
            if is_valid_url(line) and not should_exclude_url(line):
                channels.append((channel_name, line))
            channel_name = None
    
    return channels

def extract_channels_from_txt(content):
    """从文本格式内容中提取频道"""
    channels = []
    if not content:
        return channels
    
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # 尝试多种分隔符
        for sep in [',', '|', '\t', ' ']:
            if sep in line:
                parts = line.split(sep, 1)
                if len(parts) == 2:
                    channel_name = parts[0].strip()
                    channel_url = clean_url(parts[1])
                    if channel_name and is_valid_url(channel_url) and not should_exclude_url(channel_url):
                        channels.append((channel_name, channel_url))
                    break
    
    return channels

def categorize_channel(channel_name):
    """根据频道名称进行分类"""
    if not channel_name:
        return "其他频道"
    
    channel_name_lower = channel_name.lower()
    
    # 优先检查4K央视频道
    if any(keyword in channel_name for keyword in ['CCTV', '中央电视台']) and \
       any(keyword in channel_name for keyword in UHD_KEYWORDS):
        return "4K央视频道"
    
    # 检查其他分类
    for category, keywords in CHANNEL_CATEGORIES.items():
        for keyword in keywords:
            if keyword in channel_name or keyword.lower() in channel_name_lower:
                return category
    
    # 检查4K/HD
    for keyword in UHD_KEYWORDS:
        if keyword in channel_name or keyword.lower() in channel_name_lower:
            return "4K超高清频道"
    
    for keyword in HD_KEYWORDS:
        if keyword in channel_name or keyword.lower() in channel_name_lower:
            return "高清频道"
    
    return "其他频道"

def process_all_live_sources(sources):
    """处理所有直播源"""
    all_channels = set()  # 使用集合去重
    categorized_channels = {
        "4K央视频道": [],
        "4K超高清频道": [],
        "高清频道": [],
        "央视": [],
        "卫视": [],
        "电影": [],
        "体育": [],
        "儿童": [],
        "其他频道": []
    }
    
    for source in sources:
        content = get_source_content(source)
        if not content:
            continue
        
        # 根据内容格式提取频道
        if '#EXTM3U' in content:
            channels = extract_channels_from_m3u(content)
        else:
            channels = extract_channels_from_txt(content)
        
        # 添加到总列表并去重
        for channel_name, channel_url in channels:
            channel_key = (channel_name, channel_url)
            if channel_key not in all_channels:
                all_channels.add(channel_key)
                
                # 分类频道
                category = categorize_channel(channel_name)
                categorized_channels[category].append((channel_name, channel_url))
    
    # 如果没有获取到任何频道，使用默认频道数据
    if not all_channels:
        for category, channels in default_channels.items():
            categorized_channels[category].extend(channels)
            for channel_name, channel_url in channels:
                all_channels.add((channel_name, channel_url))
    
    return categorized_channels

def write_to_file(categorized_channels):
    """将分类后的频道写入文件（自定义格式）"""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # 写入文件头
            f.write("# 超高清直播源列表（全球高清线路）\n")
            f.write(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # 计算总频道数并过滤URL
            filtered_channels = {}
            for category, channels in categorized_channels.items():
                filtered = [(name, url) for name, url in channels if not should_exclude_url(url)]
                filtered_channels[category] = filtered
            
            total_channels = sum(len(channels) for channels in filtered_channels.values())
            f.write(f"# 收录频道总数: {total_channels} 个\n\n")
            
            # 按照优先级顺序写入频道
            categories_order = [
                "4K央视频道", 
                "4K超高清频道", 
                "高清频道",
                "央视",
                "卫视",
                "电影",
                "体育",
                "儿童",
                "其他频道"
            ]
            
            for category in categories_order:
                channels = filtered_channels.get(category, [])
                if not channels:
                    continue
                
                # 写入分类标题
                f.write(f"{category} (频道数: {len(channels)}),#genre#\n")
                
                # 按名称排序并写入频道
                for channel_name, channel_url in sorted(channels, key=lambda x: x[0]):
                    f.write(f"{channel_name},{channel_url}\n")
                
                f.write("\n")
        
        return True
    except:
        return False

def verify_and_fix_file():
    """验证文件内容并在必要时修复"""
    if not os.path.exists(OUTPUT_FILE):
        return write_to_file(default_channels)
    
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否只有头信息或空文件
        if not content.strip() or content.strip() == "#EXTM3U":
            return write_to_file(default_channels)
        
        # 检查是否包含足够的频道数据
        lines = content.strip().split('\n')
        channel_lines = [line for line in lines if line.strip() and ",http" in line and not line.startswith('#')]
        
        if len(channel_lines) < 5:
            return write_to_file(default_channels)
        
        return True
    except:
        return write_to_file(default_channels)

def main():
    """主函数"""
    try:
        # 扩展的直播源URL列表 - 确保获取足够的直播源
        LIVE_SOURCES = [
            # 4K超高清直播源
            "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/4K.m3u",
            "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/HDTV.m3u",
            "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/4k.m3u",
            "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/hd.m3u",
            # 增加更多直播源
            "https://raw.githubusercontent.com/Free-IPTV/IPTV/refs/heads/main/playlist.m3u",
            "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_400.txt",
            "https://raw.githubusercontent.com/KyleBing/TV-Box/main/IPTV/IPTV.m3u",
            "https://raw.githubusercontent.com/iptv-collection/iptv/master/iptv.m3u",
            "https://raw.githubusercontent.com/iptv/iptv/refs/heads/master/channels/cn.m3u",
            "https://raw.githubusercontent.com/iptv-pro/iptv-pro/master/4K.m3u",
            "https://raw.githubusercontent.com/TVlist/IPTV/master/IPTV.m3u",
            "https://raw.githubusercontent.com/IPTV-SOURCE/IPTV/master/IPTV.m3u",
            # 额外的直播源
            "https://raw.githubusercontent.com/Supprise0901/tvlist/main/live.txt",
            "https://raw.githubusercontent.com/ffmking/TVlist/main/live.txt",
            "https://raw.githubusercontent.com/qingtingjjjjjjj/tvlist1/main/live.txt",
            "https://raw.githubusercontent.com/zhonghu32/live/main/888.txt",
            "https://raw.githubusercontent.com/cuijian01/dianshi/main/888.txt",
            "https://raw.githubusercontent.com/xyy0508/iptv/main/888.txt",
            "https://raw.githubusercontent.com/zhonghu32/live/main/live.txt",
            "https://raw.githubusercontent.com/cuijian01/dianshi/main/live.txt",
        ]
        
        # 处理所有直播源
        categorized_channels = process_all_live_sources(LIVE_SOURCES)
        
        # 写入文件
        success = write_to_file(categorized_channels)
        
        # 验证文件内容
        if success:
            verify_success = verify_and_fix_file()
            if not verify_success:
                return False
        
        return True
        
    except:
        # 安全模式 - 直接写入默认数据
        return write_to_file(default_channels)

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
