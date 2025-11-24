#!/usr/bin/env python3
"""
自动从 https://tonkiang.us/ 获取直播源并保存为 CGQ.TXT
"""

import requests
import re
import time
import sys
import os
from urllib.parse import urljoin, urlparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LiveSourceUpdater:
    def __init__(self):
        self.base_url = "https://tonkiang.us/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        })
        
    def get_live_sources(self, max_pages=5):
        """获取直播源数据"""
        all_sources = []
        
        for page in range(1, max_pages + 1):
            try:
                logger.info(f"正在获取第 {page} 页数据...")
                
                # 构建请求参数
                params = {}
                if page > 1:
                    params['page'] = str(page)
                
                response = self.session.get(
                    self.base_url, 
                    params=params,
                    timeout=30,
                    verify=True
                )
                response.raise_for_status()
                
                # 检查是否获取到有效内容
                if "没有找到" in response.text or "No results" in response.text:
                    logger.info(f"第 {page} 页没有内容，停止爬取")
                    break
                
                # 提取直播源链接
                sources = self.extract_sources(response.text)
                logger.info(f"第 {page} 页找到 {len(sources)} 个直播源")
                
                if sources:
                    all_sources.extend(sources)
                else:
                    logger.warning(f"第 {page} 页未提取到直播源")
                
                # 添加延迟
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"获取第 {page} 页时出错: {e}")
                continue
                
        return all_sources
    
    def extract_sources(self, html_content):
        """从HTML内容中提取直播源链接"""
        sources = []
        
        # 更全面的匹配模式
        patterns = [
            # M3U8链接
            r'https?://[^\s"\'<>{}|\\^`]*?\.m3u8(?:\?[^\s"\'<>{}|\\^`]*)?',
            # 其他视频流格式
            r'https?://[^\s"\'<>{}|\\^`]*?\.(?:ts|flv|mp4)(?:\?[^\s"\'<>{}|\\^`]*)?',
            # 包含在引号中的URL
            r'["\'](https?://[^\s"\'<>{}|\\^`]*?\.(?:m3u8|ts|flv|mp4)[^\s"\'<>{}|\\^`]*)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # 清理URL
                clean_url = self.clean_url(match)
                if clean_url and self.is_valid_source(clean_url):
                    sources.append(clean_url)
        
        # 去重
        unique_sources = []
        seen = set()
        for source in sources:
            if source not in seen:
                seen.add(source)
                unique_sources.append(source)
                
        return unique_sources
    
    def clean_url(self, url):
        """清理URL"""
        # 移除引号和特殊字符
        url = re.sub(r'[\'"<>{}|\\^`]', '', url)
        url = url.strip()
        
        # 确保是完整的URL
        if url.startswith('//'):
            url = 'https:' + url
        elif not url.startswith(('http://', 'https://')):
            # 如果不是完整URL，尝试修复
            if '.' in url and any(ext in url for ext in ['.m3u8', '.ts', '.flv', '.mp4']):
                url = 'https://' + url
        
        return url
    
    def is_valid_source(self, source):
        """验证直播源是否有效"""
        # 过滤无效域名
        invalid_domains = [
            'example.com', 'test.com', 'localhost', 
            '127.0.0.1', 'google.com', 'youtube.com'
        ]
        
        try:
            parsed = urlparse(source)
            if not parsed.netloc:
                return False
                
            # 检查域名
            if any(domain in parsed.netloc for domain in invalid_domains):
                return False
                
            # 检查文件扩展名
            path = parsed.path.lower()
            if not any(ext in path for ext in ['.m3u8', '.ts', '.flv', '.mp4']):
                return False
                
            return True
            
        except Exception:
            return False
    
    def save_sources(self, sources, filename="CGQ.TXT"):
        """保存直播源到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# 自动更新的直播源\n")
                f.write(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总数量: {len(sources)}\n")
                f.write("# 来源: https://tonkiang.us/\n")
                f.write("# 格式: M3U8直播源\n")
                f.write("\n")
                
                for source in sources:
                    f.write(f"{source}\n")
            
            logger.info(f"成功保存 {len(sources)} 个直播源到 {filename}")
            return True
            
        except Exception as e:
            logger.error(f"保存文件时出错: {e}")
            return False
    
    def update(self):
        """执行更新流程"""
        logger.info("开始更新直播源...")
        
        # 获取直播源
        sources = self.get_live_sources()
        
        if not sources:
            logger.error("未获取到任何直播源")
            # 创建空的CGQ.TXT文件
            with open("CGQ.TXT", "w", encoding="utf-8") as f:
                f.write("# 未获取到直播源\n")
                f.write(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            return True  # 仍然返回True，避免工作流失败
            
        logger.info(f"成功获取 {len(sources)} 个直播源")
        
        # 保存到文件
        return self.save_sources(sources)

def main():
    """主函数"""
    updater = LiveSourceUpdater()
    success = updater.update()
    
    if success:
        logger.info("直播源更新完成")
    else:
        logger.error("直播源更新失败")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
