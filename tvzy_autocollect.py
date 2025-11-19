#!/usr/bin/env python3
# tvzy_autocollect.py

import requests
import re
import json
from datetime import datetime
import time
import os
import random

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
        
        # 示例数据源 - 需要替换为真实可用的源
        self.data_sources = [
            # 这里添加真实的直播源URL
            # 示例格式:
            #"http://106.53.99.30/2025.txt",
            #"http://tv.html-5.me/i/9390107.txt",
            #"https://ghcy.eu.org/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt",

            
           ]
        
    def fetch_all_sources(self):
        """
        从多个数据源获取直播源
        """
        if not self.data_sources:
            print("警告：没有配置数据源，使用示例数据")
            self.generate_sample_data()
            return
            
        for source_url in self.data_sources:
            try:
                print(f"正在获取源: {source_url}")
                response = requests.get(source_url, timeout=10)
                if response.status_code == 200:
                    self.parse_m3u_content(response.text, source_url)
                else:
                    print(f"获取源失败，状态码: {response.status_code}")
                time.sleep(1)  # 避免请求过于频繁
            except Exception as e:
                print(f"获取源 {source_url} 失败: {e}")
                continue
    
    def generate_sample_data(self):
        """
        生成示例数据用于测试
        """
        sample_channels = [
            # 4K频道
            {"name": "CCTV-4K 超高清", "url": "http://example.com/cctv4k.m3u8", "group": "4K"},
            {"name": "北京卫视 4K", "url": "http://example.com/beijing4k.m3u8", "group": "4K"},
            
            # 央视频道
            {"name": "CCTV-1 综合", "url": "http://example.com/cctv1.m3u8", "group": "央视"},
            {"name": "CCTV-2 财经", "url": "http://example.com/cctv2.m3u8", "group": "央视"},
            {"name": "CCTV-5 体育", "url": "http://example.com/cctv5.m3u8", "group": "央视"},
            {"name": "CCTV-6 电影", "url": "http://example.com/cctv6.m3u8", "group": "央视"},
            {"name": "CCTV-8 电视剧", "url": "http://example.com/cctv8.m3u8", "group": "央视"},
            {"name": "CCTV-13 新闻", "url": "http://example.com/cctv13.m3u8", "group": "央视"},
            
            # 卫视
            {"name": "湖南卫视", "url": "http://example.com/hunan.m3u8", "group": "卫视"},
            {"name": "浙江卫视", "url": "http://example.com/zhejiang.m3u8", "group": "卫视"},
            {"name": "江苏卫视", "url": "http://example.com/jiangsu.m3u8", "group": "卫视"},
            {"name": "东方卫视", "url": "http://example.com/dongfang.m3u8", "group": "卫视"},
            
            # 港澳台
            {"name": "凤凰中文台", "url": "http://example.com/fenghuang.m3u8", "group": "港澳台"},
            {"name": "TVB翡翠台", "url": "http://example.com/tvb.m3u8", "group": "港澳台"},
            {"name": "澳亚卫视", "url": "http://example.com/aya.m3u8", "group": "港澳台"},
            
            # 影视剧
            {"name": "星空卫视", "url": "http://example.com/xingkong.m3u8", "group": "影视剧"},
            {"name": "华语电影", "url": "http://example.com/huayu.m3u8", "group": "影视剧"},
            
            # 音乐
            {"name": "MTV音乐", "url": "http://example.com/mtv.m3u8", "group": "音乐"},
            {"name": "音乐台", "url": "http://example.com/music.m3u8", "group": "音乐"},
            
            # 体育
            {"name": "广东体育", "url": "http://example.com/guangdong_sports.m3u8", "group": "体育"},
            {"name": "NBA TV", "url": "http://example.com/nba.m3u8", "group": "体育"},
        ]
        
        for channel in sample_channels:
            self.sources.append({
                'channel_name': channel["name"],
                'url': channel["url"],
                'group_title': channel["group"],
                'quality': '1080p'
            })
    
    def parse_m3u_content(self, content, source_url):
        """
        解析M3U格式内容，提取频道信息
        """
        lines = content.split('\n')
        current_channel = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                # 解析频道信息
                current_channel = self.parse_extinf_line(line)
                current_channel['source'] = source_url
            elif line.startswith('http'):
                if current_channel and 'url' not in current_channel:
                    current_channel['url'] = line
                    if self.check_quality(current_channel):
                        self.sources.append(current_channel.copy())
                    current_channel = {}
    
    def parse_extinf_line(self, line):
        """
        解析EXTINF行
        """
        channel = {}
        
        # 提取tvg-name
        tvg_name_match = re.search(r'tvg-name="([^"]*)"', line)
        if tvg_name_match:
            channel['tvg_name'] = tvg_name_match.group(1)
        
        # 提取group-title
        group_match = re.search(r'group-title="([^"]*)"', line)
        if group_match:
            channel['group_title'] = group_match.group(1)
        
        # 提取频道名称（最后一个逗号后的内容）
        name_match = re.search(r',([^,]*)$', line)
        if name_match:
            channel['channel_name'] = name_match.group(1)
        else:
            # 如果没有逗号，尝试其他解析方式
            channel['channel_name'] = line
        
        return channel
    
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
        
        # 如果没有质量信息，默认接受
        channel['quality'] = 'unknown'
        return True
    
    def categorize_channels(self):
        """
        将频道按规则分类
        """
        for channel in self.sources:
            name = channel['channel_name'].lower()
            
            # 分类逻辑
            if '4k' in name or '超高清' in name:
                self.categories["4K"].append(channel)
            elif 'cctv' in name or '央视' in name or '中央' in name:
                self.categories["央视"].append(channel)
            elif '卫视' in name and 'cctv' not in name:
                self.categories["卫视"].append(channel)
            elif '凤凰' in name or '翡翠' in name or 'tvb' in name or '澳亚' in name or '港澳' in name:
                self.categories["港澳台"].append(channel)
            elif '电影' in name or '影院' in name or '剧场' in name or '影视' in name:
                self.categories["影视剧"].append(channel)
            elif '音乐' in name or 'mtv' in name:
                self.categories["音乐"].append(channel)
            elif '体育' in name or 'cctv5' in name or '运动' in name or 'nba' in name:
                self.categories["体育"].append(channel)
    
    def limit_channels_per_group(self):
        """
        限制每个分组的频道数量
        """
        for category, channels in self.categories.items():
            # 去重：基于URL去除重复频道
            unique_channels = {}
            for channel in channels:
                url = channel['url']
                if url not in unique_channels:
                    unique_channels[url] = channel
            
            unique_channel_list = list(unique_channels.values())
            
            # 限制数量：最少10个，最多90个
            if len(unique_channel_list) < 10:
                print(f"警告: {category} 分组频道数不足10个，当前为 {len(unique_channel_list)} 个")
            elif len(unique_channel_list) > 90:
                unique_channel_list = unique_channel_list[:90]
            
            self.categories[category] = unique_channel_list
    
    def generate_output_file(self):
        """
        生成最终的输出文件
        """
        with open('tzyauto.txt', 'w', encoding='utf-8') as f:
            f.write("# 自动生成的直播源文件\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# 分组格式: 频道名称,频道URL,#genre#\n\n")
            
            for category, channels in self.categories.items():
                if channels:  # 只输出有内容的分类
                    f.write(f"\n# {category}频道,#genre#\n")
                    for channel in channels:
                        f.write(f"{channel['channel_name']},{channel['url']}\n")
        
        print(f"文件生成完成! 共处理 {len(self.sources)} 个频道")

def main():
    collector = TVSourceCollector()
    print("开始收集直播源...")
    collector.fetch_all_sources()
    print(f"共收集到 {len(collector.sources)} 个频道")
    
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
    print(f"总计: {total_channels} 个频道")

if __name__ == "__main__":
    main()
