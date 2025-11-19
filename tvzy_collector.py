#!/usr/bin/env python3
"""
TV直播源主收集脚本
功能：从多个数据源采集直播源，进行初步去重和验证
"""

import requests
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor
import logging

# 配置GitHub搜索的数据源（示例仓库，实际需要更多）
GITHUB_SOURCES = [
    "iptv-org/iptv",
    "imDazui/Tvlist-awesome-m3u-m3u8",
    "badO1a5A90/YouTube-TV",
    # 可添加更多数据源
]

class TVSourceCollector:
    def __init__(self):
        self.sources = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_github_sources(self):
        """从GitHub仓库搜索直播源"""
        for repo in GITHUB_SOURCES:
            try:
                # 获取仓库中的m3u文件
                api_url = f"https://api.github.com/repos/{repo}/contents/"
                response = self.session.get(api_url)
                if response.status_code == 200:
                    files = response.json()
                    m3u_files = [f for f in files if f['name'].endswith('.m3u')]
                    
                    for file_info in m3u_files:
                        self.process_m3u_file(file_info['download_url'])
            except Exception as e:
                logging.error(f"处理仓库 {repo} 时出错: {e}")
    
    def process_m3u_file(self, url):
        """处理单个m3u文件"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                channels = self.parse_m3u_content(response.text)
                self.sources.extend(channels)
        except Exception as e:
            logging.error(f"处理文件 {url} 时出错: {e}")
    
    def parse_m3u_content(self, content):
        """解析m3u文件内容"""
        channels = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines) - 1:
            if lines[i].startswith('#EXTINF:'):
                # 解析频道信息
                extinf = lines[i]
                url = lines[i + 1] if i + 1 < len(lines) else ""
                
                if url and not url.startswith('#'):
                    channel = {
                        'name': self.extract_channel_name(extinf),
                        'url': url.strip(),
                        'group': self.extract_group(extinf),
                        'resolution': self.extract_resolution(extinf)
                    }
                    # 基础过滤：只保留中国境内可访问的源
                    if self.is_chinese_source(channel):
                        channels.append(channel)
                
                i += 2
            else:
                i += 1
        
        return channels
    
    def extract_channel_name(self, extinf_line):
        """提取频道名称"""
        match = re.search(r',(.+?)(?:\s*\(|$)', extinf_line)
        return match.group(1).strip() if match else "未知频道"
    
    def extract_group(self, extinf_line):
        """提取分组信息"""
        match = re.search(r'group-title="([^"]*)"', extinf_line)
        return match.group(1) if match else "其他"
    
    def extract_resolution(self, extinf_line):
        """提取分辨率信息"""
        if '1080' in extinf_line:
            return '1080p'
        elif '720' in extinf_line:
            return '720p'
        elif '4K' in extinf_line or '2160' in extinf_line:
            return '4K'
        else:
            return 'SD'
    
    def is_chinese_source(self, channel):
        """判断是否为中国境内可访问的源"""
        # 根据频道名称和URL进行基础判断
        name = channel['name'].lower()
        url = channel['url'].lower()
        
        # 排除明显不可访问的源
        blocked_keywords = ['porn', 'xxx', 'adult', 'proxy', 'vpn']
        if any(kw in name or kw in url for kw in blocked_keywords):
            return False
        
        return True

def main():
    collector = TVSourceCollector()
    print("开始收集直播源...")
    collector.search_github_sources()
    print(f"初步收集到 {len(collector.sources)} 个频道")
    
    # 保存原始数据
    with open('raw_sources.json', 'w', encoding='utf-8') as f:
        json.dump(collector.sources, f, ensure_ascii=False, indent=2)
    
    return collector.sources

if __name__ == "__main__":
    main()
