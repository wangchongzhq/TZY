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

# 默认频道数据 - 当获取失败时使用
default_channels = {
    "4K央视频道": [
        ("CCTV-4K", "http://example.com/cctv4k.m3u8"),
        ("CCTV-1 4K", "http://example.com/cctv14k.m3u8"),
        ("NHK BS4K", "https://example.com/nhk4k/index.m3u8"),
        ("BS TV Tokyo 4K", "https://vn.utako.moe/bstx4k/index.m3u8")
    ],
    "4K超高清频道": [
        ("4K测试频道", "http://example.com/test4k.m3u8"),
        ("4K电影频道", "http://example.com/4kmovie.m3u8")
    ],
    "高清频道": [
        ("CCTV-1 高清", "http://example.com/cctv1hd.m3u8"),
        ("CCTV-2 高清", "http://example.com/cctv2hd.m3u8"),
        ("湖南卫视高清", "http://example.com/hunanhd.m3u8"),
        ("浙江卫视高清", "http://example.com/zhejianghd.m3u8")
    ],
    "卫视": [
        ("湖南卫视", "http://example.com/hunan.m3u8"),
        ("浙江卫视", "http://example.com/zhejiang.m3u8")
    ],
    "央视": [
        ("CCTV-1", "http://example.com/cctv1.m3u8"),
        ("CCTV-2", "http://example.com/cctv2.m3u8"),
        ("CCTV-3", "http://example.com/cctv3.m3u8")
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
            data = json.loads(content)
            return data
    except Exception as e:
        print(f"获取GitHub文件信息失败: {e}")
        return None

def is_recently_updated(url):
    """检查GitHub文件是否最近更新"""
    if not url or 'github.com' not in url:
        # 非GitHub链接，认为是最近更新的
        return True
    
    try:
        # 获取文件信息
        file_info = get_github_file_info(url)
        if not file_info:
            # 如果获取文件信息失败，仍然尝试获取内容
            print(f"获取文件信息失败，仍然尝试获取内容: {url}")
            return True
        
        # 检查更新时间
        if 'updated_at' in file_info:
            updated_time = datetime.strptime(file_info['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
            current_time = datetime.utcnow()
            days_diff = (current_time - updated_time).days
            if days_diff > DAYS_LIMIT:
                print(f"{url} 超过{DAYS_LIMIT}天未更新，但仍然尝试获取内容")
            return True  # 总是尝试获取内容，扩大直播源范围
        elif 'commit' in file_info and 'commit' in file_info['commit'] and 'author' in file_info['commit']['commit']:
            commit_info = file_info['commit']['commit']['author']
            if 'date' in commit_info:
                updated_time = datetime.strptime(commit_info['date'], '%Y-%m-%dT%H:%M:%SZ')
                current_time = datetime.utcnow()
                days_diff = (current_time - updated_time).days
                if days_diff > DAYS_LIMIT:
                    print(f"{url} 超过{DAYS_LIMIT}天未更新，但仍然尝试获取内容")
            return True  # 总是尝试获取内容，扩大直播源范围
        
        return True  # 总是尝试获取内容，扩大直播源范围
    except Exception as e:
        print(f"检查更新时间失败，仍然尝试获取内容: {e} - {url}")
        return True  # 发生异常时仍然尝试获取内容

def get_source_content(url):
    """获取直播源内容"""
    if not is_valid_url(url):
        print(f"无效的URL: {url}")
        return None
    
    try:
        # 检查是否最近更新
        if not is_recently_updated(url):
            print(f"{url} 不是最近{DAYS_LIMIT}天内更新的，跳过")
            return None
        
        # 发送请求
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=TIMEOUT) as response:
            if response.getcode() == 200:
                content = response.read().decode('utf-8')
                print(f"成功获取 {url}")
                return content
            else:
                print(f"获取失败，状态码: {response.getcode()} - {url}")
                return None
    except Exception as e:
        print(f"获取内容异常: {e} - {url}")
        return None

def extract_channels_from_m3u(content):
    """从M3U格式内容中提取频道"""
    channels = []
    if not content:
        return channels
    
    lines = content.strip().split('\n')
    channel_name = None
    channel_url = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('#EXTINF:'):
            # 提取频道名称
            match = re.search(r',([^,]+)$', line)
            if match:
                channel_name = match.group(1).strip()
            else:
                channel_name = None
        elif line and not line.startswith('#') and channel_name:
            channel_url = line
            if is_valid_url(channel_url):
                channels.append((channel_name, channel_url))
            channel_name = None
            channel_url = None
    
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
                    if channel_name and is_valid_url(channel_url):
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
    
    # 如果没有获取到任何频道，使用默认频道数据
    if not all_channels:
        print("\n警告: 未获取到任何直播源，使用默认频道数据")
        for category, channels in default_channels.items():
            categorized_channels[category].extend(channels)
            for channel_name, channel_url in channels:
                all_channels.add((channel_name, channel_url))
        
        print(f"使用默认频道数据: {sum(len(channels) for channels in default_channels.values())} 个频道")
    
    return categorized_channels

def write_to_file(categorized_channels):
    """将分类后的频道写入文件（自定义格式）"""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # 写入文件头
            f.write("# 超高清直播源列表（全球高清线路）\n")
            f.write(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # 计算总频道数
            total_channels = sum(len(channels) for channels in categorized_channels.values())
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
                channels = categorized_channels.get(category, [])
                if not channels:
                    continue
                
                # 写入分类标题
                f.write(f"{category} (频道数: {len(channels)}),#genre#\n")
                
                # 按名称排序并写入频道
                for channel_name, channel_url in sorted(channels, key=lambda x: x[0]):
                    f.write(f"{channel_name},{channel_url}\n")
                
                f.write("\n")
        
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
        
        return True
    except Exception as e:
        print(f"写入文件失败: {e}")
        return False

def verify_and_fix_file():
    """验证文件内容并在必要时修复"""
    if not os.path.exists(OUTPUT_FILE):
        print(f"文件 {OUTPUT_FILE} 不存在，创建默认文件")
        return write_to_file(default_channels)
    
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n===== 文件验证 =====")
        print(f"文件大小: {len(content)} 字符")
        print(f"文件行数: {len(content.splitlines())}")
        
        # 检查是否只有头信息或空文件
        if not content.strip() or content.strip() == "#EXTM3U":
            print("警告: 文件内容异常，重新写入默认数据")
            return write_to_file(default_channels)
        
        # 检查是否包含足够的频道数据
        lines = content.strip().split('\n')
        channel_lines = [line for line in lines if line.strip() and ",http" in line and not line.startswith('#')]
        
        if len(channel_lines) < 5:
            print(f"警告: 文件中频道数量过少 ({len(channel_lines)}个)，重新写入默认数据")
            return write_to_file(default_channels)
        
        print(f"文件验证通过，包含 {len(channel_lines)} 个频道")
        return True
    except Exception as e:
        print(f"验证文件失败: {e}")
        print("重新写入默认数据")
        return write_to_file(default_channels)

def main():
    """主函数"""
    start_time = time.time()
    
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
        
        print(f"开始处理 {len(LIVE_SOURCES)} 个直播源")
        print(f"筛选条件: 近{DAYS_LIMIT}天内更新的直播源")
        
        # 处理所有直播源
        categorized_channels = process_all_live_sources(LIVE_SOURCES)
        
        # 写入文件
        success = write_to_file(categorized_channels)
        
        # 验证文件内容
        if success:
            verify_success = verify_and_fix_file()
            if not verify_success:
                print("严重错误: 文件验证修复失败")
                return False
        
        end_time = time.time()
        print(f"\n任务完成！总耗时: {end_time - start_time:.2f} 秒")
        return True
        
    except Exception as e:
        print(f"主程序异常: {e}")
        
        # 安全模式 - 直接写入默认数据
        print("\n安全模式: 直接写入默认频道数据")
        if write_to_file(default_channels):
            print("安全模式写入成功")
            return True
        else:
            print("安全模式写入失败")
            return False

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
