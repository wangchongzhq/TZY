#!/usr/bin/env python3
# tvzy_autocollect.py

import requests
import re
import json
from datetime import datetime
import time
import os

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
        
    def fetch_all_sources(self):
        """
        从多个数据源获取直播源
        这里需要你添加实际的数据源URL
        """
        data_sources = [
            # 示例数据源，需要替换为真实可用的源
            "https://example.com/source1.m3u",
            "https://example.com/source2.m3u",
            # 添加至少10个不同的数据源
        ]
        
        for source_url in data_sources:
            try:
                response = requests.get(source_url, timeout=10)
                if response.status_code == 200:
                    self.parse_m3u_content(response.text, source_url)
                time.sleep(1)  # 避免请求过于频繁
            except Exception as e:
                print(f"获取源 {source_url} 失败: {e}")
                continue
    
    def parse_m3u_content(self, content, source_url):
        """
        解析M3U格式内容，提取频道信息
        需要根据实际数据源格式调整解析逻辑
        """
        lines = content.split('\n')
        current_channel = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                # 解析频道信息，例如: #EXTINF:-1 tvg-id="CCTV1" tvg-name="CCTV1" group-title="央视",CCTV-1 综合
                match = re.search(r'tvg-name="([^"]*)".*group-title="([^"]*)",(.*)', line)
                if match:
                    current_channel = {
                        'tvg_name': match.group(1),
                        'group_title': match.group(2),
                        'channel_name': match.group(3),
                        'source': source_url
                    }
            elif line.startswith('http'):
                if current_channel:
                    current_channel['url'] = line
                    # 这里可以添加清晰度检测逻辑
                    if self.check_quality(current_channel):
                        self.sources.append(current_channel.copy())
                    current_channel = {}
    
    def check_quality(self, channel):
        """
        检查频道清晰度是否符合要求
        实际使用时需要更完善的检测逻辑
        """
        name = channel['channel_name'].lower()
        # 初步基于名称过滤，理想情况应该实际测试链接
        if '4k' in name or 'uhd' in name:
            channel['quality'] = '4K'
            return True
        elif '1080' in name or 'fhd' in name:
            channel['quality'] = '1080p'
            return True
        elif '高清' in name or 'hd' in name:
            channel['quality'] = '720p'
            return True
        return False
    
    def categorize_channels(self):
        """
        将频道按规则分类
        """
        for channel in self.sources:
            name = channel['channel_name']
            group = channel['group_title']
            
            # 分类逻辑 - 需要根据实际频道名称调整
            if '4k' in name.lower():
                self.categories["4K"].append(channel)
            elif 'cctv' in name.lower() or '央视' in name:
                self.categories["央视"].append(channel)
            elif '卫视' in name:
                self.categories["卫视"].append(channel)
            elif '凤凰' in name or '翡翠' in name or 'tvb' in name.lower() or '澳亚' in name:
                self.categories["港澳台"].append(channel)
            elif '电影' in name or '影院' in name or '剧场' in name:
                self.categories["影视剧"].append(channel)
            elif '音乐' in name:
                self.categories["音乐"].append(channel)
            elif '体育' in name or 'cctv5' in name.lower():
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
                f.write(f"\n# {category}频道\n")
                for channel in channels:
                    f.write(f"{channel['channel_name']},{channel['url']},#genre#\n")
        
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
    for category, channels in collector.categories.items():
        print(f"{category}: {len(channels)} 个频道")

if __name__ == "__main__":
    main()
