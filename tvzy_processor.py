#!/usr/bin/env python3
"""
TV直播源处理器
功能：对采集的源进行分类、筛选和生成最终文件
"""

import json
import re
import os
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
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def load_sources(self, filename='raw_sources.json'):
        """加载原始数据"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.logger.info(f"成功加载 {len(data)} 个原始频道")
                return data
        except FileNotFoundError:
            self.logger.error("未找到原始数据文件，请先运行采集脚本")
            return []
        except json.JSONDecodeError:
            self.logger.error("原始数据文件格式错误")
            return []
    
    def categorize_channel(self, channel):
        """对频道进行分类"""
        name = channel['name'].lower()
        group = channel['group'].lower()
        
        # 4K频道检测
        if channel['resolution'] == '4K' or '4k' in name:
            return '4K'
        
        # 央视频道检测
        if any(keyword in name for keyword in ['cctv', '央视', '中央']):
            return '央视'
        
        # 卫视检测
        if any(keyword in name for keyword in ['卫视', 'tv']):
            return '卫视'
        
        # 港澳台频道检测
        if any(keyword in name for keyword in ['香港', '澳门', '台湾', '翡翠', '明珠', 'tvb', '凤凰']):
            return '港澳台'
        
        # 影视剧频道检测
        if any(keyword in name for keyword in ['电影', '影视', '剧场', '影院']):
            return '影视剧'
        
        # 音乐频道检测
        if any(keyword in name for keyword in ['音乐', 'mtv', '演唱会']):
            return '音乐'
        
        # 体育频道检测
        if any(keyword in name for keyword in ['体育', '足球', '篮球', '奥运', 'nba']):
            return '体育'
        
        return '其他'
    
    def filter_quality_sources(self, sources, min_sources=10, max_sources=90):
        """筛选高质量源"""
        quality_sources = []
        
        for source in sources:
            # 只保留1080p及以上的源
            if source.get('resolution') in ['1080p', '4K']:
                quality_sources.append(source)
        
        self.logger.info(f"质量筛选后剩余 {len(quality_sources)} 个高清频道")
        
        # 按频道名分组，每个频道保留最佳源
        channel_groups = defaultdict(list)
        for source in quality_sources:
            channel_name = source['name']
            channel_groups[channel_name].append(source)
        
        # 为每个频道选择最佳源（优先高分辨率）
        final_sources = []
        for channel_name, sources in channel_groups.items():
            # 按分辨率排序：4K > 1080p > 其他
            sorted_sources = sorted(sources, 
                                  key=lambda x: {'4K': 3, '1080p': 2, '720p': 1}.get(x.get('resolution', ''), 0),
                                  reverse=True)
            # 每个频道最多保留3个最佳源
            final_sources.extend(sorted_sources[:3])
        
        return final_sources
    
    def generate_output(self, categorized_sources):
        """生成最终输出文件"""
        output_lines = ["#EXTM3U"]
        total_channels = 0
        
        for category, sources in categorized_sources.items():
            if sources:
                # 限制每个类别最多90个源
                category_sources = sources[:90]
                output_lines.append(f"\n# {category},#genre#")
                total_channels += len(category_sources)
                
                for source in category_sources:
                    output_lines.append(f"#EXTINF:-1 tvg-id=\"\" tvg-name=\"{source['name']}\" tvg-logo=\"\" group-title=\"{category}\",{source['name']}")
                    output_lines.append(source['url'])
        
        # 写入文件
        try:
            with open('tzyauto.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines))
            
            self.logger.info(f"成功生成 tzyauto.txt，包含 {total_channels} 个频道，{len(output_lines)} 行")
            return True
        except Exception as e:
            self.logger.error(f"写入文件失败: {e}")
            return False
    
    def process(self):
        """主处理流程"""
        self.logger.info("开始处理直播源数据...")
        
        sources = self.load_sources()
        if not sources:
            self.logger.warning("没有可用的原始数据，创建基础文件")
            # 创建基础文件
            with open('tzyauto.txt', 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n# 自动更新脚本 - 数据收集进行中\n")
            return
        
        # 筛选高质量源
        quality_sources = self.filter_quality_sources(sources)
        
        # 分类
        categorized = defaultdict(list)
        uncategorized = []
        
        for source in quality_sources:
            category = self.categorize_channel(source)
            if category and category != '其他':
                categorized[category].append(source)
            else:
                uncategorized.append(source)
        
        # 如果有未分类的频道，添加到"其他"类别
        if uncategorized:
            categorized['其他'] = uncategorized
        
        self.logger.info("分类统计:")
        for category, sources in categorized.items():
            self.logger.info(f"  {category}: {len(sources)} 个频道")
        
        # 生成输出
        success = self.generate_output(categorized)
        if not success:
            # 如果生成失败，创建基础文件
            with open('tzyauto.txt', 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n# 自动更新脚本 - 生成文件时出错\n")

if __name__ == "__main__":
    processor = TVSourceProcessor()
    processor.process()
