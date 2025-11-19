#!/usr/bin/env python3
"""
TV直播源主收集脚本
功能：从多个数据源采集直播源，进行初步去重和验证
"""

import requests
import re
import json
import time
import logging
from urllib.parse import urljoin

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 更多的数据源
GITHUB_SOURCES = [
    "iptv-org/iptv",
    "imDazui/Tvlist-awesome-m3u-m3u8", 
    "Free-IPTV/Countries",
    "ruvelro/IPTV",
    # 可以添加更多数据源
]

class TVSourceCollector:
    def __init__(self):
        self.sources = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_github_sources(self):
        """从GitHub仓库搜索直播源"""
        logger.info(f"开始从 {len(GITHUB_SOURCES)} 个数据源收集...")
        
        for repo in GITHUB_SOURCES:
            try:
                logger.info(f"处理仓库: {repo}")
                # 获取仓库内容
                api_url = f"https://api.github.com/repos/{repo}/contents/"
                response = self.session.get(api_url, timeout=30)
                
                if response.status_code == 200:
                    files = response.json()
                    m3u_files = [f for f in files if f['name'].endswith(('.m3u', '.m3u8', '.txt'))]
                    
                    logger.info(f"在 {repo} 中找到 {len(m3u_files)} 个可能的数据文件")
                    
                    for file_info in m3u_files[:5]:  # 限制处理前5个文件避免超时
                        self.process_m3u_file(file_info['download_url'])
                        
                elif response.status_code == 403:
                    logger.warning(f"访问限制: {repo}，跳过")
                else:
                    logger.warning(f"无法访问 {repo}: HTTP {response.status_code}")
                    
                time.sleep(1)  # 避免请求过快
                
            except Exception as e:
                logger.error(f"处理仓库 {repo} 时出错: {e}")
                continue
    
    def process_m3u_file(self, url):
        """处理单个m3u文件"""
        try:
            logger.info(f"下载文件: {url}")
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                channels = self.parse_m3u_content(response.text)
                logger.info(f"从文件中解析出 {len(channels)} 个频道")
                self.sources.extend(channels)
            else:
                logger.warning(f"下载失败: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"处理文件 {url} 时出错: {e}")
    
    def parse_m3u_content(self, content):
        """解析m3u文件内容"""
        channels = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines) - 1:
            line = lines[i].strip()
            if line.startswith('#EXTINF:'):
                # 解析频道信息
                extinf = line
                url_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                
                if url_line and not url_line.startswith('#') and url_line:
                    channel = {
                        'name': self.extract_channel_name(extinf),
                        'url': url_line,
                        'group': self.extract_group(extinf),
                        'resolution': self.extract_resolution(extinf)
                    }
                    # 基础过滤
                    if self.is_chinese_source(channel):
                        channels.append(channel)
                
                i += 2
            else:
                i += 1
        
        return channels
    
    def extract_channel_name(self, extinf_line):
        """提取频道名称"""
        # 尝试多种模式匹配频道名
        patterns = [
            r',([^,]+?)(?:\s*\([^)]*\))?\s*$',
            r'tvg-name="([^"]*)"',
            r',(.+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, extinf_line)
            if match:
                name = match.group(1).strip()
                if name and name != '""':
                    return name
        
        return "未知频道"
    
    def extract_group(self, extinf_line):
        """提取分组信息"""
        match = re.search(r'group-title="([^"]*)"', extinf_line)
        return match.group(1) if match else "其他"
    
    def extract_resolution(self, extinf_line):
        """提取分辨率信息"""
        extinf_lower = extinf_line.lower()
        if '4k' in extinf_lower or '2160' in extinf_lower:
            return '4K'
        elif '1080' in extinf_lower:
            return '1080p'
        elif '720' in extinf_lower:
            return '720p'
        elif 'hd' in extinf_lower:
            return 'HD'
        else:
            return 'SD'
    
    def is_chinese_source(self, channel):
        """判断是否为中国境内可访问的源"""
        name = channel['name'].lower()
        url = channel['url'].lower()
        
        # 排除明显不可访问的源
        blocked_keywords = ['porn', 'xxx', 'adult', 'proxy', 'vpn', '国外', '海外']
        if any(kw in name or kw in url for kw in blocked_keywords):
            return False
        
        # 优先选择中文频道
        chinese_keywords = ['cctv', '央视', '卫视', '香港', '台湾', '澳门', '电影', '体育', '音乐']
        if any(kw in name for kw in chinese_keywords):
            return True
        
        return True

def main():
    collector = TVSourceCollector()
    logger.info("开始收集直播源...")
    
    collector.search_github_sources()
    
    # 去重
    unique_sources = []
    seen_urls = set()
    
    for source in collector.sources:
        if source['url'] not in seen_urls:
            unique_sources.append(source)
            seen_urls.add(source['url'])
    
    logger.info(f"收集完成: 原始 {len(collector.sources)} 个, 去重后 {len(unique_sources)} 个")
    
    # 保存原始数据
    try:
        with open('raw_sources.json', 'w', encoding='utf-8') as f:
            json.dump(unique_sources, f, ensure_ascii=False, indent=2)
        logger.info("原始数据保存成功")
    except Exception as e:
        logger.error(f"保存原始数据失败: {e}")
    
    return unique_sources

if __name__ == "__main__":
    main()
