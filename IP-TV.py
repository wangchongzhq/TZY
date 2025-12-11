#!/usr/bin/env python3
"""
IPTV直播源自动生成工具
功能：从多个来源获取IPTV直播源并生成M3U文件
support：手动更新和通过GitHub Actions工作流定时更新
"""

import asyncio
import os
import re
import time
import requests
import datetime

from collections import defaultdict
from dataclasses import dataclass
from typing import List, Tuple, Optional

# 延迟导入aiohttp以避免不必要的依赖
import aiohttp

# 导入核心模块
from core.logging_config import get_logger, setup_logging
from core.config import get_config
from core.network import fetch_multiple
from core.file_utils import write_file
from core.epg_handler import EPGHandler

# 初始化EPG处理
logger = get_logger(__name__)
epg_handler = EPGHandler()
epg_handler.load_epg_data()

# 输出目录 - 全局变量
OUTPUT_DIR = "output"

# 确保输出文件包含正确的输出目录的函数
def ensure_output_dir(file_path):
    """确保文件路径包含输出目录，并创建目录（如果不存在）"""
    # 特定文件例外：这些文件应直接放在根目录
    root_files = ['jieguo.m3u', 'jieguo.txt']
    
    if not os.path.dirname(file_path):  # 如果没有目录部分
        # 如果是例外文件，保持在根目录
        if os.path.basename(file_path) in root_files:
            pass  # 不修改路径
        else:
            file_path = os.path.join(OUTPUT_DIR, file_path)
    
    # 确保输出目录存在
    output_dir = os.path.dirname(file_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    return file_path

# 测速配置类
class SpeedTestConfig:
    CONCURRENT_LIMIT = 20  # 并发限制
    TIMEOUT = 10  # 超时时间（秒）
    RETRY_TIMES = 3  # 重试次数
    OUTPUT_DIR = "output"  # 输出目录

# 数据类
@dataclass
class SpeedTestResult:
    url: str
    latency: Optional[float] = None  # 延迟（毫秒）
    resolution: Optional[str] = None  # 分辨率
    bitrate: Optional[int] = None  # 码率（Kbps）
    content_type: Optional[str] = None  # 内容类型
    success: bool = False  # 是否成功
    error: Optional[str] = None  # 错误信息
    test_time: float = 0  # 测试时间戳

# 速度测试工具类
class SpeedTester:
    def __init__(self):
        self.session = None
        self.logger = get_logger(__name__)
    
    async def __aenter__(self):
        import aiohttp
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=SpeedTestConfig.TIMEOUT))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def extract_resolution_from_m3u8(self, url: str) -> Optional[str]:
        """从m3u8文件中提取分辨率信息"""
        try:
            async with self.session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                if response.status == 200:
                    content = await response.text()
                    # 查找EXT-X-STREAM-INF标签，通常包含分辨率信息
                    stream_inf_pattern = r"#EXT-X-STREAM-INF:.*?RESOLUTION=(\d+x\d+).*?(\S+)"
                    matches = re.findall(stream_inf_pattern, content, re.MULTILINE | re.DOTALL)
                    if matches:
                        # 返回第一个流的分辨率
                        return matches[0][0]
            return None
        except Exception as e:
            self.logger.warning(f"解析m3u8分辨率失败: {e}")
            return None
    
    async def measure_latency(self, url: str, retry_times: int = 3) -> SpeedTestResult:
        """测量单个URL的延迟、分辨率、码率等指标"""
        result = SpeedTestResult(url=url, test_time=time.time())
        
        for attempt in range(retry_times):
            try:
                start_time = time.time()
                async with self.session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=SpeedTestConfig.TIMEOUT)) as response:
                    if response.status == 200:
                        # 测量响应时间作为延迟
                        latency = (time.time() - start_time) * 1000  # 转换为毫秒
                        
                        # 提取内容类型
                        content_type = response.headers.get("Content-Type", "")
                        
                        # 提取分辨率
                        resolution = None
                        if "application/vnd.apple.mpegurl" in content_type or url.endswith(".m3u8"):
                            # 对于m3u8文件，解析获取分辨率
                            resolution = await self.extract_resolution_from_m3u8(url)
                        elif "video" in content_type:
                            # 尝试从响应头获取内容长度
                            content_length = response.headers.get("Content-Length")
                            if content_length:
                                # 视频流可能没有分辨率信息，标记为流
                                resolution = "stream"
                        
                        # 提取码率信息（如果可用）
                        bitrate = None
                        if "video" in content_type:
                            # 尝试从响应头获取码率（有些服务器会提供）
                            bitrate_header = response.headers.get("X-Content-Bitrate")
                            if bitrate_header:
                                bitrate = int(bitrate_header) // 1000  # 转换为Kbps
                        
                        result.latency = latency
                        result.resolution = resolution
                        result.bitrate = bitrate
                        result.content_type = content_type
                        result.success = True
                        self.logger.info(f"URL: {url} 测试成功，延迟: {latency:.2f}ms, 分辨率: {resolution or 'unknown'}")
                        break
                    else:
                        result.error = f"HTTP状态码: {response.status}"
            except Exception as e:
                result.error = str(e)
                self.logger.warning(f"URL: {url} 尝试 {attempt+1}/{retry_times} 失败: {e}")
                await asyncio.sleep(1)  # 重试前等待1秒
        
        return result
    
    async def batch_speed_test(self, urls: List[str], show_progress: bool = False) -> List[SpeedTestResult]:
        """批量测速（带并发控制和进度显示）"""
        results = []
        semaphore = asyncio.Semaphore(SpeedTestConfig.CONCURRENT_LIMIT)

        async def worker(url):
            async with semaphore:
                result = await self.measure_latency(url, SpeedTestConfig.RETRY_TIMES)
                results.append(result)

        tasks = [worker(url) for url in urls]
        
        # 执行任务，根据参数决定是否显示进度
        if show_progress:
            try:
                from tqdm.asyncio import tqdm_asyncio
                await tqdm_asyncio.gather(*tasks, total=len(urls), desc="测速中", unit="url")
            except ImportError:
                await asyncio.gather(*tasks)
        else:
            await asyncio.gather(*tasks)
        
        # 按延迟排序结果（升序）
        return sorted(results, key=lambda x: x.latency if x.latency is not None else float('inf'))

# M3U文件处理类
class M3UProcessor:
    @staticmethod
    def parse_m3u(file_path: str) -> List[Tuple[str, str]]:
        """解析M3U文件，返回[(名称, URL), ...]"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            live_sources = []
            current_name = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('#EXTINF:'):
                    # 提取名称
                    name_start = line.find(',') + 1
                    current_name = line[name_start:] if name_start > 0 else "未知频道"
                elif line.startswith('http') and current_name:
                    # 添加到源列表
                    live_sources.append((current_name, line))
                    current_name = None
            
            return live_sources
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"解析M3U文件失败: {e}")
            return []
    
    @staticmethod
    def generate_m3u(live_sources: List[Tuple[str, str]], output_path: str) -> None:
        """生成M3U文件"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                for name, url in live_sources:
                    f.write(f'#EXTINF:-1,{name}\n')
                    f.write(f'{url}\n')
            
            logger.info(f"已生成M3U文件: {output_path}")
        except Exception as e:
            logger.error(f"生成M3U文件失败: {e}")

# 设置日志
setup_logging()
logger = get_logger(__name__)

# 默认频道分类
DEFAULT_CHANNEL_CATEGORIES = {
    "4K频道": ['CCTV4K', 'CCTV8K', 'CCTV16 4K', '北京卫视4K', '北京IPTV4K', '湖南卫视4K', '山东卫视4K','广东卫视4K', '四川卫视4K', '浙江卫视4K', '江苏卫视4K', '东方卫视4K', '深圳卫视4K', '河北卫视4K', '峨眉电影4K', '求索4K', '咪视界4K', '欢笑剧场4K', '苏州4K', '至臻视界4K', '南国都市4K', '翡翠台4K', '百事通电影4K', '百事通少儿4K', '百事通纪实4K', '华数爱上4K'],

    "央视频道": ['CCTV1', 'CCTV2', 'CCTV3', 'CCTV4', 'CCTV4欧洲', 'CCTV4美洲', 'CCTV5', 'CCTV5+', 'CCTV6', 'CCTV7', 'CCTV8', 'CCTV9', 'CCTV10', 'CCTV11', 'CCTV12', 'CCTV13', 'CCTV14', 'CCTV15', 'CCTV16', 'CCTV17', 'CETV1', 'CETV2', 'CETV3', 'CETV4', '早期教育','兵器科技', '风云音乐', '风云足球', '风云剧场', '怀旧剧场', '第一剧场', '女性时尚', '世界地理', '央视台球', '高尔夫网球', '央视文化精品', '卫生健康','电视指南'],

    "卫视频道": ['山东卫视', '浙江卫视', '江苏卫视', '东方卫视', '深圳卫视', '北京卫视', '广东卫视', '广西卫视', '东南卫视', '海南卫视', '河北卫视', '河南卫视', '湖北卫视', '江西卫视', '四川卫视', '重庆卫视', '贵州卫视', '云南卫视', '天津卫视', '安徽卫视', '湖南卫视', '辽宁卫视', '黑龙江卫视', '吉林卫视', '内蒙古卫视', '宁夏卫视', '山西卫视', '陕西卫视', '甘肃卫视', '青海卫视', '新疆卫视', '西藏卫视', '三沙卫视', '厦门卫视', '兵团卫视', '延边卫视', '安多卫视', '康巴卫视', '农林卫视', '山东教育'],

    "北京专属频道": ['北京卫视', '北京财经', '北京纪实', '北京生活', '北京体育休闲', '北京国际', '北京文艺', '北京新闻', '北京淘电影', '北京淘剧场', '北京淘4K', '北京淘娱乐', '北京淘BABY', '北京萌宠TV', '北京卡酷少儿'],

    "山东专属频道": ['山东卫视', '山东齐鲁', '山东综艺', '山东少儿', '山东生活',
                 '山东新闻', '山东国际', '山东体育', '山东文旅', '山东农科'],

    "港澳频道": ['凤凰中文', '凤凰资讯', '凤凰香港', '凤凰电影'],

    "电影频道": ['CHC动作电影', 'CHC家庭影院', 'CHC影迷电影', '淘电影',
                 '淘精彩', '淘剧场', '星空卫视', '黑莓电影', '东北热剧',
                 '中国功夫', '动作电影', '超级电影'],

    "儿童频道": ['动漫秀场', '哒啵电竞', '黑莓动画', '卡酷少儿',
                 '金鹰卡通', '优漫卡通', '哈哈炫动', '嘉佳卡通'],

    "iHOT频道": ['iHOT爱喜剧', 'iHOT爱科幻', 'iHOT爱院线', 'iHOT爱悬疑', 'iHOT爱历史', 'iHOT爱谍战', 'iHOT爱旅行', 'iHOT爱幼教', 'iHOT爱玩具', 'iHOT爱体育', 'iHOT爱赛车', 'iHOT爱浪漫', 'iHOT爱奇谈', 'iHOT爱科学', 'iHOT爱动漫'],

    "综合频道": ['重温经典', 'CHANNEL[V]', '求索纪录', '求索科学', '求索生活', '求索动物', '睛彩青少', '睛彩竞技', '睛彩篮球', '睛彩广场舞', '金鹰纪实', '快乐垂钓', '茶频道', '军事评论', '军旅剧场', '乐游', '生活时尚', '都市剧场', '欢笑剧场', '游戏风云', '金色学堂', '法治天地', '哒啵赛事'],

    "体育频道": ['天元围棋', '魅力足球', '五星体育', '劲爆体育', '超级体育'],
    
    "剧场频道": ['古装剧场', '家庭剧场', '惊悚悬疑', '明星大片', '欢乐剧场', '海外剧场', '潮妈辣婆',
                 '爱情喜剧', '超级电视剧', '超级综艺', '金牌综艺', '武搏世界', '农业致富', '炫舞未来',
                 '精品体育', '精品大剧', '精品纪录', '精品萌宠', '怡伴健康'],
    
    "音乐频道": ['CCTV音乐', '音乐Tai', '音乐台', 'MTV', 'MTV中文', '华语音乐', '流行音乐', '古典音乐'],
}

# 频道分类：从config.json中读取并与默认值合并
CHANNEL_CATEGORIES = get_config('channels.categories', {})

# 合并默认分类和配置分类，确保所有分类都能应用
merged_categories = DEFAULT_CHANNEL_CATEGORIES.copy()
if CHANNEL_CATEGORIES:
    # 如果配置中存在分类，则合并它们
    for category_name, channels in CHANNEL_CATEGORIES.items():
        if category_name in merged_categories:
            # 如果分类已存在，合并频道列表（去重）
            merged_categories[category_name] = list(set(merged_categories[category_name] + channels))
        else:
            # 如果是新分类，直接添加
            merged_categories[category_name] = channels

# 使用合并后的分类
CHANNEL_CATEGORIES = merged_categories

# 频道映射（别名 -> 规范名）
CHANNEL_MAPPING = {
    # 4K频道
    "CCTV4K": ["CCTV 4K", "CCTV-4K超高清頻道", "CCTV4K超高清頻道", "CCTV-4K"],
    "CCTV8K": ["CCTV 8K", "CCTV-8K超高清頻道", "CCTV8K超高清頻道", "CCTV-8K"],
    "CCTV16 4K": ["CCTV16 4K", "CCTV16-4K", "CCTV16 奥林匹克 4K", "CCTV16奥林匹克 4K"],
    "北京卫视4K": ["北京卫视 4K", "北京卫视4K超高清", "北京卫视-4K"],
    "北京IPTV4K": ["北京IPTV 4K", "北京IPTV-4K"],
    "湖南卫视4K": ["湖南卫视 4K", "湖南卫视-4K"],
    "山东卫视4K": ["山东卫视 4K", "山东卫视-4K"],
    "广东卫视4K": ["广东卫视 4K", "广东卫视-4K"],
    "四川卫视4K": ["四川卫视 4K", "四川卫视-4K"],
    "浙江卫视4K": ["浙江卫视 4K", "浙江卫视-4K"],
    "江苏卫视4K": ["江苏卫视 4K", "江苏卫视-4K"],
    "东方卫视4K": ["东方卫视 4K", "东方卫视-4K"],
    "深圳卫视4K": ["深圳卫视 4K", "深圳卫视-4K"],
    "河北卫视4K": ["河北卫视 4K", "河北卫视-4K"],
    "峨眉电影4K": ["峨眉电影 4K", "峨眉电影-4K"],
    "求索4K": ["求索 4K", "求索-4K"],
    "咪视界4K": ["咪视界 4K", "咪视界-4K"],
    "欢笑剧场4K": ["欢笑剧场 4K", "欢笑剧场-4K"],
    "苏州4K": ["苏州 4K", "苏州-4K"],
    "至臻视界4K": ["至臻视界 4K", "至臻视界-4K"],
    "南国都市4K": ["南国都市 4K", "南国都市-4K"],
    "翡翠台4K": ["翡翠台 4K", "翡翠台-4K"],
    "百事通电影4K": ["百事通电影 4K", "百事通电影-4K"],
    "百事通少儿4K": ["百事通少儿 4K", "百事通少儿-4K"],
    "百事通纪实4K": ["百事通纪实 4K", "百事通纪实-4K"],
    "华数爱上4K": ["华数爱上 4K", "爱上 4K", "爱上4K",  "爱上-4K", "华数爱上-4K"],
    
    # 央视频道
    "CCTV1": ["CCTV-1", "CCTV-1 HD", "CCTV1综合", "CCTV-1 综合"],
    "CCTV2": ["CCTV-2", "CCTV-2 HD", "CCTV2 财经", "CCTV-2 财经"],
    "CCTV3": ["CCTV-3", "CCTV-3 HD", "CCTV3 综艺", "CCTV-3 综艺"],
    "CCTV4": ["CCTV-4", "CCTV-4 HD", "CCTV4 中文国际", "CCTV-4 中文国际"],
    "CCTV4欧洲": ["CCTV-4欧洲", "CCTV-4欧洲 HD", "CCTV-4 欧洲", "CCTV-4 中文欧洲", "CCTV4中文欧洲"],
    "CCTV4美洲": ["CCTV-4美洲", "CCTV-4美洲 HD", "CCTV-4 美洲", "CCTV-4 中文美洲", "CCTV4中文美洲"],
    "CCTV5": ["CCTV-5", "CCTV-5 HD", "CCTV5 体育", "CCTV-5 体育"],
    "CCTV5+": ["CCTV-5+", "CCTV-5+ HD", "CCTV5+ 体育赛事", "CCTV-5+ 体育赛事"],
    "CCTV6": ["CCTV-6", "CCTV-6 HD", "CCTV6 电影", "CCTV-6 电影"],
    "CCTV7": ["CCTV-7", "CCTV-7 HD", "CCTV7 国防军事", "CCTV-7 国防军事"],
    "CCTV8": ["CCTV-8", "CCTV-8 HD", "CCTV8 电视剧", "CCTV-8 电视剧"],
    "CCTV9": ["CCTV-9", "CCTV-9 HD", "CCTV9 纪录", "CCTV-9 纪录"],
    "CCTV10": ["CCTV-10", "CCTV-10 HD", "CCTV10 科教", "CCTV-10 科教"],
    "CCTV11": ["CCTV-11", "CCTV-11 HD", "CCTV11 戏曲", "CCTV-11 戏曲"],
    "CCTV12": ["CCTV-12", "CCTV-12 HD", "CCTV12 社会与法", "CCTV-12 社会与法"],
    "CCTV13": ["CCTV-13", "CCTV-13 HD", "CCTV13 新闻", "CCTV-13 新闻"],
    "CCTV14": ["CCTV-14", "CCTV-14 HD", "CCTV14 少儿", "CCTV-14 少儿"],
    "CCTV15": ["CCTV-15", "CCTV-15 HD", "CCTV15 音乐", "CCTV-15 音乐"],
    "CCTV16": ["CCTV-16", "CCTV-16 HD", "CCTV-16 奥林匹克", "CCTV16 奥林匹克"],
    "CCTV17": ["CCTV-17", "CCTV-17 HD", "CCTV17 农业农村", "CCTV-17 农业农村"],
    "CETV1": ["CETV-1", "中国教育1", "中国教育台1"],
    "CETV2": ["CETV-2", "中国教育2", "中国教育台2"],
    "CETV3": ["CETV-3", "中国教育3", "中国教育台3"],
    "CETV4": ["CETV-4", "中国教育4", "中国教育台4"],
    "早期教育": ["CETV-早期教育", "中国教育台-早期教育"],
    "兵器科技": ["CCTV-兵器科技", "CCTV兵器科技"],
    "风云音乐": ["CCTV-风云音乐", "CCTV风云音乐"],
    "风云足球": ["CCTV-风云足球", "CCTV风云足球"],
    "风云剧场": ["CCTV-风云剧场", "CCTV风云剧场"],
    "怀旧剧场": ["CCTV-怀旧剧场", "CCTV怀旧剧场"],
    "第一剧场": ["CCTV-第一剧场", "CCTV第一剧场"],
    "女性时尚": ["CCTV-女性时尚", "CCTV女性时尚"],
    "世界地理": ["CCTV-世界地理", "CCTV世界地理"],
    "央视台球": ["CCTV-央视台球", "CCTV央视台球"],
    "高尔夫网球": ["CCTV-高尔夫网球", "CCTV高尔夫网球"],
    "央视文化精品": ["CCTV-央视文化精品", "CCTV央视文化精品"],
    "卫生健康": ["CCTV-卫生健康", "CCTV卫生健康"],
    "电视指南": ["CCTV-电视指南", "CCTV电视指南"],
    
    # 卫视频道
    "山东卫视": ["山东卫视 HD", "山东台", "山东卫视高清"],
    "浙江卫视": ["浙江卫视 HD", "浙江台", "浙江卫视高清"],
    "江苏卫视": ["江苏卫视 HD", "江苏台", "江苏卫视高清"],
    "东方卫视": ["东方卫视 HD", "东方台", "上海东方卫视", "东方卫视高清"],
    "深圳卫视": ["深圳卫视 HD", "深圳台", "深圳卫视高清"],
    "北京卫视": ["北京卫视 HD", "北京台", "北京卫视高清"],
    "广东卫视": ["广东卫视 HD", "广东台", "广东卫视高清"],
    "广西卫视": ["广西卫视 HD", "广西台", "广西卫视高清"],
    "东南卫视": ["东南卫视 HD", "东南台", "福建东南卫视", "东南卫视高清"],
    "海南卫视": ["海南卫视 HD", "海南台", "海南卫视高清"],
    "河北卫视": ["河北卫视 HD", "河北台", "河北卫视高清"],
    "河南卫视": ["河南卫视 HD", "河南台", "河南卫视高清"],
    "湖北卫视": ["湖北卫视 HD", "湖北台", "湖北卫视高清"],
    "江西卫视": ["江西卫视 HD", "江西台", "江西卫视高清"],
    "四川卫视": ["四川卫视 HD", "四川台", "四川卫视高清"],
    "重庆卫视": ["重庆卫视 HD", "重庆台", "重庆卫视高清"],
    "贵州卫视": ["贵州卫视 HD", "贵州台", "贵州卫视高清"],
    "云南卫视": ["云南卫视 HD", "云南台", "云南卫视高清"],
    "天津卫视": ["天津卫视 HD", "天津台", "天津卫视高清"],
    "安徽卫视": ["安徽卫视 HD", "安徽台", "安徽卫视高清"],
    "湖南卫视": ["湖南卫视 HD", "湖南台", "湖南卫视高清"],
    "辽宁卫视": ["辽宁卫视 HD", "辽宁台", "辽宁卫视高清"],
    "黑龙江卫视": ["黑龙江卫视 HD", "黑龙江台", "黑龙江卫视高清"],
    "吉林卫视": ["吉林卫视 HD", "吉林台", "吉林卫视高清"],
    "内蒙古卫视": ["内蒙古卫视 HD", "内蒙古台", "内蒙古卫视高清"],
    "宁夏卫视": ["宁夏卫视 HD", "宁夏台", "宁夏卫视高清"],
    "山西卫视": ["山西卫视 HD", "山西台", "山西卫视高清"],
    "陕西卫视": ["陕西卫视 HD", "陕西台", "陕西卫视高清"],
    "甘肃卫视": ["甘肃卫视 HD", "甘肃台", "甘肃卫视高清"],
    "青海卫视": ["青海卫视 HD", "青海台", "青海卫视高清"],
    "新疆卫视": ["新疆卫视 HD", "新疆台", "新疆卫视高清"],
    "西藏卫视": ["西藏卫视 HD", "西藏台", "西藏卫视高清"],
    "三沙卫视": ["三沙卫视 HD", "三沙台", "三沙卫视高清"],
    "厦门卫视": ["厦门卫视 HD", "厦门台", "厦门卫视高清"],
    "兵团卫视": ["兵团卫视 HD", "兵团台", "兵团卫视高清"],
    "延边卫视": ["延边卫视 HD", "延边台", "延边卫视高清"],
    "安多卫视": ["安多卫视 HD", "安多台", "安多卫视高清"],
    "康巴卫视": ["康巴卫视 HD", "康巴台", "康巴卫视高清"],
    "农林卫视": ["农林卫视 HD", "农林台", "农林卫视高清"],
    "山东教育": ["山东教育台", "山东教育卫视"],
    
    # 音乐频道
    "CCTV音乐": ["CCTV-音乐", "CCTV 音乐"],
    "音乐Tai": ["音乐Tai", "音乐台"],
    "音乐台": ["音乐台 HD", "音乐台HD"],
    "MTV": ["MTV", "音乐电视"],
    "MTV中文": ["MTV中文", "中文MTV"],
    "华语音乐": ["华语音乐", "华语"],
    "流行音乐": ["流行音乐", "流行"],
    "古典音乐": ["古典音乐", "古典"]
 }

# 默认直播源URL
# 从统一播放源文件导入
try:
    from unified_sources import UNIFIED_SOURCES
    default_sources = UNIFIED_SOURCES
    logger.info(f"✅ 成功从unified_sources.py导入 {len(default_sources)} 个播放源")
except ImportError as e:
    logger.error(f"❌ 导入unified_sources.py失败: {e}")
    # 如果导入失败，使用一些默认的播放源
    default_sources = [
        "https://gitee.com/xiao-ping2/iptv-api/raw/master/output/xp_result.txt",
        "https://cdn.jsdelivr.net/gh/Guovin/iptv-api@gd/output/result.txt"
    ]
    logger.info(f"⚠️ 使用默认播放源列表，共 {len(default_sources)} 个播放源")

# 本地直播源文件
default_local_sources = []

# 用户自定义直播源URL（可在本地添加）
user_sources = []

# 格式化时间间隔
def format_interval(seconds):
    """格式化时间间隔"""
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes)}分{int(seconds)}秒"
    else:
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}时{int(minutes)}分{int(seconds)}秒"



# 检查IPv6支持
def check_ipv6_support():
    """检查系统是否支持IPv6"""
    try:
        import socket
        socket.inet_pton(socket.AF_INET6, '::1')
        return True
    except:
        return False

# 判断是否为IPv6地址
def is_ipv6(url):
    """通过判断URL中是否包含'['来区分IPv6地址"""
    return '[' in url

# 从M3U文件中提取频道信息
def extract_channels_from_m3u(content):
    """从M3U内容中提取频道信息"""
    channels = defaultdict(list)
    
    # 使用core/parser.py中的解析函数来获取完整的频道信息，包括group-title
    from core.parser import parse_m3u_content
    channel_infos = parse_m3u_content(content)
    
    for channel_info in channel_infos:
        try:
            channel_name = channel_info.name
            url = channel_info.url
            group = channel_info.group
            
            # 检查URL是否应该被排除
            if should_exclude_url(url, channel_name):
                continue
            
            # 检查频道名称或group是否包含4K/8K标识
            is_4k_channel = ('4K' in channel_name or '4k' in channel_name or '8K' in channel_name or '8k' in channel_name or 
                           '4K' in group or '4k' in group or '8K' in group or '8k' in group)
            
            # 规范化频道名称
            normalized_name = normalize_channel_name(channel_name)
            if normalized_name:
                # 获取频道分类
                category = get_channel_category(normalized_name)
                # 如果是4K频道，强制放在4K频道分类
                if is_4k_channel:
                    category = "4K频道"
                channels[category].append((normalized_name, url))
            else:
                # 未规范化的频道，如果是4K/8K频道，放在4K频道分类
                if is_4k_channel:
                    channels["4K频道"].append((channel_name, url))
                else:
                    channels["其他频道"].append((channel_name, url))
                    
        except Exception as e:
            logger.error(f"处理频道信息时出错: {e}")
            continue
    
    return channels

# 创建反向映射（频道 -> 分类）以提高查找效率
CHANNEL_TO_CATEGORY = {}
for category, channels in CHANNEL_CATEGORIES.items():
    for channel in channels:
        CHANNEL_TO_CATEGORY[channel] = category

# 调试信息：打印分类配置
print("===== 频道分类配置调试信息 =====")
print(f"加载的分类数量: {len(CHANNEL_CATEGORIES)}")
print(f"分类名称: {list(CHANNEL_CATEGORIES.keys())}")
print(f"总频道数: {len(CHANNEL_TO_CATEGORY)}")
print("前5个分类及示例频道:")
for i, (category, channels) in enumerate(list(CHANNEL_CATEGORIES.items())[:5]):
    print(f"  {i+1}. {category}: {channels[:3]}...")
print("==============================")

# 获取频道分类
def get_channel_category(channel_name):
    """获取频道所属的分类"""
    # 1. 首先检查是否包含4K/8K，优先归类为4K频道
    if '4K' in channel_name or '4k' in channel_name or '8K' in channel_name or '8k' in channel_name:
        return "4K频道"
    
    # 2. 如果不是4K频道，使用反向映射直接查找
    category = CHANNEL_TO_CATEGORY.get(channel_name, None)
    if category:
        return category
    
    # 3. 未匹配到任何分类，返回其他频道
    return "其他频道"

# 创建反向映射（别名 -> 标准名）以提高查找效率
ALIAS_TO_STANDARD = {}
for standard_name, aliases in CHANNEL_MAPPING.items():
    ALIAS_TO_STANDARD[standard_name] = standard_name  # 标准名映射到自身
    for alias in aliases:
        ALIAS_TO_STANDARD[alias] = standard_name  # 别名映射到标准名

# 规范化频道名称
def normalize_channel_name(name):
    """将频道名称规范化为标准名称"""
    name = name.strip()
    
    # 如果名称为空，直接返回None
    if not name:
        return None
    
    # 检查是否包含4K/8K标识
    has_4k = '4K' in name or '4k' in name or '8K' in name or '8k' in name
    
    # 1. 直接匹配
    if name in ALIAS_TO_STANDARD:
        # 如果原始名称包含4K/8K，确保返回的标准名称也包含4K/8K
        if has_4k:
            standard_name = ALIAS_TO_STANDARD[name]
            # 检查标准名称是否包含4K/8K
            if '4K' in standard_name or '4k' in standard_name or '8K' in standard_name or '8k' in standard_name:
                return standard_name
        return ALIAS_TO_STANDARD[name]
    
    # 2. 去除括号内容
    name_without_brackets = re.sub(r'\s*\([^)]*\)\s*', ' ', name)
    if name_without_brackets.strip() in ALIAS_TO_STANDARD:
        # 如果原始名称包含4K/8K，需要特殊处理
        if has_4k:
            base_name = ALIAS_TO_STANDARD[name_without_brackets.strip()]
            # 检查是否有对应的4K版本标准名称
            for standard_name in CHANNEL_MAPPING:
                if base_name in standard_name and ('4K' in standard_name or '8K' in standard_name):
                    return standard_name
        return ALIAS_TO_STANDARD[name_without_brackets.strip()]
    
    # 3. 去除额外描述（如"超高清"、"高清"、"2160p"等）
    name_without_desc = re.sub(r'(超高清|高清|2160p|1080p|720p|480p|标清)\s*$', '', name_without_brackets, flags=re.IGNORECASE)
    if name_without_desc.strip() in ALIAS_TO_STANDARD:
        # 如果原始名称包含4K/8K，需要特殊处理
        if has_4k:
            base_name = ALIAS_TO_STANDARD[name_without_desc.strip()]
            # 检查是否有对应的4K版本标准名称
            for standard_name in CHANNEL_MAPPING:
                if base_name in standard_name and ('4K' in standard_name or '8K' in standard_name):
                    return standard_name
        return ALIAS_TO_STANDARD[name_without_desc.strip()]
    
    # 3.1 特殊处理4K/8K频道：如果包含4K/8K，尝试匹配
    processed_name = name_without_desc.strip()
    if has_4k or '4K' in processed_name or '4k' in processed_name or '8K' in processed_name or '8k' in processed_name:
        # 检查是否与CHANNEL_MAPPING中的4K/8K标准名称匹配
        for standard_name in CHANNEL_MAPPING:
            if '4K' in standard_name or '8K' in standard_name:
                # 不区分大小写的包含关系匹配
                if standard_name.lower() in processed_name.lower() or processed_name.lower() in standard_name.lower():
                    return standard_name
        # 如果没有匹配到标准名称，直接返回处理后的名称（包含4K/8K信息）
        return processed_name
    
    # 4. 尝试使用部分匹配（对于常见的4K频道）
    # 先检查是否包含4K/8K
    if '4K' in name or '4k' in name or '8K' in name or '8k' in name:
        # 提取包含4K/8K的部分
        match = re.search(r'([^\s]+4K[^\s]*)|([^\s]+8K[^\s]*)', name, re.IGNORECASE)
        if match:
            partial_name = match.group(0)
            # 检查是否与标准名称匹配
            for standard_name in CHANNEL_MAPPING:
                # 检查标准名称是否在partial_name中，或者partial_name是否在标准名称中
                if standard_name.lower() in partial_name.lower() or partial_name.lower() in standard_name.lower():
                    return standard_name
                # 检查别名
                for alias in CHANNEL_MAPPING[standard_name]:
                    if alias.lower() in partial_name.lower() or partial_name.lower() in alias.lower():
                        return standard_name
            # 如果没有匹配到标准名称，直接返回提取的部分
            return partial_name
    
    # 5. 全部大写尝试
    name_upper = name_without_brackets.strip().upper()
    for standard_name, aliases in CHANNEL_MAPPING.items():
        if standard_name.upper() in name_upper:
            return standard_name
        for alias in aliases:
            if alias.upper() in name_upper:
                return standard_name
    
    # 6. 检查是否包含4K/8K，如果包含且无法匹配，返回一个基于4K/8K的名称（如"CCTV4K"）
    if '4K' in name or '4k' in name or '8K' in name or '8k' in name:
        # 尝试提取频道的主要部分
        main_part = re.sub(r'\s*[0-9]+p|\s*超高清|\s*高清|\s*超清|\s*UHD', '', name, flags=re.IGNORECASE)
        main_part = main_part.strip()
        if main_part:
            return main_part
        # 如果提取失败，直接返回原始名称
        return name
    
    # 7. 无法匹配，返回None
    return None

# 从URL获取M3U内容
def fetch_m3u_content(url):
    """从URL获取M3U内容"""
    try:
        print(f"正在获取: {url}")
        # 添加verify=False参数来跳过SSL证书验证
        response = requests.get(url, timeout=30, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"获取 {url} 时出错: {e}")
        return None

# 从本地文件获取M3U内容
def fetch_local_m3u_content(file_path):
    """从本地文件获取M3U内容"""
    try:
        print(f"正在读取本地文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取本地文件 {file_path} 时出错: {e}")
        return None

# 检查是否应该排除购物频道和测试频道
def should_exclude_channel(name):
    """检查是否应该排除购物频道和测试频道"""
    try:
        # 排除购物相关频道
        shopping_keywords = ['购物', '导购', '电视购物', '商城', '易购', '优购', '家购', 
                             '购享', '购彩', '购物车', '购物频道', '时尚购', '快乐购', 
                             '好享购', '东方购物', '环球购物', '风尚购物', '居家购物', 
                             '优购物', '电视商城', '直播购物']
        
        # 排除测试相关频道
        test_keywords = ['测试', 'test']
        
        # 检查购物关键词
        for keyword in shopping_keywords:
            if keyword in name:
                return True
        
        # 检查测试关键词
        for keyword in test_keywords:
            if keyword in name:
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"检查频道是否应该排除时发生错误: {e}")
        return False

# 检查是否应该排除该URL
def should_exclude_url(url, channel_name=''):
    """检查是否应该排除该URL
    排除规则：
    1. 包含example.com的URL
    2. 包含demo、sample、samples的URL
    3. 分辨率低于最小要求的URL
    """
    try:
        if not url or not isinstance(url, str):
            return True
            
        # 定义需要排除的模式
        exclude_patterns = [
            r'example\.com',  # 排除example.com域名
            r'demo',
            r'sample',
            r'samples',
            r'accountinfo',  # 排除带有认证信息的URL
            r'GuardEncType',  # 排除带有加密类型参数的URL
            r'AuthInfo'       # 排除带有认证信息的URL
        ]
        
        # 检查是否匹配任何排除模式
        for pattern in exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        # 检查分辨率是否满足要求
        from core.channel_utils import should_exclude_resolution
        from core.config import config_manager
        
        # 获取所有配置
        config = config_manager.get_all()
        # 从配置中获取最小分辨率要求
        min_resolution = config.get('quality', {}).get('min_resolution', '1920x1080')
        
        # 检查是否开启分辨率过滤
        open_filter_resolution = config.get('quality', {}).get('open_filter_resolution', True)
        
        if open_filter_resolution:
            if should_exclude_resolution(url, channel_name, min_resolution):
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"检查URL是否应该排除时发生错误: {e}")
        return False  # 发生错误时不排除频道，避免误过滤

# 过滤频道
def filter_channels(channels):
    """过滤频道列表
    1. 排除购物频道
    2. 排除CCTV数字超过17的频道
    3. 排除测试URL和低分辨率URL
    """
    try:
        from core.channel_utils import ChannelInfo
        
        # 调试信息：打印输入频道数量
        logger.info(f"过滤前频道组数: {len(channels)}, 总频道数: {sum(len(chans) for group, chans in channels.items())}")
        
        # 将channels转换为ChannelInfo列表以便使用channel_utils.py中的filter_channels函数
        channel_info_list = []
        for category, channel_list in channels.items():
            for channel_name, url in channel_list:
                channel_info_list.append(ChannelInfo(name=channel_name, url=url, group=category))
        
        # 调试信息：打印转换后的ChannelInfo数量
        logger.info(f"转换为ChannelInfo后的数量: {len(channel_info_list)}")
        
        # 自定义过滤函数
        def custom_filter(channel):
            # 检查是否应该排除购物频道
            if should_exclude_channel(channel.name):
                return False
                
            # 检查CCTV频道数字是否超过17
            cctv_match = re.match(r'^CCTV[- ]?(\d+)', channel.name, re.IGNORECASE)
            if cctv_match:
                cctv_number = int(cctv_match.group(1))
                if cctv_number > 17:
                    return False
                    
            # 检查是否应该排除该URL
            if should_exclude_url(channel.url, channel.name):
                return False
                
            return True
        
        # 使用channel_utils.py中的filter_channels函数
        from core.channel_utils import filter_channels as utils_filter_channels
        filtered_channel_infos = utils_filter_channels(channel_info_list, custom_filter=custom_filter)
        
        # 调试信息：打印过滤后的ChannelInfo数量
        logger.info(f"过滤后ChannelInfo的数量: {len(filtered_channel_infos)}")
        
        # 将过滤后的ChannelInfo列表转换回原来的格式
        filtered_channels = defaultdict(list)
        for channel_info in filtered_channel_infos:
            filtered_channels[channel_info.group].append((channel_info.name, channel_info.url))
        
        # 调试信息：打印最终过滤后的频道数量
        logger.info(f"最终过滤后频道组数: {len(filtered_channels)}, 总频道数: {sum(len(chans) for group, chans in filtered_channels.items())}")
        
        excluded_count = len(channel_info_list) - len(filtered_channel_infos)
        logger.info(f"过滤统计: 共排除 {excluded_count} 个频道")
        return filtered_channels
        
    except Exception as e:
        logger.error(f"过滤频道时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return channels

# 生成M3U文件
def generate_m3u_file(channels, output_path):
    """生成M3U文件，包含EPG和台标信息"""
    print(f"正在生成 {output_path}...")
    
    # 从配置中获取EPG源
    epg_config = get_config("epg", {})
    epg_sources = epg_config.get("sources", [])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入文件头，包含EPG源信息
        if epg_sources:
            # 写入第一个EPG源作为tvg-url
            f.write(f"#EXTM3U tvg-url=\"{epg_sources[0]}\"\n")
        else:
            f.write("#EXTM3U\n")
        
        # 按CHANNEL_CATEGORIES中定义的顺序写入分类
        for category in CHANNEL_CATEGORIES:
            if category in channels:
                for channel_name, url in channels[category]:
                    # 获取频道的台标信息
                    logo_url = epg_handler.get_channel_logo(channel_name)
                    
                    # 构建EXTINF行
                    extinf_line = f"#EXTINF:-1 group-title=\"{category}\""
                    
                    # 添加EPG和台标信息
                    if channel_name:
                        extinf_line += f" tvg-id=\"{channel_name}\" tvg-name=\"{channel_name}\""
                    if logo_url:
                        extinf_line += f" tvg-logo=\"{logo_url}\""
                    
                    # 完成EXTINF行
                    extinf_line += f",{channel_name}\n"
                    
                    # 写入频道信息
                    f.write(extinf_line)
                    f.write(f"{url}\n")
        
        # 最后写入其他频道
        if "其他频道" in channels:
            for channel_name, url in channels["其他频道"]:
                # 获取频道的台标信息
                logo_url = epg_handler.get_channel_logo(channel_name)
                
                # 构建EXTINF行
                extinf_line = f"#EXTINF:-1 group-title=\"其他频道\""
                
                # 添加EPG和台标信息
                if channel_name:
                    extinf_line += f" tvg-id=\"{channel_name}\" tvg-name=\"{channel_name}\""
                if logo_url:
                    extinf_line += f" tvg-logo=\"{logo_url}\""
                
                # 完成EXTINF行
                extinf_line += f",{channel_name}\n"
                
                # 写入频道信息
                f.write(extinf_line)
                f.write(f"{url}\n")
    
    print(f"✅ 成功生成 {output_path}")
    return True

# 生成TXT文件
def generate_txt_file(channels, output_path):
    """生成TXT文件"""
    logger.info(f"正在生成 {output_path}...")
    
    # 生成文件内容
    content_lines = []
    
    # 写入文件头注释
    content_lines.append("# IPTV直播源列表")
    content_lines.append(f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content_lines.append("# 格式: 频道名称,播放URL")
    content_lines.append("# 按分组排列")
    content_lines.append("")
    
    # 写入频道分类说明
    content_lines.append("# 频道分类: 4K频道,央视频道,卫视频道,北京专属频道,山东专属频道,港澳频道,电影频道,儿童频道,iHOT频道,综合频道,体育频道,剧场频道,其他频道")
    content_lines.append("")
    
    # 按照要求的固定顺序输出频道分类
    required_order = [
        "4K频道", "央视频道", "卫视频道", "北京专属频道", "山东专属频道", 
        "港澳频道", "电影频道", "儿童频道", "iHOT频道", "综合频道", 
        "体育频道", "剧场频道", "其他频道"
    ]
    
    # 按要求的顺序写入分类
    for category in required_order:
        if category in channels and channels[category]:
            # 写入分组标题，添加,genre#后缀
            content_lines.append(f"#{category}#,genre#")
            
            # 写入该分组下的所有频道
            for channel_name, url in channels[category]:
                content_lines.append(f"{channel_name},{url}")
            
            # 分组之间添加空行
            content_lines.append("")
    
    # 使用核心模块写入文件
    content = '\n'.join(content_lines)
    if write_file(output_path, content):
        logger.info(f"✅ 成功生成 {output_path}")
        return True
    else:
        logger.error(f"❌ 生成 {output_path} 失败")
        return False

# 从本地TXT文件提取频道信息
def extract_channels_from_txt_content(content):
    """从TXT格式的内容字符串中提取频道信息，支持分类行"""
    channels = defaultdict(list)
    current_category = "其他频道"
    
    try:
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 处理分类行（如"🇨🇳 4K,#genre#"）
            if line.endswith(',#genre#') or line.endswith(',genre#'):
                # 提取分类名称
                category_name = line.split(',')[0].strip()
                # 检查是否为4K分类
                if '4K' in category_name or '4k' in category_name or '8K' in category_name or '8k' in category_name:
                    current_category = "4K频道"
                else:
                    current_category = "其他频道"
                continue
            
            # 解析频道信息（格式：频道名称,URL）
            if ',' in line:
                channel_name, url = line.split(',', 1)
                channel_name = channel_name.strip()
                url = url.strip()
                
                # 跳过无效的URL
                if not url.startswith(('http://', 'https://')):
                    continue
                
                # 检查URL是否应该被排除
                if should_exclude_url(url, channel_name):
                    continue
                
                # 检查频道名称是否包含4K/8K，无论是否规范化成功
                is_4k_channel = '4K' in channel_name or '4k' in channel_name or '8K' in channel_name or '8k' in channel_name
                
                # 规范化频道名称
                normalized_name = normalize_channel_name(channel_name)
                if normalized_name:
                    # 获取频道分类
                    category = get_channel_category(normalized_name)
                    # 如果是4K频道，强制放在4K频道分类
                    if is_4k_channel or current_category == "4K频道":
                        category = "4K频道"
                    channels[category].append((normalized_name, url))
                else:
                    # 未规范化的频道，如果是4K/8K频道或当前分类是4K频道，放在4K频道分类
                    if is_4k_channel or current_category == "4K频道":
                        channels["4K频道"].append((channel_name, url))
                    else:
                        channels[current_category].append((channel_name, url))
    except Exception as e:
        logger.error(f"解析TXT内容时出错: {e}")
    
    return channels


def extract_channels_from_txt(file_path):
    """从本地TXT文件提取频道信息"""
    channels = defaultdict(list)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        channels = extract_channels_from_txt_content(content)
    except Exception as e:
        print(f"解析本地文件 {file_path} 时出错: {e}")
    
    return channels

# 合并直播源
def merge_sources(sources, local_files):
    """合并多个直播源，返回包含IPv4和IPv6的分离频道以及合并的频道"""
    all_channels = defaultdict(list)
    
    # 使用核心模块的fetch_multiple实现并发获取远程直播源
    logger.info(f"📡 正在并发获取{len(sources)}个远程直播源...")
    results = fetch_multiple(sources, timeout=30, verify=False)
    
    # 处理远程直播源结果
    failed_sources = []
    for url, content in results.items():
        if content:
            # 根据内容格式选择合适的解析函数
            if content.strip().startswith('#EXTM3U'):
                # 标准M3U格式
                channels = extract_channels_from_m3u(content)
            else:
                # 自定义TXT格式
                channels = extract_channels_from_txt_content(content)
            
            ipv6_count = sum(1 for group, chans in channels.items() for name, u in chans if is_ipv6(u))
            logger.info(f"从 {url} 获取到 {sum(len(chans) for group, chans in channels.items())} 个频道，其中IPv6频道: {ipv6_count}个")
            for group_title, channel_list in channels.items():
                all_channels[group_title].extend(channel_list)
        else:
            logger.error(f"❌ 无法获取直播源: {url}")
            failed_sources.append(url)
    
    # 输出失败的直播源信息
    if failed_sources:
        logger.warning(f"⚠️  共有 {len(failed_sources)} 个直播源读取失败:")
        for url in failed_sources:
            logger.warning(f"  - {url}")
    
    # 从配置文件获取输出文件名，避免将输出文件作为输入文件处理
    output_config = get_config('output', {})
    output_file_m3u_all = output_config.get('m3u_file', output_config.get('m3u_filename', "jieguo.m3u"))
    output_file_txt_all = output_config.get('txt_file', output_config.get('txt_filename', "jieguo.txt"))
    
    # 应用输出目录
    output_file_m3u_all = ensure_output_dir(output_file_m3u_all)
    output_file_txt_all = ensure_output_dir(output_file_txt_all)
    
    # 生成所有可能的输出文件名
    output_files = [output_file_m3u_all, output_file_txt_all]
    output_files.append(output_file_m3u_all.replace('.m3u', '_i4.m3u'))
    output_files.append(output_file_txt_all.replace('.txt', '_i4.txt'))
    output_files.append(output_file_m3u_all.replace('.m3u', '_i6.m3u'))
    output_files.append(output_file_txt_all.replace('.txt', '_i6.txt'))
    
    # 处理本地直播源文件
    logger.info(f"💻 正在读取{len(local_files)}个本地直播源文件...")
    for file_path in local_files:
        # 检查是否是输出文件，如果是则跳过
        file_name = os.path.basename(file_path)
        if file_name in output_files:
            logger.warning(f"⚠️  跳过输出文件: {file_path}")
            continue
            
        if os.path.exists(file_path):
            # 根据文件扩展名选择解析函数
            if file_path.lower().endswith('.m3u'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                local_channels = extract_channels_from_m3u(content)
            else:
                local_channels = extract_channels_from_txt(file_path)
            
            for group_title, channel_list in local_channels.items():
                all_channels[group_title].extend(channel_list)
        else:
            logger.warning(f"⚠️  本地直播源文件不存在: {file_path}")
    
    # 对所有频道进行去重处理
    deduplicated_channels = defaultdict(list)
    deduplicated_channels_ipv4 = defaultdict(list)
    deduplicated_channels_ipv6 = defaultdict(list)
    seen = set()
    
    for group_title, channel_list in all_channels.items():
        for channel_name, url in channel_list:
            if (channel_name, url) not in seen:
                # 添加到合并频道
                deduplicated_channels[group_title].append((channel_name, url))
                
                # 根据IP类型分离
                if is_ipv6(url):
                    deduplicated_channels_ipv6[group_title].append((channel_name, url))
                else:
                    deduplicated_channels_ipv4[group_title].append((channel_name, url))
                
                seen.add((channel_name, url))
    
    # 统计去重后的IPv6频道数量
    total_ipv6_after_dedup = sum(len(chans) for group, chans in deduplicated_channels_ipv6.items())
    logger.info(f"去重后共得到 {total_ipv6_after_dedup} 个IPv6频道")
    
    # 返回分离后的频道和合并频道
    return {
        'all': deduplicated_channels,
        'ipv4': deduplicated_channels_ipv4,
        'ipv6': deduplicated_channels_ipv6
    }


# 忽略requests的SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def update_iptv_sources():
    """更新IPTV直播源"""
    logger.info("🚀 IPTV直播源自动生成工具")
    logger.info(f"📅 运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    # 合并所有直播源
    all_sources = default_sources + user_sources
    logger.info(f"📡 正在获取{len(all_sources)}个远程直播源...")
    
    # 从配置文件加载本地源
    local_sources_enabled = get_config('local_sources.enabled', True)
    local_sources_files = get_config('local_sources.files', [])
    
    # 合并本地源：默认本地源 + 配置文件中的本地源
    combined_local_sources = default_local_sources.copy()
    if local_sources_enabled and local_sources_files:
        combined_local_sources.extend(local_sources_files)
    
    # 去重本地源
    combined_local_sources = list(set(combined_local_sources))
    
    # 过滤掉不存在的本地源文件
    existing_local_sources = []
    for file_path in combined_local_sources:
        if os.path.exists(file_path):
            existing_local_sources.append(file_path)
        else:
            logger.warning(f"⚠️  本地直播源文件不存在: {file_path}")
    
    logger.info(f"正在读取{len(existing_local_sources)}个本地直播源文件...")
    
    start_time = time.time()
    channels_data = merge_sources(all_sources, existing_local_sources)
    
    # 统计过滤前的频道数量
    logger.info(f"过滤前 - 合并频道: {sum(len(chans) for group, chans in channels_data['all'].items())} 个")
    logger.info(f"过滤前 - IPv4频道: {sum(len(chans) for group, chans in channels_data['ipv4'].items())} 个")
    logger.info(f"过滤前 - IPv6频道: {sum(len(chans) for group, chans in channels_data['ipv6'].items())} 个")
    
    # 过滤各个版本的频道
    print("\n===== 调试信息: 开始过滤频道 =====")
    before_all = sum(len(chans) for group, chans in channels_data['all'].items())
    before_ipv4 = sum(len(chans) for group, chans in channels_data['ipv4'].items())
    before_ipv6 = sum(len(chans) for group, chans in channels_data['ipv6'].items())
    print(f"过滤前 - 合并频道: {before_all} 个")
    print(f"过滤前 - IPv4频道: {before_ipv4} 个")
    print(f"过滤前 - IPv6频道: {before_ipv6} 个")
    logger.info("开始过滤频道...")
    logger.info(f"过滤前 - 合并频道: {before_all} 个")
    logger.info(f"过滤前 - IPv4频道: {before_ipv4} 个")
    logger.info(f"过滤前 - IPv6频道: {before_ipv6} 个")
    
    filtered_channels_all = filter_channels(channels_data['all'])
    filtered_channels_ipv4 = filter_channels(channels_data['ipv4'])
    filtered_channels_ipv6 = filter_channels(channels_data['ipv6'])
    
    # 统计过滤后的频道数量
    all_count = sum(len(chans) for group, chans in filtered_channels_all.items())
    ipv4_count = sum(len(chans) for group, chans in filtered_channels_ipv4.items())
    ipv6_count = sum(len(chans) for group, chans in filtered_channels_ipv6.items())
    
    print(f"过滤后 - 合并频道: {all_count} 个")
    print(f"过滤后 - IPv4频道: {ipv4_count} 个")
    print(f"过滤后 - IPv6频道: {ipv6_count} 个")
    logger.info(f"过滤后 - 合并频道: {all_count} 个")
    logger.info(f"过滤后 - IPv4频道: {ipv4_count} 个")
    logger.info(f"过滤后 - IPv6频道: {ipv6_count} 个")
    print("===== 调试信息: 过滤频道完成 =====")
    
    # 检查过滤后的频道数据
    if all_count == 0:
        logger.error("过滤后没有合并频道数据！")
    else:
        logger.info("过滤后有合并频道数据")
        # 打印前几个频道
        for i, (category, chans) in enumerate(list(filtered_channels_all.items())[:3]):
            logger.info(f"   分类 {i+1}: {category} - {len(chans)} 个频道")
            for j, (name, url) in enumerate(chans[:2]):
                logger.info(f"      频道 {j+1}: {name} - {url[:50]}...")
    
    # 统计频道数量
    total_channels_all = sum(len(channel_list) for channel_list in filtered_channels_all.values())
    total_channels_ipv4 = sum(len(channel_list) for channel_list in filtered_channels_ipv4.values())
    total_channels_ipv6 = sum(len(channel_list) for channel_list in filtered_channels_ipv6.values())
    total_groups = len(filtered_channels_all)
    
    logger.info("=" * 50)
    logger.info("统计信息:")
    logger.info(f"直播源数量: {len(all_sources)}")
    logger.info(f"频道组数: {total_groups}")
    logger.info(f"总频道数(合并): {total_channels_all}")
    logger.info(f"IPv4频道数: {total_channels_ipv4}")
    logger.info(f"IPv6频道数: {total_channels_ipv6}")
    logger.info(f"耗时: {format_interval(time.time() - start_time)}")
    logger.info("=" * 50)
    
    # 生成所有版本的文件
    # 注意：output_config已经在上面获取过，这里不需要重新获取
    
    def generate_files(channels, m3u_filename, txt_filename, version_name):
        """生成指定版本的M3U和TXT文件"""
        file_success = True
        
        print(f"\n生成{version_name}文件")
        print(f"   M3U文件: {m3u_filename}")
        print(f"   TXT文件: {txt_filename}")
        print(f"   频道数据: {sum(len(chans) for _, chans in channels.items())} 个频道，{len(channels)} 个分类")
        print(f"   文件路径是否存在: M3U={os.path.exists(os.path.dirname(m3u_filename)) if os.path.dirname(m3u_filename) else True}, TXT={os.path.exists(os.path.dirname(txt_filename)) if os.path.dirname(txt_filename) else True}")
        
        if channels:
            # 显示前3个分类及其前2个频道
            print(f"   前3个分类示例:")
            for i, (category, chans) in enumerate(list(channels.items())[:3]):
                print(f"     {category} - {len(chans)} 个频道")
                for j, (name, url) in enumerate(chans[:2]):
                    print(f"       {name}: {url[:50]}...")
        else:
            print(f"   频道数据为空！")
            return False
        
        # 生成M3U文件
        print(f"   正在生成M3U文件...")
        try:
            if generate_m3u_file(channels, m3u_filename):
                logger.info(f"成功生成{version_name}M3U文件: {m3u_filename}")
                print(f"   M3U文件生成成功")
                print(f"   M3U文件大小: {os.path.getsize(m3u_filename) if os.path.exists(m3u_filename) else 0} 字节")
            else:
                logger.error(f"生成{version_name}M3U文件失败: {m3u_filename}")
                print(f"   M3U文件生成失败")
                file_success = False
        except Exception as e:
            logger.error(f"生成{version_name}M3U文件时发生异常: {e}")
            print(f"   M3U文件生成时发生异常: {e}")
            file_success = False
        
        # 生成TXT文件
        print(f"   正在生成TXT文件...")
        try:
            if generate_txt_file(channels, txt_filename):
                logger.info(f"成功生成{version_name}TXT文件: {txt_filename}")
                print(f"   TXT文件生成成功")
                print(f"   TXT文件大小: {os.path.getsize(txt_filename) if os.path.exists(txt_filename) else 0} 字节")
            else:
                logger.error(f"生成{version_name}TXT文件失败: {txt_filename}")
                print(f"   TXT文件生成失败")
                file_success = False
        except Exception as e:
            logger.error(f"生成{version_name}TXT文件时发生异常: {e}")
            print(f"   TXT文件生成时发生异常: {e}")
            file_success = False
        
        print(f"   {version_name}文件生成完成 - 成功: {file_success}")
        return file_success
    
    # 合并版本
    output_file_m3u_all = output_config.get('m3u_file', output_config.get('m3u_filename', "jieguo.m3u"))
    output_file_txt_all = output_config.get('txt_file', output_config.get('txt_filename', "jieguo.txt"))
    
    # 应用输出目录
    output_file_m3u_all = ensure_output_dir(output_file_m3u_all)
    output_file_txt_all = ensure_output_dir(output_file_txt_all)
    
    # IPv4版本
    output_file_m3u_ipv4 = output_file_m3u_all.replace('.m3u', '_i4.m3u')
    output_file_txt_ipv4 = output_file_txt_all.replace('.txt', '_i4.txt')
    
    # IPv6版本
    output_file_m3u_ipv6 = output_file_m3u_all.replace('.m3u', '_i6.m3u')
    output_file_txt_ipv6 = output_file_txt_all.replace('.txt', '_i6.txt')
    
    # IPv4和IPv6合并版本（明确标识）
    output_file_m3u_merged = output_file_m3u_all.replace('.m3u', '_merged.m3u')
    output_file_txt_merged = output_file_txt_all.replace('.txt', '_merged.txt')
    
    # 兼容配置文件和工作流的文件名 - 生成ip-tv_前缀的版本
    output_dir = os.path.dirname(output_file_m3u_ipv4) or OUTPUT_DIR
    output_file_m3u_ipv4_compat = os.path.join(output_dir, "ip-tv_i4.m3u")
    output_file_txt_ipv4_compat = os.path.join(output_dir, "ip-tv_i4.txt")
    output_file_m3u_ipv6_compat = os.path.join(output_dir, "ip-tv_i6.m3u")
    output_file_txt_ipv6_compat = os.path.join(output_dir, "ip-tv_i6.txt")
    output_file_m3u_all_compat = os.path.join(output_dir, "ip-tv.m3u")
    output_file_txt_all_compat = os.path.join(output_dir, "ip-tv.txt")
    
    # 生成所有文件
    success = True
    print("\n===== 调试信息: 开始生成文件 =====")
    print(f"输出文件配置:")
    print(f"  合并版 M3U: {output_file_m3u_all}")
    print(f"  合并版 TXT: {output_file_txt_all}")
    print(f"  IPv4版 M3U: {output_file_m3u_ipv4}")
    print(f"  IPv4版 TXT: {output_file_txt_ipv4}")
    print(f"  IPv6版 M3U: {output_file_m3u_ipv6}")
    print(f"  IPv6版 TXT: {output_file_txt_ipv6}")
    print(f"  IPv4&IPv6合并版 M3U: {output_file_m3u_merged}")
    print(f"  IPv4&IPv6合并版 TXT: {output_file_txt_merged}")
    
    # 合并版本
    print(f"\n开始生成合并版文件...")
    logger.info(f"开始生成合并版文件 - M3U: {output_file_m3u_all}, TXT: {output_file_txt_all}")
    if not generate_files(filtered_channels_all, output_file_m3u_all, output_file_txt_all, "合并版"):
        logger.error("合并版文件生成失败")
        success = False
    else:
        logger.info("合并版文件生成成功")
        print("合并版文件生成成功")
    
    # IPv4版本
    print(f"\n开始生成IPv4版文件...")
    logger.info(f"开始生成IPv4版文件 - M3U: {output_file_m3u_ipv4}, TXT: {output_file_txt_ipv4}")
    if not generate_files(filtered_channels_ipv4, output_file_m3u_ipv4, output_file_txt_ipv4, "IPv4版"):
        logger.error("IPv4版文件生成失败")
        success = False
    else:
        logger.info("IPv4版文件生成成功")
        print("IPv4版文件生成成功")
    
    # IPv6版本
    print(f"\n开始生成IPv6版文件...")
    logger.info(f"开始生成IPv6版文件 - M3U: {output_file_m3u_ipv6}, TXT: {output_file_txt_ipv6}")
    if not generate_files(filtered_channels_ipv6, output_file_m3u_ipv6, output_file_txt_ipv6, "IPv6版"):
        logger.error("IPv6版文件生成失败")
        success = False
    else:
        logger.info("IPv6版文件生成成功")
        print("IPv6版文件生成成功")
    
    # IPv4和IPv6合并版本（明确标识）
    print(f"\n开始生成IPv4&IPv6合并版文件...")
    logger.info(f"开始生成IPv4&IPv6合并版文件 - M3U: {output_file_m3u_merged}, TXT: {output_file_txt_merged}")
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file_m3u_merged)
    if not os.path.exists(output_dir):
        print(f"输出目录不存在，正在创建: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
    
    # 简化的调试信息
    print(f"输出目录: {output_dir}")
    print(f"合并M3U文件: {os.path.basename(output_file_m3u_merged)}")
    print(f"合并TXT文件: {os.path.basename(output_file_txt_merged)}")
    print(f"频道总数: {sum(len(chans) for _, chans in filtered_channels_all.items())} 个")
    
    # 尝试直接生成文件
    try:
        # 先清理可能存在的旧文件
        if os.path.exists(output_file_m3u_merged):
            os.remove(output_file_m3u_merged)
            print("已清理旧的M3U文件")
        if os.path.exists(output_file_txt_merged):
            os.remove(output_file_txt_merged)
            print("已清理旧的TXT文件")
        
        # 生成M3U文件
        print(f"\n正在生成M3U文件...")
        m3u_success = generate_m3u_file(filtered_channels_all, output_file_m3u_merged)
        
        # 生成TXT文件
        print(f"正在生成TXT文件...")
        txt_success = generate_txt_file(filtered_channels_all, output_file_txt_merged)
        
        # 立即检查文件是否存在
        print(f"\n检查文件生成结果:")
        m3u_exists = os.path.exists(output_file_m3u_merged)
        txt_exists = os.path.exists(output_file_txt_merged)
        
        print(f"   M3U文件生成成功: {m3u_exists}")
        print(f"   TXT文件生成成功: {txt_exists}")
        
        if m3u_exists:
            print(f"   M3U文件大小: {os.path.getsize(output_file_m3u_merged)} 字节")
        if txt_exists:
            print(f"   TXT文件大小: {os.path.getsize(output_file_txt_merged)} 字节")
        
        if m3u_exists and txt_exists:
            logger.info("IPv4&IPv6合并版文件生成成功")
            print("IPv4&IPv6合并版文件生成成功")
        else:
            logger.error("IPv4&IPv6合并版文件生成失败")
            success = False
    except Exception as e:
        print(f"文件生成时发生异常: {e}")
        logger.error(f"直接生成IPv4&IPv6合并版文件时发生异常: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    # 生成兼容版本的文件（ip-tv_前缀）
    print(f"\n===== 生成兼容版本文件 =====")
    compat_success = True
    
    # 1. 合并版（ip-tv.m3u/ip-tv.txt）
    print(f"生成兼容合并版...")
    if os.path.exists(output_file_m3u_all):
        import shutil
        try:
            shutil.copy(output_file_m3u_all, output_file_m3u_all_compat)
            shutil.copy(output_file_txt_all, output_file_txt_all_compat)
            print(f"   成功生成: {os.path.basename(output_file_m3u_all_compat)}, {os.path.basename(output_file_txt_all_compat)}")
        except Exception as e:
            print(f"   生成兼容合并版失败: {e}")
            compat_success = False
    
    # 2. IPv4版本（ip-tv_i4.m3u/ip-tv_i4.txt）
    print(f"生成兼容IPv4版...")
    if os.path.exists(output_file_m3u_ipv4):
        try:
            shutil.copy(output_file_m3u_ipv4, output_file_m3u_ipv4_compat)
            shutil.copy(output_file_txt_ipv4, output_file_txt_ipv4_compat)
            print(f"   成功生成: {os.path.basename(output_file_m3u_ipv4_compat)}, {os.path.basename(output_file_txt_ipv4_compat)}")
        except Exception as e:
            print(f"   生成兼容IPv4版失败: {e}")
            compat_success = False
    
    # 3. IPv6版本（ip-tv_i6.m3u/ip-tv_i6.txt）
    print(f"生成兼容IPv6版...")
    if os.path.exists(output_file_m3u_ipv6):
        try:
            shutil.copy(output_file_m3u_ipv6, output_file_m3u_ipv6_compat)
            shutil.copy(output_file_txt_ipv6, output_file_txt_ipv6_compat)
            print(f"   成功生成: {os.path.basename(output_file_m3u_ipv6_compat)}, {os.path.basename(output_file_txt_ipv6_compat)}")
        except Exception as e:
            print(f"   生成兼容IPv6版失败: {e}")
            compat_success = False
    
    # 更新成功状态
    success = success and compat_success
    
    print(f"\n最终输出目录文件列表:")
    for file in os.listdir(output_dir):
        if file.endswith('.m3u') or file.endswith('.txt'):
            print(f"   - {file}")
    
    if success:
        logger.info("任务完成！")
        return True
    else:
        logger.error("部分文件生成失败！")
        return False


def check_ip_tv_syntax():
    """检查IP-TV.py文件的语法错误"""
    import ast
    
    # 尝试解析当前文件，获取更详细的错误信息
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析整个文件
        ast.parse(content)
        print('✓ IP-TV.py: 语法正确')
        return True
        
    except SyntaxError as e:
        print(f'✗ 语法错误: {e}')
        print(f'行号: {e.lineno}, 偏移量: {e.offset}')
        
        # 获取有问题的行
        lines = content.splitlines()
        if 0 <= e.lineno - 1 < len(lines):
            problem_line = lines[e.lineno - 1]
            print(f'问题行内容: {repr(problem_line)}')
            
            # 打印该行的十六进制表示
            print(f'问题行十六进制: {problem_line.encode("utf-8").hex()}')
            
            # 标记错误位置
            if 0 <= e.offset - 1 < len(problem_line):
                print('错误位置: ' + ' ' * (e.offset - 1) + '^')
        return False
        
    except Exception as e:
        print(f'✗ 其他错误: {type(e).__name__}: {e}')
        return False


def fix_ip_tv_chars():
    """修复IP-TV.py文件中的不可打印字符"""
    import re
    
    # 读取当前文件内容
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除所有不可打印字符，包括欧元符号和其他特殊字符
        # 保留ASCII可打印字符和常见的中文、日文、韩文等Unicode字符
        cleaned_content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f\u20ac\ue000-\uf8ff]', '', content)
        
        # 将清理后的内容写回文件
        with open(__file__, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print('✓ IP-TV.py文件中的不可打印字符已移除')
        return True
        
    except Exception as e:
        print(f'✗ 处理文件时出错: {type(e).__name__}: {e}')
        return False


async def run_speed_test(input_file, output_dir="output"):
    """
    运行测速功能的主函数
    参数:
        input_file: 输入M3U文件路径
        output_dir: 输出目录
    """
    logger = get_logger(__name__)
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 解析M3U文件
    logger.info(f"开始解析M3U文件: {input_file}")
    live_sources = M3UProcessor.parse_m3u(input_file)
    if not live_sources:
        logger.error("解析M3U文件失败或文件中没有直播源")
        return
    
    logger.info(f"成功解析 {len(live_sources)} 个直播源")
    
    # 2. 提取所有URL
    urls = [url for _, url in live_sources]
    total_urls = len(urls)
    
    # 3. 批量测速（带进度显示）
    logger.info("开始批量测速...")
    start_time = time.time()
    
    # 导入tqdm用于进度显示
    try:
        from tqdm.asyncio import tqdm_asyncio
        has_tqdm = True
    except ImportError:
        has_tqdm = False
        logger.warning("tqdm库未安装，将不显示进度条")
    
    async with SpeedTester() as tester:
        results = await tester.batch_speed_test(urls, show_progress=has_tqdm)
    
    elapsed_time = time.time() - start_time
    logger.info(f"测速完成，耗时: {elapsed_time:.2f}秒")
    
    # 4. 统计结果
    total = len(results)
    success = sum(1 for r in results if r.success)
    failed = total - success
    avg_latency = sum(r.latency for r in results if r.success) / success if success > 0 else 0
    
    logger.info(f"测速统计: 总直播源={total}, 成功={success}, 失败={failed}, 平均延迟={avg_latency:.2f}ms")
    
    # 5. 生成测速报告
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"speed_test_report_{timestamp}.txt")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== IPTV直播源测速报告 ===\n")
        f.write(f"测试时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"测试直播源总数: {total}\n")
        f.write(f"成功测试数: {success}\n")
        f.write(f"失败测试数: {failed}\n")
        f.write(f"平均延迟: {avg_latency:.2f}ms\n")
        f.write(f"测试耗时: {elapsed_time:.2f}秒\n")
        f.write("\n")
        f.write("=== 测试结果详情（按延迟升序排列） ===\n")
        
        # 创建URL到名称的映射
        url_to_name = {url: name for name, url in live_sources}
        
        for i, result in enumerate(results):
            name = url_to_name.get(result.url, "未知频道")
            status = "成功" if result.success else "失败"
            latency_str = f"{result.latency:.2f}ms" if result.success else "-"
            resolution_str = result.resolution if result.resolution else "-"
            bitrate_str = f"{result.bitrate}Kbps" if result.bitrate else "-"
            content_type_str = result.content_type if result.content_type else "-"
            error_str = f" 错误: {result.error}" if not result.success else ""
            
            f.write(f"{i+1}. {name}\n")
            f.write(f"   URL: {result.url}\n")
            f.write(f"   状态: {status}\n")
            f.write(f"   延迟: {latency_str}\n")
            f.write(f"   分辨率: {resolution_str}\n")
            f.write(f"   码率: {bitrate_str}\n")
            f.write(f"   内容类型: {content_type_str}\n")
            f.write(f"   {error_str}\n")
            f.write("\n")
    
    logger.info(f"测速报告已生成: {report_path}")
    
    # 6. 生成排序后的M3U文件
    if success > 0:
        # 创建排序后的直播源列表（只包含成功的）
        sorted_sources = []
        url_to_name = {url: name for name, url in live_sources}
        
        for result in results:
            if result.success and result.url in url_to_name:
                name = url_to_name[result.url]
                sorted_sources.append((name, result.url))
        
        # 生成M3U文件
        sorted_m3u_path = os.path.join(output_dir, f"sorted_{os.path.basename(input_file)}")
        M3UProcessor.generate_m3u(sorted_sources, sorted_m3u_path)
        logger.info(f"排序后的M3U文件已生成: {sorted_m3u_path}")
    
    return results

def main():
    """主函数"""
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--update":
            # 手动更新模式
            if not update_iptv_sources():
                logger.error("更新IPTV直播源失败")
                sys.exit(1)
        elif sys.argv[1] == "--check-syntax":
            # 检查语法错误
            check_ip_tv_syntax()
        elif sys.argv[1] == "--fix-chars":
            # 修复不可打印字符
            fix_ip_tv_chars()
        elif sys.argv[1] == "--speed-test" and len(sys.argv) > 2:
            # 测速功能
            import asyncio
            input_file = sys.argv[2]
            output_dir = sys.argv[3] if len(sys.argv) > 3 else "output"
            asyncio.run(run_speed_test(input_file, output_dir))
        else:
            # 显示帮助信息
            print("未知参数，请使用以下参数：")
            print("  --update       # 立即手动更新直播源")
            print("  --check-syntax # 检查IP-TV.py文件语法错误")
            print("  --fix-chars    # 修复IP-TV.py文件中的不可打印字符")
            print("  --speed-test   # 对M3U文件中的直播源进行测速，使用方法：--speed-test <input_file> [output_dir]")
    else:
        # 显示帮助信息
        print("=" * 60)
        print("      IPTV直播源自动生成工具")
        print("=" * 60)
        print("功能：")
        print("  1. 从多个来源获取IPTV直播源")
        print("  2. 生成M3U和TXT格式的直播源文件")
        print("  3. 支持手动更新和通过GitHub Actions工作流定时更新")
        print("  4. 检查IP-TV.py文件语法错误")
        print("  5. 修复IP-TV.py文件中的不可打印字符")
        print("  6. 对M3U文件中的直播源进行异步测速")
        print("")
        print("使用方法：")
        print("  python IP-TV.py --update       # 立即手动更新直播源")
        print("  python IP-TV.py --check-syntax # 检查语法错误")
        print("  python IP-TV.py --fix-chars    # 修复不可打印字符")
        print("  python IP-TV.py --speed-test <input_file> [output_dir] # 直播源测速")
        print("")
        print("输出文件：")
        print("  - ip-tv.m3u   # M3U格式的直播源文件")
        print("  - ip-tv.txt   # TXT格式的直播源文件")
        print("  - ip-tv_i4.m3u   # IPv4版本的M3U文件")
        print("  - ip-tv_i4.txt   # IPv4版本的TXT文件")
        print("  - ip-tv_i6.m3u   # IPv6版本的M3U文件")
        print("  - ip-tv_i6.txt   # IPv6版本的TXT文件")
        print("  - iptv_update.log  # 更新日志文件")
        print("  - output/speed_test_report_*.txt  # 测速报告")
        print("  - output/sorted_*.m3u  # 排序后的M3U文件")
        print("=" * 60)


if __name__ == "__main__":
    main()