#!/usr/bin/env python3
"""
TV直播源处理器
功能：对采集的源进行分类、筛选和生成最终文件
"""

import json
import re
from collections import defaultdict
import logging

class TVSourceProcessor:
    def __init__(self):
        self.categories = {
            '4K': [],
            '央视': [],
            '卫视': [], 
            '港澳台': [],
            '影视剧': [],
            '音乐': [],
            '体育': []
        }
    
    def load_sources(self, filename='raw_sources.json'):
        """加载原始数据"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("未找到原始数据文件，请先运行采集脚本")
            return []
    
    def categorize_channel(self, channel):
        """对频道进行分类"""
        name = channel['name']
        group = channel['group']
        
        # 4K频道检测
        if channel['resolution'] == '4K' or '4k' in name.lower():
            return '4K'
        
        # 央视频道检测
        if any(keyword in name for keyword in ['CCTV', '央视', '中央']):
            return '央视'
        
        # 卫视检测
        if any(keyword in name for keyword in ['卫视', 'TV']):
            return '卫视'
        
        # 港澳台频道检测
        if any(keyword in name for keyword in ['香港', '澳门', '台湾', '翡翠', '明珠']):
            return '港澳台'
        
        # 影视剧频道检测
        if any(keyword in name for keyword in ['电影', '影视', '剧场', '影院']):
            return '影视剧'
        
        # 音乐频道检测
        if any(keyword in name for keyword in ['音乐', 'MTV', '演唱会']):
            return '音乐'
        
        # 体育频道检测
        if any(keyword in name for keyword in ['体育', '足球', '篮球', '奥运']):
            return '体育'
        
        return None
    
    def filter_quality_sources(self, sources, min_sources=10, max_sources=90):
        """筛选高质量源"""
        quality_sources = []
        
        for source in sources:
            # 只保留1080p及以上的源
            if source['resolution'] in ['1080p', '4K']:
                quality_sources.append(source)
        
        # 按频道名分组，每个频道保留最佳源
        channel_groups = defaultdict(list)
        for source in quality_sources:
            channel_groups[source['name']].append(source)
        
        # 为每个频道选择最佳源（优先高分辨率）
        final_sources = []
        for channel_name, sources in channel_groups.items():
            sorted_sources = sorted(sources, 
                                  key=lambda x: 2 if x['resolution'] == '4K' else 1 if x['resolution'] == '1080p' else 0,
                                  reverse=True)
            # 每个频道最多保留3个最佳源
            final_sources.extend(sorted_sources[:3])
        
        return final_sources
    
    def generate_output(self, categorized_sources):
        """生成最终输出文件"""
        output_lines = []
        
        for category, sources in categorized_sources.items():
            if sources:
                output_lines.append(f"\n# {category},#genre#")
                for source in sources[:90]:  # 最多90个源
                    output_lines.append(f"#EXTINF:-1 tvg-id=\"\" tvg-name=\"{source['name']}\" tvg-logo=\"\" group-title=\"{category}\",{source['name']}")
                    output_lines.append(source['url'])
        
        # 写入文件
        with open('tzyauto.txt', 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            f.write('\n'.join(output_lines))
        
        print(f"生成文件完成，共 {len(output_lines)//2} 个频道")
    
    def process(self):
        """主处理流程"""
        sources = self.load_sources()
        if not sources:
            return
        
        # 筛选高质量源
        quality_sources = self.filter_quality_sources(sources)
        print(f"质量筛选后剩余 {len(quality_sources)} 个频道")
        
        # 分类
        categorized = defaultdict(list)
        for source in quality_sources:
            category = self.categorize_channel(source)
            if category:
                categorized[category].append(source)
        
        # 生成输出
        self.generate_output(categorized)

if __name__ == "__main__":
    processor = TVSourceProcessor()
    processor.process()
