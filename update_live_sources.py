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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('update.log', encoding='utf-8')
    ]
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
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def get_live_sources(self, max_pages=5):
        """获取直播源数据"""
        all_sources = []
        
        for page in range(1, max_pages + 1):
            try:
                logger.info(f"正在获取第 {page} 页数据...")
                
                params = {}
                if page > 1:
                    params['page'] = str(page)
                
                response = self.session.get(
                    self.base_url, 
                    params=params,
                    timeout=60,
                    verify=True
                )
                response.raise_for_status()
                
                # 检查页面内容是否有效
                if len(response.text) < 1000:
                    logger.warning(f"第 {page} 页内容过短，可能已到达末页")
                    break
                
                # 提取直播源链接
                sources = self.extract_sources(response.text)
                if not sources:
                    logger.warning(f"第 {page} 页未找到直播源")
                    # 如果连续两页没有找到源，停止爬取
                    if page > 2 and len(all_sources) == 0:
                        break
                    continue
                    
                all_sources.extend(sources)
                logger.info(f"第 {page} 页找到 {len(sources)} 个直播源")
                
                # 添加延迟避免请求过快
                time.sleep(3)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"获取第 {page} 页时网络错误: {e}")
                continue
            except Exception as e:
                logger.error(f"获取第 {page} 页时出错: {e}")
                continue
                
        return all_sources
    
    def extract_sources(self, html_content):
        """从HTML内容中提取直播源链接"""
        sources = []
        
        # 多种匹配模式
        patterns = [
            # 匹配m3u8链接
            r'https?://[^\s<>"\'{}|\\^`]*?\.m3u8(?:\?[^\s<>"\'{}|\\^`]*)?',
            # 匹配包含直播源文本的行
            r'[^\s<>"\'{}|\\^`]*?\.(?:m3u8|ts|flv|mp4)(?:\?[^\s<>"\'{}|\\^`]*)?',
            # 匹配URL格式
            r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*\.(?:m3u8|ts|flv|mp4)[^\s]*',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            # 过滤和清理URL
            cleaned_matches = [self.clean_url(match) for match in matches]
            sources.extend(cleaned_matches)
        
        # 去重并保持顺序
        seen = set()
        unique_sources = []
        for source in sources:
            if source and source not in seen and self.is_valid_source(source):
                seen.add(source)
                unique_sources.append(source)
                
        return unique_sources
    
    def clean_url(self, url):
        """清理URL"""
        # 移除可能的HTML标签和特殊字符
        url = re.sub(r'[<>"\'{}|\\^`]', '', url)
        # 确保URL以http开头
        if not url.startswith(('http://', 'https://')):
            # 尝试修复相对URL
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith(('http://', 'https://')):
                url = 'https://' + url
        return url.strip()
    
    def is_valid_source(self, source):
        """验证直播源是否有效"""
        # 过滤掉明显无效的链接
        invalid_keywords = [
            'example.com', 'test.com', 'localhost', '127.0.0.1',
            'google', 'facebook', 'twitter', 'youtube'
        ]
        
        valid_extensions = ['.m3u8', '.ts', '.flv', '.mp4']
        
        # 检查是否包含无效关键词
        if any(keyword in source.lower() for keyword in invalid_keywords):
            return False
            
        # 检查是否有有效的文件扩展名
        if not any(ext in source.lower() for ext in valid_extensions):
            return False
            
        # 检查URL格式
        try:
            parsed = urlparse(source)
            if not parsed.scheme or not parsed.netloc:
                return False
        except Exception:
            return False
            
        return True
    
    def save_sources(self, sources, filename="CGQ.TXT"):
        """保存直播源到文件"""
        try:
            # 对源进行排序
            sorted_sources = sorted(sources)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# 自动更新的直播源\n")
                f.write(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总数量: {len(sorted_sources)}\n")
                f.write("# 来源: https://tonkiang.us/\n")
                f.write("# 格式: 直接可用的直播源链接\n")
                f.write("\n")
                
                for i, source in enumerate(sorted_sources, 1):
                    f.write(f"{source}\n")
            
            logger.info(f"成功保存 {len(sorted_sources)} 个直播源到 {filename}")
            
            # 同时保存一个统计信息
            stats = {
                'total_sources': len(sorted_sources),
                'update_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'unique_domains': len(set(urlparse(source).netloc for source in sorted_sources))
            }
            
            logger.info(f"统计信息: {stats}")
            return True
            
        except Exception as e:
            logger.error(f"保存文件时出错: {e}")
            return False
    
    def update(self):
        """执行更新流程"""
        logger.info("开始更新直播源...")
        logger.info(f"目标网站: {self.base_url}")
        
        try:
            sources = self.get_live_sources()
            
            if not sources:
                logger.error("未获取到任何直播源")
                return False
                
            logger.info(f"总共获取到 {len(sources)} 个直播源")
            
            # 统计域名分布
            domains = {}
            for source in sources:
                domain = urlparse(source).netloc
                domains[domain] = domains.get(domain, 0) + 1
            
            logger.info("域名分布统计:")
            for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
                logger.info(f"  {domain}: {count} 个源")
            
            # 保存到文件
            success = self.save_sources(sources)
            
            if success:
                logger.info("直播源更新完成")
            else:
                logger.error("直播源更新失败")
                
            return success
            
        except Exception as e:
            logger.error(f"更新过程中发生错误: {e}")
            return False

def main():
    """主函数"""
    try:
        updater = LiveSourceUpdater()
        success = updater.update()
        
        # 设置退出码
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
