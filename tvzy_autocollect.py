#!/usr/bin/env python3
# tvzy_autocollect.py

import requests
import re
import json
from datetime import datetime
import time
import os
import random
from urllib.parse import urlparse

class TVSourceCollector:
    def __init__(self):
        self.sources = []
        self.categories = {
            "4K": [],
            "央视": [],
            "卫视": [], 
            "港澳台": [],
            "影视剧": [],
            "音乐": [],
            "体育": []
        }
        
        # 真实数据源列表
        self.data_sources = [
            # GitHub上的直播源
            "https://raw.githubusercontent.com/iptv-org/iptv/master/channels/cn.m3u",
            "https://raw.githubusercontent.com/iptv-org/iptv/master/channels/hk.m3u",
            "https://raw.githubusercontent.com/iptv-org/iptv/master/channels/tw.m3u",
            "https://raw.githubusercontent.com/Free-IPTV/Countries/master/China.m3u",
            "https://raw.githubusercontent.com/EvilCaster/iptv/master/cleaned_iptv.m3u",
            "http://106.53.99.30/2025.txt",
            "http://tv.html-5.me/i/9390107.txt",
            "https://ghcy.eu.org/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt",
            "https://ghfast.top/raw.githubusercontent.com/ffmking/tv1/main/888.txt",
            "https://ghfast.top/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt",
            
            # 其他直播源
            "https://mirror.ghproxy.com/https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u",
            "https://fastly.jsdelivr.net/gh/iptv-org/iptv@master/channels/cn.m3u",
            "https://ghproxy.com/https://raw.githubusercontent.com/iptv-org/iptv/master/channels/cn.m3u",
            
            # 备份源
            "https://mirror.ghproxy.com/https://raw.githubusercontent.com/guptaharsh2024/iptv/main/iptv.m3u",
            "https://raw.githubusercontent.com/frank007886/TVBox/main/live.txt",
        ]
        
    def fetch_all_sources(self):
        """
        从多个数据源获取直播源
        """
        print(f"开始从 {len(self.data_sources)} 个数据源收集直播源...")
        
        for source_url in self.data_sources:
            try:
                print(f"正在获取源: {source_url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(source_url, timeout=15, headers=headers)
                if response.status_code == 200:
                    content = response.text
                    print(f"获取成功，内容长度: {len(content)} 字符")
                    self.parse_content(content, source_url)
                else:
                    print(f"获取源失败，状态码: {response.status_code}")
                time.sleep(2)  # 避免请求过于频繁
            except Exception as e:
                print(f"获取源 {source_url} 失败: {e}")
                continue
    
    def parse_content(self, content, source_url):
        """
        解析内容，支持多种格式
        """
        lines = content.split('\n')
        current_channel = {}
        format_detected = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # 检测M3U格式
            if line.startswith('#EXTM3U'):
                format_detected = True
                continue
                
            # 解析EXTINF行
            if line.startswith('#EXTINF:'):
                current_channel = self.parse_extinf_line(line)
                current_channel['source'] = source_url
                continue
                
            # 如果是URL行且前面有EXTINF
            if line.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
                if current_channel:
                    current_channel['url'] = line
                    if self.check_quality(current_channel):
                        self.sources.append(current_channel.copy())
                    current_channel = {}
                else:
                    # 如果没有EXTINF，尝试从URL推断频道信息
                    self.parse_url_only(line, source_url)
                continue
                
            # 尝试解析文本格式：频道名称,URL
            if ',' in line and any(proto in line for proto in ['http://', 'https://', 'rtmp://']):
                parts = line.split(',', 1)
                if len(parts) == 2 and parts[1].startswith(('http://', 'https://', 'rtmp://')):
                    channel_name = parts[0].strip()
                    url = parts[1].strip()
                    if self.is_valid_url(url):
                        channel = {
                            'channel_name': channel_name,
                            'url': url,
                            'source': source_url,
                            'quality': 'unknown'
                        }
                        if self.check_quality(channel):
                            self.sources.append(channel)
        
        if not format_detected and len(self.sources) == 0:
            print(f"警告: 无法识别 {source_url} 的格式")
    
    def parse_extinf_line(self, line):
        """
        解析EXTINF行
        """
        channel = {}
        
        # 提取tvg-name
        tvg_name_match = re.search(r'tvg-name="([^"]*)"', line)
        if tvg_name_match:
            channel['tvg_name'] = tvg_name_match.group(1)
        else:
            # 如果没有tvg-name，尝试从其他地方提取
            tvg_name_match = re.search(r'tvg-id="([^"]*)"', line)
            if tvg_name_match:
                channel['tvg_name'] = tvg_name_match.group(1)
        
        # 提取group-title
        group_match = re.search(r'group-title="([^"]*)"', line)
        if group_match:
            channel['group_title'] = group_match.group(1)
        
        # 提取频道名称（最后一个逗号后的内容）
        name_match = re.search(r',([^,]*)$', line)
        if name_match:
            channel['channel_name'] = name_match.group(1).strip()
        else:
            # 如果没有逗号，尝试其他解析方式
            channel['channel_name'] = line
        
        return channel
    
    def parse_url_only(self, url, source_url):
        """
        解析只有URL没有频道信息的情况
        """
        if self.is_valid_url(url):
            # 从URL推断频道名称
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            path = parsed_url.path
            
            # 尝试从路径中提取频道信息
            channel_name = "未知频道"
            if '/cctv' in path.lower():
                channel_name = "CCTV频道"
            elif '/tv' in path.lower():
                channel_name = "电视频道"
            elif 'live' in path.lower():
                channel_name = "直播频道"
                
            channel = {
                'channel_name': f"{channel_name} ({domain})",
                'url': url,
                'source': source_url,
                'quality': 'unknown'
            }
            if self.check_quality(channel):
                self.sources.append(channel)
    
    def is_valid_url(self, url):
        """
        检查URL是否有效
        """
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False
    
    def check_quality(self, channel):
        """
        检查频道清晰度是否符合要求
        """
        name = channel['channel_name'].lower()
        
        # 基于名称的简单过滤
        if '4k' in name or 'uhd' in name or '超高清' in name:
            channel['quality'] = '4K'
            return True
        elif '1080' in name or 'fhd' in name:
            channel['quality'] = '1080p'
            return True
        elif '高清' in name or 'hd' in name:
            channel['quality'] = '720p'
            return True
        elif 'test' in name or '演示' in name or 'sample' in name:
            return False  # 过滤测试频道
        
        # 如果没有质量信息，默认接受（后面会进一步过滤）
        channel['quality'] = 'unknown'
        return True
    
    def categorize_channels(self):
        """
        将频道按规则分类
        """
        for channel in self.sources:
            name = channel['channel_name'].lower()
            
            # 分类逻辑
            if '4k' in name or 'uhd' in name or '超高清' in name:
                self.categories["4K"].append(channel)
            elif 'cctv' in name or '央视' in name or '中央' in name or 'cctv' in channel.get('tvg_name', '').lower():
                self.categories["央视"].append(channel)
            elif '卫视' in name or '卫视' in channel.get('group_title', '').lower():
                self.categories["卫视"].append(channel)
            elif any(keyword in name for keyword in ['凤凰', '翡翠', 'tvb', '澳亚', '港澳', '香港', '澳门', '台湾']):
                self.categories["港澳台"].append(channel)
            elif any(keyword in name for keyword in ['电影', '影院', '剧场', '影视', 'movie']):
                self.categories["影视剧"].append(channel)
            elif any(keyword in name for keyword in ['音乐', 'mtv', 'music', '演唱会']):
                self.categories["音乐"].append(channel)
            elif any(keyword in name for keyword in ['体育', 'sports', 'cctv5', '运动', 'nba', '足球', '篮球']):
                self.categories["体育"].append(channel)
            else:
                # 如果无法分类，根据group_title尝试分类
                group = channel.get('group_title', '').lower()
                if 'cctv' in group or '央视' in group:
                    self.categories["央视"].append(channel)
                elif '卫视' in group:
                    self.categories["卫视"].append(channel)
                elif any(keyword in group for keyword in ['香港', '澳门', '台湾']):
                    self.categories["港澳台"].append(channel)
                elif any(keyword in group for keyword in ['电影', '影视']):
                    self.categories["影视剧"].append(channel)
                elif '音乐' in group:
                    self.categories["音乐"].append(channel)
                elif '体育' in group:
                    self.categories["体育"].append(channel)
    
    def filter_quality_channels(self):
        """
        过滤出高质量频道
        """
        quality_sources = []
        for channel in self.sources:
            # 优先选择已知清晰度的频道
            if channel['quality'] in ['4K', '1080p', '720p']:
                quality_sources.append(channel)
        
        # 如果高质量频道不够，添加一些未知质量的频道
        if len(quality_sources) < 100:
            unknown_quality = [ch for ch in self.sources if ch['quality'] == 'unknown']
            # 随机选择一些未知质量的频道（但确保总数不超过限制）
            additional = min(len(unknown_quality), 200 - len(quality_sources))
            quality_sources.extend(unknown_quality[:additional])
        
        self.sources = quality_sources
    
    def limit_channels_per_group(self):
        """
        限制每个分组的频道数量
        """
        for category, channels in self.categories.items():
            if not channels:
                print(f"警告: {category} 分组没有频道")
                continue
                
            # 去重：基于URL去除重复频道
            unique_channels = {}
            for channel in channels:
                url = channel['url']
                if url not in unique_channels:
                    unique_channels[url] = channel
                else:
                    # 如果已有相同URL，选择质量更好的
                    existing = unique_channels[url]
                    if self.get_quality_score(channel) > self.get_quality_score(existing):
                        unique_channels[url] = channel
            
            unique_channel_list = list(unique_channels.values())
            
            # 按质量排序
            unique_channel_list.sort(key=lambda x: self.get_quality_score(x), reverse=True)
            
            # 限制数量：最少10个，最多90个
            if len(unique_channel_list) < 10:
                print(f"警告: {category} 分组频道数不足10个，当前为 {len(unique_channel_list)} 个")
            elif len(unique_channel_list) > 90:
                unique_channel_list = unique_channel_list[:90]
            
            self.categories[category] = unique_channel_list
    
    def get_quality_score(self, channel):
        """
        获取频道质量评分
        """
        quality_scores = {
            '4K': 4,
            '1080p': 3,
            '720p': 2,
            'unknown': 1
        }
        return quality_scores.get(channel['quality'], 0)
    
    def generate_output_file(self):
        """
        生成最终的输出文件
        """
        with open('tzyauto.txt', 'w', encoding='utf-8') as f:
            f.write("# 自动生成的直播源文件\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# 分组格式: 频道名称,频道URL,#genre#\n\n")
            
            # 按指定顺序输出分组
            category_order = ["4K", "央视", "卫视", "港澳台", "影视剧", "音乐", "体育"]
            
            for category in category_order:
                channels = self.categories.get(category, [])
                if channels:
                    f.write(f"\n# {category}频道,#genre#\n")
                    for channel in channels:
                        f.write(f"{channel['channel_name']},{channel['url']}\n")
        
        print(f"文件生成完成! 共处理 {len(self.sources)} 个频道")

def main():
    collector = TVSourceCollector()
    print("开始收集直播源...")
    collector.fetch_all_sources()
    print(f"初步收集到 {len(collector.sources)} 个频道")
    
    print("过滤高质量频道...")
    collector.filter_quality_channels()
    print(f"过滤后剩余 {len(collector.sources)} 个频道")
    
    print("开始分类频道...")
    collector.categorize_channels()
    
    print("限制各分组频道数量...")
    collector.limit_channels_per_group()
    
    print("生成输出文件...")
    collector.generate_output_file()
    
    # 输出统计信息
    print("\n=== 统计信息 ===")
    total_channels = 0
    for category, channels in collector.categories.items():
        print(f"{category}: {len(channels)} 个频道")
        total_channels += len(channels)
    
    # 质量统计
    quality_stats = {}
    for channel in collector.sources:
        quality = channel['quality']
        quality_stats[quality] = quality_stats.get(quality, 0) + 1
    
    print(f"\n=== 质量统计 ===")
    for quality, count in quality_stats.items():
        print(f"{quality}: {count} 个频道")
    
    print(f"\n总计: {total_channels} 个频道")

if __name__ == "__main__":
    main()
