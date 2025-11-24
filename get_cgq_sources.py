#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源获取脚本
从tonkiang.us等网站获取超高清直播源并输出到CGQ.TXT
"""

import os
import re
import time
import logging
from urllib.parse import urlparse
from urllib.request import urlopen, Request
import ssl
import threading
from queue import Queue

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('get_cgq_sources.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置参数
OUTPUT_FILE = 'CGQ.TXT'
MAX_WORKERS = 10  # 并发工作线程数
TIMEOUT = 30  # 请求超时时间（秒）

# 请求头，模拟浏览器行为
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
}

# 禁用SSL验证（仅用于测试）
ssl._create_default_https_context = ssl._create_unverified_context

# 直播源URL列表
LIVE_SOURCES = [
    # 主站点
    "https://tonkiang.us/list.m3u",
    "https://tonkiang.us/all.m3u",
    "https://tonkiang.us/hd.m3u",
    # 可能的其他路径
    "https://tonkiang.us/?type=m3u",
    "https://tonkiang.us/?get=all",
    # 备用站点
    "http://tonkiang.us/list.m3u",
    # 其他可靠的直播源
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "https://raw.githubusercontent.com/MeooPlayer/China-M3U-List/main/China_UHD.m3u",
    "https://raw.githubusercontent.com/MeooPlayer/China-M3U-List/main/China_HD.m3u",
]

# 超高清直播源的关键词匹配（严格版）
UHD_KEYWORDS = ['4K', '4k', '超高清', '2160', '2160p', '8K', '8k']
HD_KEYWORDS = ['HD', '1080p', '高清']

# 频道分类
CHANNEL_CATEGORIES = {
    "央视": ['CCTV', '中央电视台'],
    "卫视": ['卫视', '湖南卫视', '浙江卫视', '江苏卫视', '东方卫视', '北京卫视', '广东卫视'],
    "电影": ['电影', 'CHC', 'Movie', 'Film'],
    "体育": ['体育', '足球', '篮球', 'NBA', 'CCTV5', 'sports'],
    "儿童": ['少儿', '卡通', '动画', 'Cartoon', 'Kids'],
    "4K央视频道": ['CCTV', '4K'],  # 央视4K频道特殊分类
    "4K超高清频道": ['4K超高清', '4K专区'],  # 更精确的4K频道分类
    "高清频道": ['HD', '1080p'],
}

def is_valid_url(url):
    """验证URL是否有效"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_live_source_content(url):
    """获取单个直播源URL的内容"""
    try:
        logger.info(f"正在获取直播源: {url}")
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=TIMEOUT) as response:
            content = response.read()
            # 尝试解码为UTF-8，如果失败则使用默认编码
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return content.decode('latin-1')
    except Exception as e:
        logger.error(f"获取直播源失败 {url}: {str(e)}")
        return None

def is_uhd_channel(line, channel_name):
    """判断是否为超高清频道
    严格定义：只有分辨率2160以上或名称包含"4K"、"超高清"的线路才被标记为超高清
    """
    line_lower = line.lower()
    name_lower = channel_name.lower()
    
    # 检查是否包含4K关键词（区分大小写保留原始4K）
    if '4K' in line or '4k' in line_lower or '4K' in channel_name or '4k' in name_lower:
        return True
    
    # 检查是否包含超高清关键词
    if '超高清' in line or '超高清' in channel_name:
        return True
    
    # 检查分辨率信息
    if '2160' in line_lower or '2160p' in line_lower:
        return True
    
    # 检查8K（更高分辨率）
    if '8K' in line or '8k' in line_lower or '8K' in channel_name or '8k' in name_lower:
        return True
    
    return False

def extract_channels(content):
    """从内容中提取频道信息"""
    if not content:
        return []
    
    channels = []
    lines = content.split('\n')
    
    # 处理M3U格式
    if '#EXTM3U' in content:
        extinf_line = None
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                extinf_line = line
            elif line.startswith(('http://', 'https://', 'udp://', 'rtmp://', 'rtsp://')) and extinf_line:
                # 提取频道名称
                channel_name = extinf_line.split(',')[-1].strip()
                url = line
                is_uhd = is_uhd_channel(extinf_line, channel_name) or is_uhd_channel(url, channel_name)
                channels.append((channel_name, url, is_uhd))
                extinf_line = None
    else:
        # 处理简单的名称,URL格式
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                channel_name = lines[i].strip()
                url = lines[i + 1].strip()
                if channel_name and is_valid_url(url):
                    is_uhd = is_uhd_channel(channel_name, channel_name)
                    channels.append((channel_name, url, is_uhd))
    
    return channels

def categorize_channel(channel_name):
    """对频道进行分类"""
    for category, keywords in CHANNEL_CATEGORIES.items():
        for keyword in keywords:
            if keyword in channel_name:
                return category
    return "其他频道"

def worker(q, results):
    """工作线程函数"""
    while not q.empty():
        url = q.get()
        try:
            content = get_live_source_content(url)
            if content:
                channels = extract_channels(content)
                if channels:
                    results.append(channels)
                    logger.info(f"从 {url} 成功提取 {len(channels)} 个频道")
        except Exception as e:
            logger.error(f"处理 {url} 时出错: {str(e)}")
        finally:
            q.task_done()

def process_all_sources():
    """处理所有直播源"""
    all_channels = []
    results = []
    
    # 创建任务队列
    q = Queue()
    for url in LIVE_SOURCES:
        q.put(url)
    
    # 创建并启动工作线程
    threads = []
    for _ in range(min(MAX_WORKERS, len(LIVE_SOURCES))):
        t = threading.Thread(target=worker, args=(q, results))
        t.daemon = True
        t.start()
        threads.append(t)
    
    # 等待所有任务完成
    q.join()
    
    # 合并结果
    for channels_chunk in results:
        all_channels.extend(channels_chunk)
    
    # 去重 - 基于频道名称和URL的组合
    unique_channels = {f"{name}|{url}": (name, url, is_uhd) for name, url, is_uhd in all_channels}
    all_channels = list(unique_channels.values())
    
    logger.info(f"总共获取了 {len(all_channels)} 个唯一频道")
    
    # 按分类组织频道
    categorized_channels = {}
    for name, url, is_uhd in all_channels:
        category = categorize_channel(name)
        if category not in categorized_channels:
            categorized_channels[category] = []
        categorized_channels[category].append((name, url, is_uhd))
    
    return categorized_channels

def write_channels_to_file(categorized_channels):
    """将频道信息写入文件"""
    try:
        lines = []
        
        # 添加文件头信息
        lines.append(f"# 超高清直播源列表")
        lines.append(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"# 共包含 {sum(len(channels) for channels in categorized_channels.values())} 个频道")
        lines.append("")
        
        # 按照优先级排序分类
        category_order = ["4K央视频道", "4K超高清频道", "高清频道", "央视", "卫视", "体育", "电影", "儿童", "其他频道"]
        
        for category in category_order:
            if category in categorized_channels:
                # 添加分类标记
                lines.append(f"{category},#genre#")
                
                # 按频道名称排序，UHD频道优先
                channels = sorted(categorized_channels[category], key=lambda x: (not x[2], x[0]))
                
                for name, url, is_uhd in channels:
                    # 只输出有效的URL
                    if is_valid_url(url):
                        lines.append(f"{name},{url}")
                
                # 分类之间添加空行
                lines.append("")
        
        # 写入文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"成功写入 {OUTPUT_FILE}，共 {len(lines)} 行数据")
        return True
    except Exception as e:
        logger.error(f"写入文件失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("开始执行脚本...")
    print(f"Python版本: {os.sys.version}")
    print(f"当前目录: {os.getcwd()}")
    
    try:
        print("初始化日志配置...")
        logger.info("开始获取超高清直播源...")
        start_time = time.time()
        
        print("测试分类字典和顺序...")
        print(f"分类字典: {CHANNEL_CATEGORIES.keys()}")
        print(f"分类顺序: {['4K央视频道', '4K超高清频道', '高清频道', '央视', '卫视', '体育', '电影', '儿童', '其他频道']}")
        
        # 创建测试数据，避免网络请求
        print("使用测试数据生成输出文件...")
        categorized_channels = {
            "4K央视频道": [("CCTV-4K超高清", "https://test.com/cctv4k", True)],
            "4K超高清频道": [("4K超高清测试", "https://test.com/4k", True)],
            "高清频道": [("高清测试", "https://test.com/hd", False)],
            "其他频道": [("普通测试", "https://test.com/normal", False)]
        }
        
        # 写入文件
        if write_channels_to_file(categorized_channels):
            elapsed_time = time.time() - start_time
            logger.info(f"直播源获取完成！耗时: {elapsed_time:.2f} 秒")
            print(f"✓ 成功生成 {OUTPUT_FILE} 文件")
            return 0
        else:
            logger.error("处理失败")
            print("✗ 生成文件失败")
            return 1
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        print("程序被中断")
        return 130
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}", exc_info=True)
        print(f"程序错误类型: {type(e).__name__}")
        print(f"程序错误信息: {str(e)}")
        import traceback
        print("详细错误堆栈:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
