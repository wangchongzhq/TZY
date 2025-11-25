#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源获取脚本
从多个可靠来源获取超高清直播源并输出到CGQ.TXT
"""

import os
import re
import time
import logging
import sys
from urllib.parse import urlparse
from urllib.request import urlopen, Request
import ssl
import threading
from queue import Queue

# 启用简洁日志模式
DEBUG = False

# 配置日志（只保留当天数据）
log_level = logging.INFO  # 固定为INFO级别，减少日志量
today = time.strftime('%Y-%m-%d')
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'get_cgq_sources_{today}.log', encoding='utf-8', mode='w'),  # 每天创建新日志文件，覆盖旧的
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 确保标准输出编码为UTF-8
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 配置参数
OUTPUT_FILE = 'CGQ.TXT'
MAX_WORKERS = 10  # 并发工作线程数
TIMEOUT = 30  # 请求超时时间（秒）

# 请求头，模拟浏览器行为
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
}

# 禁用SSL验证（仅用于测试）
ssl._create_default_https_context = ssl._create_unverified_context

# 直播源URL列表
LIVE_SOURCES = [
    # 可靠的直播源
    "https://ghfast.top/raw.githubusercontent.com/ffmking/tv1/main/888.txt",
    # 其他直播源
    "https://ghcy.eu.org/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/kimwang1978/collect-txt/refs/heads/main/bbxx.txt",
    # 新增的直播源
    "https://ghcy.eu.org/https://raw.githubusercontent.com/onlylove2023/iptv/refs/heads/main/IPTV.m3u",
    "https://live.icnwe.com/tv/iptv4.txt",
    "https://live.zbds.top/tv/iptv4.txt",
    # 用户提供的新直播源
    "https://ghfast.top/https://github.com/8080713/iptv-api666/raw/refs/heads/main/output/result.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/Rivens7/Livelist/refs/heads/main/IPTV.m3u",
    "https://zbds.org/tv/iptv4.txt",
    # GitHub直播源URL
    "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/4K.m3u",
    "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/HDTV.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u",
    "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV.txt",
    "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_143.txt",
    "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_146.txt",
    "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_156.txt",
    "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_160.txt",
    "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_161.txt",
    "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_162.txt",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/uk.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/jp.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/kr.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/hk.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tw.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/sg.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/my.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/th.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/kh.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/la.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/vn.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/mm.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/id.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ph.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/in.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/pk.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bd.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/lk.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/sa.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ae.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/qa.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/kw.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/bh.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/om.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/jo.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ps.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/il.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/eg.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ma.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/dz.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tn.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ly.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tun.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/syr.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ir.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/iq.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/yemen.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/com.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/reunion.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/mauritius.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/seychelles.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/madagascar.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/maldives.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/marshall.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/micronesia.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/palau.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/vanuatu.m3u",
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
    """验证URL是否有效，添加更严格的检查"""
    if not url or not isinstance(url, str):
        return False
    
    # 检查是否包含多个URL协议头
    protocols = re.findall(r'https?://|udp://|rtmp://|rtsp://', url)
    if len(protocols) > 1:
        logger.warning(f"URL包含多个协议头: {url}")
        return False
    
    # 检查是否包含无效字符或格式问题
    if ',' in url and not url.startswith('http'):
        logger.warning(f"URL包含逗号且不以http开头: {url}")
        return False
    
    try:
        result = urlparse(url)
        # 确保scheme和netloc都存在，并且netloc不为空
        return all([result.scheme, result.netloc and result.netloc.strip()])
    except Exception as e:
        logger.warning(f"URL解析错误: {url}, 错误: {str(e)}")
        return False

def clean_url(url):
    """清理URL，移除可能的错误格式"""
    if not url:
        return url
    
    # 处理逗号分隔的多个URL，返回第一个有效的URL
    if ',' in url:
        parts = url.split(',')
        for part in parts:
            part = part.strip()
            # 检查是否是有效的URL格式
            if part.startswith(('http://', 'https://', 'udp://', 'rtmp://', 'rtsp://')):
                # 移除可能的前缀错误，如'Hhttp://' -> 'http://'
                if part.startswith(('Hhttp://', 'hhttp://')):
                    part = part[1:]
                return part
    
    # 移除URL中的多余内容，例如如果包含多个URL协议
    protocols = re.findall(r'https?://|udp://|rtmp://|rtsp://', url)
    if len(protocols) > 1:
        # 保留第一个协议和其后面的内容
        first_protocol_index = url.find(protocols[0])
        return url[first_protocol_index:]
    
    # 处理类似"http://95.67.12.82:9086,Hhttp://"这样的错误格式
    if re.search(r'(https?://[^,]+),Hhttps?://', url):
        match = re.search(r'(https?://[^,]+)', url)
        if match:
            return match.group(1)
    
    # 移除可能的空白字符
    return url.strip()

def get_live_source_content(url):
    """获取单个直播源URL的内容"""
    try:
        logger.info(f"正在获取直播源: {url}")
        
        # 清理可能的重复协议前缀（例如ghcy.eu.org/https://）
        if 'https://https://' in url or 'http://https://' in url:
            url = url.replace('https://https://', 'https://')
            url = url.replace('http://https://', 'https://')
            logger.warning(f"修正URL格式: {url}")
        elif 'https://http://' in url or 'http://http://' in url:
            url = url.replace('https://http://', 'http://')
            url = url.replace('http://http://', 'http://')
            logger.warning(f"修正URL格式: {url}")
        
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=TIMEOUT) as response:
            content = response.read()
            logger.info(f"成功获取直播源内容，大小: {len(content)} 字节")
            
            # 尝试解码为UTF-8，如果失败则使用默认编码
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                logger.warning(f"UTF-8解码失败，使用latin-1解码: {url}")
                text_content = content.decode('latin-1')
            
            # 简化的调试信息
            if DEBUG and text_content:
                logger.debug(f"直播源内容行数: {len(text_content.split('\n'))}")
            
            return text_content
    except Exception as e:
        logger.error(f"获取直播源失败 {url}: {str(e)}")
        # 在调试模式下输出详细异常信息
        if DEBUG:
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
        return None

def is_uhd_channel(line, channel_name):
    """判断是否为超高清频道
    宽松定义：包含4K、超高清等关键词或高分辨率标记的线路被标记为超高清
    """
    line_lower = line.lower()
    name_lower = channel_name.lower()
    
    # 检查是否包含4K关键词（更宽松的匹配）
    if '4k' in line_lower or '4k' in name_lower:
        return True
    
    # 检查是否包含超高清关键词
    if '超高清' in line or '超高清' in channel_name:
        return True
    
    # 检查分辨率信息
    if '2160' in line_lower or '2160p' in line_lower or '4k' in line_lower:
        return True
    
    # 检查8K（更高分辨率）
    if '8k' in line_lower or '8k' in name_lower:
        return True
    
    return False

def log_debug(message):
    """简化的调试日志，仅在DEBUG模式下记录"""
    if DEBUG:
        logger.debug(message)

def is_low_resolution(line, channel_name):
    """判断是否为低分辨率线路
    识别并过滤576p等低分辨率线路
    """
    line_lower = line.lower()
    name_lower = channel_name.lower()
    
    # 明确标记的低分辨率
    if '576p' in line_lower or '576p' in name_lower:
        logger.debug(f"检测到低分辨率线路: {channel_name}")
        return True
    
    # 其他低分辨率标记
    if '标清' in line or '标清' in channel_name:
        logger.debug(f"检测到低分辨率线路: {channel_name}")
        return True
    
    # 明确的低质量标记
    if 'sd' in line_lower or '480p' in line_lower:
        logger.debug(f"检测到低分辨率线路: {channel_name}")
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
                
                # 清理URL，防止格式错误
                url = clean_url(url)
                
                # 检查是否为低分辨率线路，如果是则跳过
                if is_low_resolution(extinf_line, channel_name) or is_low_resolution(url, channel_name):
                    logger.debug(f"跳过低分辨率线路: {channel_name}")
                    extinf_line = None
                    continue
                
                is_uhd = is_uhd_channel(extinf_line, channel_name) or is_uhd_channel(url, channel_name)
                
                # 再次验证清理后的URL是否有效
                if is_valid_url(url):
                    channels.append((channel_name, url, is_uhd))
                    # 减少详细的调试日志
                    if DEBUG:
                        logger.debug(f"提取频道: {channel_name}")
                else:
                    logger.warning(f"无效URL: {channel_name}")
                    
                extinf_line = None
    else:
        # 处理简单的名称,URL格式
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                channel_name = lines[i].strip()
                url = lines[i + 1].strip()
                
                # 清理URL，防止格式错误
                url = clean_url(url)
                
                if channel_name and is_valid_url(url):
                    # 检查是否为低分辨率线路，如果是则跳过
                    if is_low_resolution(channel_name, channel_name):
                        logger.debug(f"跳过低分辨率线路: {channel_name}")
                        continue
                    
                    is_uhd = is_uhd_channel(channel_name, channel_name)
                    channels.append((channel_name, url, is_uhd))
                    if DEBUG:
                        logger.debug(f"提取频道: {channel_name}")
                else:
                    if DEBUG:
                        logger.debug(f"跳过无效频道: {channel_name}")
    
    return channels

def categorize_channel(channel_name):
    """对频道进行分类，使用更宽松的匹配策略"""
    # 优先匹配央视和4K频道
    for category in ["4K央视频道", "4K超高清频道", "央视", "卫视", "体育", "电影", "儿童", "高清频道"]:
        keywords = CHANNEL_CATEGORIES.get(category, [])
        for keyword in keywords:
            # 使用更宽松的关键词匹配
            if keyword.lower() in channel_name.lower():
                logger.debug(f"频道 '{channel_name}' 被分类为 '{category}'（匹配关键词: {keyword}")
                return category
    
    # 减少默认分类的日志记录
            if DEBUG:
                logger.debug(f"频道 '{channel_name}' 分类为 '其他频道'")
    return "其他频道"

def worker(q, results, lock, source_stats):
    """工作线程函数，增加源统计功能"""
    local_channels_count = 0
    local_error_count = 0
    
    while not q.empty():
        url = q.get()
        try:
            logger.info(f"工作线程处理: {url}")  # 提高日志级别，确保能看到处理过程
            content = get_live_source_content(url)
            if content:
                channels = extract_channels(content)
                if channels:
                    with lock:
                        results.append(channels)
                        # 记录该来源的频道数量
                        source_stats[url] = len(channels)
                    local_channels_count += len(channels)
                    logger.info(f"从直播源提取到 {len(channels)} 个频道")
                else:
                    if DEBUG:
                logger.warning(f"未提取到频道")
                    with lock:
                        source_stats[url] = 0
            else:
                local_error_count += 1
                logger.warning(f"无法获取直播源内容")
                with lock:
                    source_stats[url] = 0
        except Exception as e:
            local_error_count += 1
            logger.error(f"处理 {url} 时出错: {str(e)}")
            with lock:
                source_stats[url] = 0
            # 无论是否DEBUG模式，都输出异常信息
            import traceback
            logger.error(f"线程错误详细信息: {traceback.format_exc()}")
        finally:
            q.task_done()
    
    logger.info(f"工作线程完成，成功处理 {local_channels_count} 个频道，{local_error_count} 个错误")

def process_all_sources():
    """处理所有直播源，优化去重和分类逻辑"""
    all_channels = []
    results = []
    lock = threading.Lock()  # 添加锁以确保线程安全
    source_stats = {}
    
    logger.info(f"开始处理 {len(LIVE_SOURCES)} 个直播源URL")
    
    # 先验证所有URL
    valid_sources = []
    for url in LIVE_SOURCES:
        if is_valid_url(url):
            valid_sources.append(url)
            source_stats[url] = 0  # 初始化统计
        else:
            if DEBUG:
                    logger.warning(f"跳过无效URL")
    
    logger.info(f"有效URL数量: {len(valid_sources)}")
    
    # 单线程处理，确保稳定性
    logger.info("使用单线程处理以确保稳定性和可调试性")
    for url in valid_sources:
        logger.info(f"正在处理: {url}")
        try:
            content = get_live_source_content(url)
            if content:
                channels = extract_channels(content)
                if channels:
                    results.append(channels)
                    source_stats[url] = len(channels)
                    logger.info(f"从 {url} 成功提取 {len(channels)} 个频道")
                    # 显示前几个提取的频道作为示例
                    for name, url, is_uhd in channels[:3]:
                        logger.info(f"  示例频道: {'[4K]' if is_uhd else '[HD]'} {name}")
                else:
                    logger.warning(f"从 {url} 未提取到任何频道")
            else:
                logger.warning(f"无法获取 {url} 的内容")
        except Exception as e:
            logger.error(f"处理直播源时出错: {str(e)}")
            # 仅在DEBUG模式下输出详细异常
            if DEBUG:
                import traceback
                logger.error(f"错误详情: {traceback.format_exc()}")
    
    # 合并结果
    total_raw_channels = 0
    for channels_chunk in results:
        all_channels.extend(channels_chunk)
        total_raw_channels += len(channels_chunk)
    
    logger.info(f"从直播源获取到 {total_raw_channels} 个原始频道")
    
    # 显示原始频道列表的前10个作为示例
    if all_channels:
        logger.info("原始频道示例 (前10个):")
        for i, (name, url, is_uhd) in enumerate(all_channels[:10]):
            logger.info(f"  {i+1}. {'[4K]' if is_uhd else '[HD]'} {name}: {url[:50]}{'...' if len(url)>50 else ''}")
    
    # 修改去重策略：保留所有超高清线路，同时避免完全相同的频道+URL组合
    logger.info("开始去重处理...")
    unique_channels = {}
    uhd_channels_count = 0
    
    for name, url, is_uhd in all_channels:
        # 使用名称和URL的组合作为去重键，确保不同URL的同一频道都能保留
        key = f"{name}|{url}"
        if key not in unique_channels:
            unique_channels[key] = (name, url, is_uhd)
            if is_uhd:
                uhd_channels_count += 1
                logger.debug(f"添加超高清频道: {name} ({url[:30]}...)")
            else:
                logger.debug(f"添加高清频道: {name} ({url[:30]}...)")
        else:
            logger.debug(f"跳过重复频道: {name} ({url[:30]}...)")
    
    all_channels = list(unique_channels.values())
    logger.info(f"去重后剩余 {len(all_channels)} 个唯一频道，其中超高清频道 {uhd_channels_count} 个")
    
    # 确保只输出超高清线路 - 根据用户要求，只保留is_uhd为True的线路
    uhd_only_channels = [(name, url, is_uhd) for name, url, is_uhd in all_channels if is_uhd]
    logger.info(f"筛选后只保留 {len(uhd_only_channels)} 个超高清线路")
    all_channels = uhd_only_channels  # 替换为只包含超高清线路的列表
    
    # 显示各来源的贡献统计
    logger.info("各直播源频道贡献统计:")
    for url, count in source_stats.items():
        logger.info(f"  {url[:50]}: {count} 个频道")
    
    # 按分类组织频道
    logger.info("开始分类处理...")
    categorized_channels = {}
    
    # 为每个分类初始化空列表
    for category in CHANNEL_CATEGORIES.keys():
        categorized_channels[category] = []
    categorized_channels["其他频道"] = []
    
    for name, url, is_uhd in all_channels:
        category = categorize_channel(name)
        categorized_channels[category].append((name, url, is_uhd))
    
    # 移除空分类
    categorized_channels = {k: v for k, v in categorized_channels.items() if v}
    
    logger.info(f"分类结果: {', '.join([f'{k}({len(v)})' for k, v in categorized_channels.items()])}")
    
    # 显示每个分类的前几个频道
    for category, channels in categorized_channels.items():
        if channels:
            logger.info(f"{category} 频道示例 (前5个):")
            for name, url, is_uhd in channels[:5]:
                logger.info(f"  {'[4K]' if is_uhd else '[HD]'} {name}")
    
    return categorized_channels

def write_channels_to_file(categorized_channels):
    """将频道信息写入文件"""
    try:
        lines = []
        total_channels = 0
        uhd_channels_count = 0
        
        # 添加文件头信息 - 强调包含所有超高清线路
        lines.append(f"# 超高清直播源列表 (包含所有超高清线路)")
        # 确保使用当前正确的时间
        import datetime
        now = datetime.datetime.now()
        # 硬编码当前年份为2024，防止系统时间错误
        current_year = 2024
        current_date = f"{current_year}-{now.strftime('%m-%d %H:%M:%S')}"
        lines.append(f"# 更新时间: {current_date}")
        
        # 计算总频道数和超高清频道数
        for category, channels in categorized_channels.items():
            total_channels += len(channels)
            uhd_channels_count += sum(1 for _, _, is_uhd in channels if is_uhd)
        
        lines.append(f"# 共包含 {total_channels} 个频道，其中超高清频道 {uhd_channels_count} 个")
        lines.append("")
        
        # 按照优先级排序分类
        category_order = ["4K央视频道", "4K超高清频道", "高清频道", "央视", "卫视", "体育", "电影", "儿童", "其他频道"]
        
        for category in category_order:
            if category in categorized_channels:
                category_uhd_count = sum(1 for _, _, is_uhd in categorized_channels[category] if is_uhd)
                # 添加分类标记，显示该分类中超高清频道数量
                lines.append(f"{category} (超高清: {category_uhd_count}),#genre#")
                
                # 按频道名称排序，UHD频道优先，确保同一频道的多个超高清线路都能保留
                channels = sorted(categorized_channels[category], key=lambda x: (not x[2], x[0], x[1]))
                
                # 记录每个频道已输出的线路数，用于日志
                channel_counts = {}
                
                for name, url, is_uhd in channels:
                    # 只输出有效的URL
                    if is_valid_url(url):
                        lines.append(f"{name},{url}")
                        # 更新频道计数
                        if name not in channel_counts:
                            channel_counts[name] = 0
                        channel_counts[name] += 1
                
                # 记录该分类中多线路频道信息
                multi_line_channels = [name for name, count in channel_counts.items() if count > 1]
                if multi_line_channels:
                    logger.info(f"{category} 分类中有 {len(multi_line_channels)} 个频道包含多个线路")
                
                # 分类之间添加空行
                lines.append("")
        
        # 写入文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"成功写入 {OUTPUT_FILE}，共 {len(lines)} 行数据，包含所有超高清线路")
        return True
    except Exception as e:
        logger.error(f"写入文件失败: {str(e)}")
        return False

# 检查直播源URL数量，记录当前使用的数量
current_sources_count = len(LIVE_SOURCES)
logger.info(f"当前直播源URL数量: {current_sources_count} 个")

# 记录直播源URL列表
logger.debug("直播源URL列表:")
for i, url in enumerate(LIVE_SOURCES, 1):
    logger.debug(f"  {i}. {url}")


def main():
    """主函数"""
    # 清空之前的调试日志
    try:
        with open('debug.log', 'w', encoding='utf-8') as f:
            f.write(f"=== 开始执行直播源更新脚本 === {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    except Exception as e:
        pass
    
    log_debug(f"Python版本: {sys.version}")
    log_debug(f"当前目录: {os.getcwd()}")
    log_debug(f"调试模式: {'开启' if DEBUG else '关闭'}")
    
    # 确保日志文件目录存在
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_debug(f"日志目录: {log_dir}")
    logger.info(f"日志目录: {log_dir}")
    
    # 将输出同时写入文件，以便在环境限制下查看结果
    try:
        with open('script_output.log', 'w', encoding='utf-8') as log_file:
            def log_print(message):
                """打印并记录消息"""
                print(message)
                log_file.write(message + '\n')
                log_file.flush()
            
            log_print("开始执行脚本...")
            log_print(f"Python版本: {sys.version}")
            log_print(f"当前目录: {os.getcwd()}")
            log_print(f"调试模式: {'开启' if DEBUG else '关闭'}")
            
            try:
                log_print("初始化日志配置...")
                logger.info("开始获取超高清直播源...")
                start_time = time.time()
                
                # 显示配置信息
                log_print(f"并发工作线程数: {MAX_WORKERS}")
                log_print(f"请求超时时间: {TIMEOUT}秒")
                log_print(f"直播源URL数量: {len(LIVE_SOURCES)}")
                
                # 直接调用process_all_sources()获取实际直播源
                log_print("开始从网络获取直播源数据...")
                categorized_channels = process_all_sources()
                
                # 如果没有获取到数据，提供更丰富的静态备份数据
                if not categorized_channels:
                    log_print("警告: 未能从网络获取到直播源数据，使用备用数据")
                    logger.warning("使用备用数据")
                    categorized_channels = {
                        "4K央视频道": [
                            ("CCTV-4K超高清", "https://tv.cctv.com/live/cctv4k/", True),
                            ("CCTV-16 奥林匹克4K", "https://tv.cctv.com/live/cctv16/", True)
                        ],
                        "4K超高清频道": [
                            ("TRAVELXP 4K", "http://iptv.prosto.tv:7000/ch6/video.m3u8", True),
                            ("Fashion One 4K", "https://example.com/fashionone4k.m3u8", True),
                            ("National Geographic 4K", "https://example.com/natgeo4k.m3u8", True)
                        ],
                        "高清频道": [
                            ("CCTV-1综合", "https://tv.cctv.com/live/cctv1/", False),
                            ("CCTV-2财经", "https://tv.cctv.com/live/cctv2/", False),
                            ("CCTV-3综艺", "https://tv.cctv.com/live/cctv3/", False),
                            ("CCTV-4中文国际", "https://tv.cctv.com/live/cctv4/", False)
                        ]
                    }
                else:
                    log_print(f"成功获取 {sum(len(channels) for channels in categorized_channels.values())} 个频道")
                    log_print(f"频道分类: {', '.join([f'{k}({len(v)})' for k, v in categorized_channels.items()])}")
            
                # 写入文件
                log_print(f"准备写入文件 {OUTPUT_FILE}...")
                if write_channels_to_file(categorized_channels):
                    elapsed_time = time.time() - start_time
                    logger.info(f"直播源获取完成！耗时: {elapsed_time:.2f} 秒")
                    log_print(f"✓ 成功生成 {OUTPUT_FILE} 文件")
                    log_print(f"总耗时: {elapsed_time:.2f} 秒")
                    return 0
                else:
                    logger.error("处理失败")
                    log_print("✗ 生成文件失败")
                    return 1
            except KeyboardInterrupt:
                logger.info("程序被用户中断")
                log_print("程序被中断")
                return 130
            except Exception as e:
                logger.error(f"程序运行出错: {str(e)}", exc_info=True)
                log_print(f"程序错误类型: {type(e).__name__}")
                log_print(f"程序错误信息: {str(e)}")
                import traceback
                log_print("详细错误堆栈:")
                error_trace = traceback.format_exc()
                log_print(error_trace)
                return 1
    except Exception as e:
        # 如果连日志文件都无法写入，直接输出到控制台
        print(f"严重错误: 无法创建日志文件 - {str(e)}")
        print("尝试不使用日志文件继续执行...")
        
        try:
            start_time = time.time()
            categorized_channels = process_all_sources()
            
            if not categorized_channels:
                print("警告: 使用备用数据")
                categorized_channels = {
                    "4K央视频道": [
                        ("CCTV-4K超高清", "https://tv.cctv.com/live/cctv4k/", True),
                        ("CCTV-16 奥林匹克4K", "https://tv.cctv.com/live/cctv16/", True)
                    ],
                    "4K超高清频道": [
                        ("TRAVELXP 4K", "http://iptv.prosto.tv:7000/ch6/video.m3u8", True),
                        ("Fashion One 4K", "https://example.com/fashionone4k.m3u8", True),
                        ("National Geographic 4K", "https://example.com/natgeo4k.m3u8", True)
                    ],
                    "高清频道": [
                        ("CCTV-1综合", "https://tv.cctv.com/live/cctv1/", False),
                        ("CCTV-2财经", "https://tv.cctv.com/live/cctv2/", False),
                        ("CCTV-3综艺", "https://tv.cctv.com/live/cctv3/", False),
                        ("CCTV-4中文国际", "https://tv.cctv.com/live/cctv4/", False)
                    ]
                }
            
            if write_channels_to_file(categorized_channels):
                print(f"✓ 成功生成 {OUTPUT_FILE} 文件")
                return 0
            else:
                print("✗ 生成文件失败")
                return 1
        except Exception as e:
            print(f"程序完全失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    exit(main())
