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
from datetime import datetime, timedelta

# 设置标准输出为UTF-8编码
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

print("开始执行直播源获取脚本...")

# 配置参数
OUTPUT_FILE = 'CGQ.TXT'
TIMEOUT = 10  # 秒，降低超时时间提高效率
DAYS_LIMIT = 20  # 只获取近20天有更新的直播源

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

def is_valid_url(url):
    """检查URL是否有效"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def clean_url(url):
    """清理URL，去除空白字符"""
    return url.strip()

def get_github_file_info(url):
    """从GitHub URL获取API信息，用于检查文件更新时间"""
    try:
        # 提取GitHub仓库信息
        pattern = r'https://raw.githubusercontent.com/([^/]+)/([^/]+)/([^/]+)/(.+)'  
        match = re.match(pattern, url)
        if not match:
            return None
        
        username, repo, branch, file_path = match.groups()
        
        # 构建API URL
        api_url = f"https://api.github.com/repos/{username}/{repo}/commits?path={file_path}&per_page=1"
        
        # 发送请求
        req = Request(api_url, headers=HEADERS)
        with urlopen(req, timeout=TIMEOUT) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data:
                    commit_date = data[0]['commit']['committer']['date']
                    return {
                        'updated_at': commit_date,
                        'username': username,
                        'repo': repo,
                        'file_path': file_path
                    }
    except Exception as e:
        # print(f"获取GitHub文件信息失败: {e}")
        pass
    return None

def is_recently_updated(url):
    """检查URL是否在近20天内更新过"""
    # 如果不是GitHub URL，我们无法检查更新时间，默认认为是有效的
    if "github.com" not in url and "raw.githubusercontent.com" not in url:
        return True
    
    # 对于GitHub URL，检查更新时间
    file_info = get_github_file_info(url)
    if not file_info:
        return True  # 如果获取不到信息，默认认为是有效的
    
    try:
        # 解析更新时间
        updated_at = datetime.strptime(file_info['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
        
        # 计算是否在DAYS_LIMIT天内
        time_diff = datetime.utcnow() - updated_at
        return time_diff <= timedelta(days=DAYS_LIMIT)
    except Exception as e:
        # print(f"解析更新时间失败: {e}")
        return True

def get_source_content(url):
    """获取直播源内容，支持重试"""
    max_retries = 3
    for retry in range(max_retries):
        try:
            url = clean_url(url)
            if not is_valid_url(url):
                print(f"无效的URL: {url}")
                return None
            
            # 检查是否在近20天内更新
            if not is_recently_updated(url):
                print(f"直播源 {url} 超过20天未更新，跳过")
                return None
            
            print(f"正在获取: {url}")
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=TIMEOUT) as response:
                if response.status == 200:
                    return response.read().decode('utf-8', errors='ignore')
                else:
                    print(f"获取失败，状态码: {response.status}")
        except Exception as e:
            print(f"获取直播源失败 (尝试 {retry + 1}/{max_retries}): {e}")
            if retry < max_retries - 1:
                time.sleep(1)
    return None

def is_uhd_content(name, url):
    """检查是否为4K内容"""
    content = f"{name} {url}".lower()
    for keyword in UHD_KEYWORDS:
        if keyword.lower() in content:
            return True
    return False

def extract_channels_from_m3u(content):
    """从M3U格式内容中提取频道"""
    channels = []
    lines = content.splitlines()
    
    for i, line in enumerate(lines):
        if line.startswith('#EXTINF:'):
            # 提取频道名称
            name_match = re.search(r'tvg-name="([^"]+)"|tvg-title="([^"]+)"|,(.+)', line)
            if name_match:
                channel_name = name_match.group(1) or name_match.group(2) or name_match.group(3)
                if channel_name:
                    channel_name = channel_name.strip()
                    # 下一行应该是URL
                    if i + 1 < len(lines) and not lines[i + 1].startswith('#'):
                        channel_url = lines[i + 1].strip()
                        if is_valid_url(channel_url):
                            channels.append((channel_name, channel_url))
    
    return channels

def extract_channels_from_txt(content):
    """从TXT格式内容中提取频道"""
    channels = []
    lines = content.splitlines()
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # 支持多种格式: 频道名,URL 或 URL 频道名
        if ',' in line:
            parts = line.split(',', 1)
            if is_valid_url(parts[0]):
                # URL,频道名
                channel_url = parts[0].strip()
                channel_name = parts[1].strip()
            else:
                # 频道名,URL
                channel_name = parts[0].strip()
                channel_url = parts[1].strip()
        else:
            # 只包含URL，使用URL作为名称
            channel_url = line
            channel_name = os.path.basename(urlparse(channel_url).path).split('.')[0]
        
        if is_valid_url(channel_url):
            channels.append((channel_name, channel_url))
    
    return channels

def categorize_channel(channel_name):
    """根据频道名称进行分类"""
    channel_name_lower = channel_name.lower()
    
    for category, keywords in CHANNEL_CATEGORIES.items():
        for keyword in keywords:
            if keyword in channel_name or keyword.lower() in channel_name_lower:
                return category
    
    # 检查4K/HD
    for keyword in UHD_KEYWORDS:
        if keyword in channel_name or keyword.lower() in channel_name_lower:
            if 'CCTV' in channel_name:
                return "4K央视频道"
            return "4K超高清频道"
    
    for keyword in HD_KEYWORDS:
        if keyword in channel_name or keyword.lower() in channel_name_lower:
            return "高清频道"
    
    return "其他频道"

def process_all_live_sources(sources):
    """处理所有直播源"""
    all_channels = set()  # 使用集合去重
    categorized_channels = {}
    
    for category in list(CHANNEL_CATEGORIES.keys()) + ["其他频道"]:
        categorized_channels[category] = []
    
    for source in sources:
        content = get_source_content(source)
        if not content:
            continue
        
        # 根据内容格式提取频道
        if '#EXTM3U' in content:
            channels = extract_channels_from_m3u(content)
        else:
            channels = extract_channels_from_txt(content)
        
        print(f"从 {source} 提取到 {len(channels)} 个频道")
        
        # 添加到总列表并去重
        for channel_name, channel_url in channels:
            channel_key = (channel_name, channel_url)
            if channel_key not in all_channels:
                all_channels.add(channel_key)
                
                # 分类频道
                category = categorize_channel(channel_name)
                categorized_channels[category].append((channel_name, channel_url))
    
    print(f"\n总计获取到 {len(all_channels)} 个直播频道")
    return categorized_channels

def write_to_file(categorized_channels):
    """将分类后的频道写入文件"""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n\n")
            
            for category, channels in categorized_channels.items():
                if not channels:
                    continue
                
                # 写入分类标题
                f.write(f"# 频道分类: {category}\n")
                f.write(f"# 频道数量: {len(channels)}\n\n")
                
                # 按名称排序并写入频道
                for channel_name, channel_url in sorted(channels, key=lambda x: x[0]):
                    f.write(f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"{category}\",{channel_name}\n")
                    f.write(f"{channel_url}\n\n")
        
        print(f"\n直播源已成功写入 {OUTPUT_FILE}")
        print(f"文件大小: {os.path.getsize(OUTPUT_FILE)} 字节")
        
        # 显示各分类频道数量
        print("\n各分类频道数量:")
        total = 0
        for category, channels in categorized_channels.items():
            if channels:
                print(f"{category}: {len(channels)} 个频道")
                total += len(channels)
        print(f"总计: {total} 个频道")
        
    except Exception as e:
        print(f"写入文件失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    start_time = time.time()
    
    # 直播源URL列表
    LIVE_SOURCES = [
        # 4K超高清直播源
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/4K.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/HDTV.m3u",
        # 添加你的新直播源URL到这里
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_400.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_410.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_420.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_430.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_440.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_450.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_460.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_470.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_480.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_490.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_500.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_510.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_520.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_530.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_540.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_550.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_560.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_570.txt",
    ]
    
    print(f"开始处理 {len(LIVE_SOURCES)} 个直播源")
    print(f"筛选条件: 近{DAYS_LIMIT}天内更新的直播源")
    
    # 处理所有直播源
    categorized_channels = process_all_live_sources(LIVE_SOURCES)
    
    # 写入文件
    success = write_to_file(categorized_channels)
    
    end_time = time.time()
    print(f"\n脚本执行完成，耗时: {end_time - start_time:.2f} 秒")
    
    return 0 if success else 1

# 主函数调用
if __name__ == "__main__":
    sys.exit(main())
