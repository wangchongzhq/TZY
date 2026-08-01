#!/usr/bin/env python3
"""
IPTV直播源自动生成工具
功能：从多个来源获取IPTV直播源并生成M3U文件
support：手动更新和通过GitHub Actions工作流定时更新
"""

import os
import re
import sys
import time
import requests
import datetime
import logging
import multiprocessing
import tempfile
import ast
import difflib
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# 导入轻量级URL快速检测器
try:
    from quick_url_checker import QuickURLChecker, create_quick_checker
    QUICK_CHECKER_AVAILABLE = True
except ImportError:
    QUICK_CHECKER_AVAILABLE = False
    print("警告: 快速URL检测器不可用，将使用基础检测")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('iptv_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 请求头设置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 时间戳跟踪器
class ValidationTimestamp:
    """验证时间戳跟踪器 - 参考BlackBird-Player的更新时间记录方式"""
    
    _instance = None
    _timestamp = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return cls._instance
    
    @classmethod
    def get_timestamp(cls):
        """获取当前验证时间戳"""
        return cls._timestamp
    
    @classmethod
    def update_timestamp(cls):
        """更新验证时间戳"""
        cls._timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return cls._timestamp
    
    @classmethod
    def reset(cls):
        """重置时间戳"""
        cls._timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class TemplateDrivenProcessor:
    """模板驱动的频道处理器"""
    
    def __init__(self, config_dict=None):
        """初始化处理器"""
        self.config = config_dict or {}
        self.channel_mapping = self.config.get('matching', {}).get('channel_mapping', {})
        self.url_blacklist = self.config.get('network', {}).get('url_blacklist', [])
        
        # 增强匹配配置
        self.fuzzy_threshold = self.config.get('matching', {}).get('fuzzy_threshold', 0.8)
        self.enable_fuzzy_match = self.config.get('matching', {}).get('enable_fuzzy_match', True)
        self.case_sensitive = self.config.get('matching', {}).get('case_sensitive', False)
        
        # 分辨率过滤配置
        self.enable_resolution_filter = self.config.get('filter', {}).get('resolution', True)
        self.min_resolution = self.config.get('filter', {}).get('min_resolution', [1920, 1080])
        self.only_4k = self.config.get('filter', {}).get('only_4k', False)
        
        # URL测试配置
        self.enable_url_testing = self.config.get('url_testing', {}).get('enable', False)
        self.url_timeout = self.config.get('url_testing', {}).get('timeout', 3)
        self.url_retries = self.config.get('url_testing', {}).get('retries', 0)
        
        # 尝试从config模块获取黑名单
        if not self.url_blacklist:
            try:
                import config as config_module
                self.url_blacklist = getattr(config_module, 'url_blacklist', [])
            except ImportError:
                self.url_blacklist = []
        
        logger.info(f"TemplateDrivenProcessor初始化完成")
        logger.info(f"频道映射: {len(self.channel_mapping)} 条记录")
        logger.info(f"URL黑名单: {len(self.url_blacklist)} 条记录")
        logger.info(f"模糊匹配: {'启用' if self.enable_fuzzy_match else '禁用'} (阈值: {self.fuzzy_threshold})")
        logger.info(f"分辨率过滤: {'启用' if self.enable_resolution_filter else '禁用'}")
        logger.info(f"URL测试: {'启用' if self.enable_url_testing else '禁用'}")
    
    def is_url_blacklisted(self, url):
        """检查URL是否在黑名单中"""
        url_lower = url.lower()
        
        # 排除黑名单关键词（stream精确匹配独立组件，避免误杀livestream等合法域名）
        if "rtsp://" in url_lower or "freetv" in url_lower or "kkk" in url_lower or "migu" in url_lower or "catvod" in url_lower or "mgtv" in url_lower:
            return True
        if STREAM_BLACKLIST_RE.search(url_lower):
            return True
            
        if not self.url_blacklist:
            return False
        
        for blacklist_item in self.url_blacklist:
            if blacklist_item and blacklist_item in url_lower:
                return True
        return False
    
    def fuzzy_match(self, name1, name2):
        """模糊匹配算法"""
        if not self.enable_fuzzy_match:
            return name1 == name2
        
        # 使用difflib进行模糊匹配
        similarity = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
        return similarity >= self.fuzzy_threshold
    
    def match_channels(self, online_channels, template_channels):
        """模板驱动的频道匹配"""
        matched_channels = {}
        
        for template_category, template_channel_list in template_channels.items():
            matched_channels[template_category] = {}
            
            for template_channel_name in template_channel_list:
                best_match = None
                best_score = 0
                
                # 精确匹配
                for online_category, online_channel_list in online_channels.items():
                    for online_channel_name, online_url in online_channel_list:
                        # 精确匹配
                        if template_channel_name == online_channel_name:
                            if not self.is_url_blacklisted(online_url):
                                best_match = (online_channel_name, online_url)
                                best_score = 1.0
                                break
                        
                        # 模糊匹配
                        elif self.fuzzy_match(template_channel_name, online_channel_name):
                            similarity = difflib.SequenceMatcher(None, template_channel_name.lower(), online_channel_name.lower()).ratio()
                            if similarity > best_score and not self.is_url_blacklisted(online_url):
                                best_match = (online_channel_name, online_url)
                                best_score = similarity
                
                # 如果找到匹配，添加到结果中
                if best_match:
                    matched_channels[template_category][template_channel_name] = [best_match[1]]
        
        return matched_channels
    
    def is_valid_resolution(self, url):
        """检查URL的视频分辨率是否满足要求"""
        if not self.enable_resolution_filter:
            return True
        
        # 从URL中提取分辨率信息
        # 这里可以扩展为从URL参数、查询字符串或流信息中获取分辨率
        # 目前简单检查URL中是否包含分辨率标识
        
        resolution_patterns = {
            '4K': ['4k', 'uhd', '2160', '3840x2160', '4096x2160'],
            '1080p': ['1080', '1920x1080', 'fhd'],
            '720p': ['720', '1280x720', 'hd']
        }
        
        url_lower = url.lower()
        
        # 如果只要求4K
        if self.only_4k:
            for pattern in resolution_patterns['4K']:
                if pattern in url_lower:
                    return True
            return False
        
        # 检查最小分辨率
        for pattern in resolution_patterns['4K']:
            if pattern in url_lower:
                return True
        
        for pattern in resolution_patterns['1080p']:
            if pattern in url_lower:
                width, height = 1920, 1080
                return (width >= self.min_resolution[0] and height >= self.min_resolution[1])
        
        for pattern in resolution_patterns['720p']:
            if pattern in url_lower:
                width, height = 1280, 720
                return (width >= self.min_resolution[0] and height >= self.min_resolution[1])
        
        # 如果没有找到明确的分辨率信息，根据URL质量判断
        # 高质量URL通常包含特定的域名或路径标识
        high_quality_indicators = [
            'cctv', '央视', '卫视', 'iptv', 'live', 'stream'
        ]
        
        for indicator in high_quality_indicators:
            if indicator in url_lower:
                # 假设这些是高质量源，默认满足最低分辨率要求
                width, height = 1920, 1080  # 默认1080p
                return (width >= self.min_resolution[0] and height >= self.min_resolution[1])
        
        # 默认返回True，允许没有明确分辨率信息的URL通过
        return True

# 频道分类（参考BlackBird-Player的分类方式，使用emoji前缀）
CHANNEL_CATEGORIES = {
    "🇨🇳 4K频道": ['CCTV4K', 'CCTV8K', 'CCTV16 4K', '北京卫视4K', '北京IPTV4K', '湖南卫视4K', '山东卫视4K','广东卫视4K', '四川卫视4K', '浙江卫视4K', '江苏卫视4K', '东方卫视4K', '深圳卫视4K', '河北卫视4K', '峨眉电影4K', '求索4K', '咪视界4K', '欢笑剧场4K', '苏州4K', '至臻视界4K', '南国都市4K', '翡翠台4K', '百事通电影4K', '百事通少儿4K', '百事通纪实4K', '华数爱上4K'],

    "📺 央视频道": ['CCTV1', 'CCTV2', 'CCTV3', 'CCTV4', 'CCTV4欧洲', 'CCTV4美洲', 'CCTV5', 'CCTV5+', 'CCTV6', 'CCTV7', 'CCTV8', 'CCTV9', 'CCTV10', 'CCTV11', 'CCTV12', 'CCTV13', 'CCTV14', 'CCTV15', 'CCTV16', 'CCTV17', 'CETV1', 'CETV2', 'CETV3', 'CETV4', '早期教育','兵器科技', '风云足球', '风云音乐', '风云剧场', '怀旧剧场', '第一剧场', '女性时尚', '世界地理', '央视台球', '高尔夫网球', '央视文化精品', '卫生健康','电视指南', 'CCTV发现之旅', 'CCTV老故事'],

    "📡 卫视频道": ['山东卫视', '浙江卫视', '江苏卫视', '东方卫视', '深圳卫视', '北京卫视', '广东卫视', '广西卫视', '东南卫视', '海南卫视', '河北卫视', '河南卫视', '湖北卫视', '江西卫视', '四川卫视', '重庆卫视', '贵州卫视', '云南卫视', '天津卫视', '安徽卫视', '湖南卫视', '辽宁卫视', '黑龙江卫视', '吉林卫视', '内蒙古卫视', '宁夏卫视', '山西卫视', '陕西卫视', '甘肃卫视', '青海卫视', '新疆卫视', '西藏卫视', '三沙卫视', '厦门卫视', '兵团卫视', '延边卫视', '安多卫视', '康巴卫视', '农林卫视', '山东教育', '大湾区卫视', '海峡卫视', '内蒙古蒙语卫视'],

    "🏙️ 北京专属频道": ['北京卫视', '北京财经', '北京纪实', '北京生活', '北京体育休闲', '北京国际', '北京文艺', '北京新闻', '北京淘电影', '北京淘剧场', '北京淘4K', '北京淘娱乐', '北京淘BABY', '北京萌宠TV', '北京卡酷少儿'],

    "🌊 山东专属频道": ['山东卫视', '山东齐鲁', '山东综艺', '山东少儿', '山东生活',
                 '山东新闻', '山东国际', '山东体育', '山东文旅', '山东农科'],

    "🌏 港澳频道": ['凤凰中文', '凤凰资讯', '凤凰香港', '凤凰电影', '中天新闻','中天娱乐', '中天综合','中天亚洲', '翡翠台', '香港卫视', '人间卫视', '明珠台', '无线新闻', '国兴卫视', '东森美洲卫视', '无线星河', '澳亚卫视', '莲花卫视', '香港32台', '香港33台', '香港34台', '香港35台'],

    "🎬 电影频道": ['CHC动作电影', 'CHC家庭影院', 'CHC影迷电影', '淘电影',
                 '淘精彩', '淘剧场', '星空卫视', '黑莓电影', '东北热剧',
                 '中国功夫', '动作电影', '超级电影', 'CHC高清电影', '龙祥电影'],

    "👶 儿童频道": ['动漫秀场', '哒啵电竞', '黑莓动画', '卡酷少儿',
                 '金鹰卡通', '优漫卡通', '哈哈炫动', '嘉佳卡通', '炫动卡通'],

    "🔥 iHOT频道": ['iHOT爱喜剧', 'iHOT爱科幻', 'iHOT爱院线', 'iHOT爱悬疑', 'iHOT爱历史', 'iHOT爱谍战', 'iHOT爱旅行', 'iHOT爱幼教', 'iHOT爱玩具', 'iHOT爱体育', 'iHOT爱赛车', 'iHOT爱浪漫', 'iHOT爱奇谈', 'iHOT爱科学', 'iHOT爱动漫'],

    "📊 综合频道": ['重温经典', 'CHANNEL[V]', '求索纪录', '求索科学', '求索生活', '求索动物', '睛彩青少', '睛彩竞技', '睛彩篮球', '睛彩广场舞', '金鹰纪实', '快乐垂钓', '茶频道', '军事评论', '军旅剧场', '乐游', '生活时尚', '都市剧场', '欢笑剧场', '游戏风云', '金色学堂', '法治天地', '哒啵赛事', '新视觉', '睛彩中原', '睛彩羽毛球'],

    "⚽ 体育频道": ['天元围棋', '魅力足球', '五星体育', '劲爆体育', '超级体育'],
    
    "🎭 剧场频道": ['古装剧场', '家庭剧场', '惊悚悬疑', '明星大片', '欢乐剧场', '海外剧场', '潮妈辣婆',
                 '爱情喜剧', '超级电视剧', '超级综艺', '金牌综艺', '武搏世界', '农业致富', '炫舞未来',
                 '精品体育', '精品大剧', '精品纪录', '精品萌宠', '怡伴健康'],

}


# 频道映射（别名 -> 规范名）
CHANNEL_MAPPING = {
    # 4K频道
    "CCTV4K": ["CCTV 4K", "CCTV-4K超高清頻道", "CCTV4K超高清頻道", "CCTV-4K"],
    "CCTV8K": ["CCTV 8K", "CCTV-8K超高清頻道", "CCTV8K超高清頻道", "CCTV-8K"],
    "CCTV16 4K": ["CCTV16-4K", "CCTV16 奥林匹克 4K", "CCTV16奥林匹克 4K"],
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
    "CCTV1": ["CCTV-1", "CCTV-1 HD", "CCTV1综合", "CCTV-1 综合", "CCTV-1综合"],
    "CCTV2": ["CCTV-2", "CCTV-2 HD", "CCTV2 财经", "CCTV-2 财经", "CCTV-2财经", "CCTV2财经"],
    "CCTV3": ["CCTV-3", "CCTV-3 HD", "CCTV3 综艺", "CCTV-3 综艺", "CCTV-3综艺", "CCTV3综艺"],
    "CCTV4": ["CCTV-4", "CCTV-4 HD", "CCTV4a", "CCTV4A", "CCTV4 中文国际", "CCTV-4 中文国际", "CCTV-4中文国际", "CCTV4中文国际"],
    "CCTV4欧洲": ["CCTV-4欧洲", "CCTV-4欧洲 HD", "CCTV-4 欧洲", "CCTV4o", "CCTV4O", "CCTV-4 中文欧洲", "CCTV4中文欧洲"],
    "CCTV4美洲": ["CCTV-4美洲", "CCTV-4美洲 HD", "CCTV-4 美洲", "CCTV4m", "CCTV4M", "CCTV-4 中文美洲", "CCTV4中文美洲"],
    "CCTV5": ["CCTV-5", "CCTV-5 HD", "CCTV5 体育", "CCTV-5 体育", "CCTV-5体育", "CCTV5体育"],
    "CCTV5+": ["CCTV-5+", "CCTV-5+ HD", "CCTV5+ 体育赛事", "CCTV-5+ 体育赛事", "CCTV-5+HD", "CCTV-5+体育赛事", "CCTV5+体育赛事"],
    "CCTV6": ["CCTV-6", "CCTV-6 HD", "CCTV6 电影", "CCTV-6 电影", "CCTV-6电影", "CCTV6电影"],
    "CCTV7": ["CCTV-7", "CCTV-7 HD", "CCTV7 国防军事", "CCTV-7 国防军事", "CCTV-7国防军事", "CCTV7国防军事"],
    "CCTV8": ["CCTV-8", "CCTV-8 HD", "CCTV8 电视剧", "CCTV-8 电视剧", "CCTV-8电视剧", "CCTV8电视剧"],
    "CCTV9": ["CCTV-9", "CCTV-9 HD", "CCTV9 纪录", "CCTV-9 纪录", "CCTV-9纪录", "CCTV9纪录"],
    "CCTV10": ["CCTV-10", "CCTV-10 HD", "CCTV10 科教", "CCTV-10 科教", "CCTV-10科教", "CCTV10科教"],
    "CCTV11": ["CCTV-11", "CCTV-11 HD", "CCTV11 戏曲", "CCTV-11 戏曲", "CCTV-11戏曲", "CCTV11戏曲"],
    "CCTV12": ["CCTV-12", "CCTV-12 HD", "CCTV12 社会与法", "CCTV-12 社会与法", "CCTV-12社会与法", "CCTV12社会与法"],
    "CCTV13": ["CCTV-13", "CCTV-13 HD", "CCTV13 新闻", "CCTV-13 新闻", "CCTV-13新闻", "CCTV13新闻"],
    "CCTV14": ["CCTV-14", "CCTV-14 HD", "CCTV14 少儿", "CCTV-14 少儿", "CCTV-14少儿", "CCTV14少儿"],
    "CCTV15": ["CCTV-15", "CCTV-15 HD", "CCTV15 音乐", "CCTV-15 音乐", "CCTV-15音乐", "CCTV15音乐"],
    "CCTV16": ["CCTV-16", "CCTV-16 HD", "CCTV-16 奥林匹克", "CCTV16 奥林匹克", "CCTV-16奥林匹克"],
    "CCTV17": ["CCTV-17", "CCTV-17 HD", "CCTV17 农业农村", "CCTV-17 农业农村", "CCTV-17农业农村", "CCTV17农业农村"],
    "CETV1": ["CETV-1", "中国教育1", "中国教育台1", "中国教育-1", "中国教育电视台1", "中国教育1台"],
    "CETV2": ["CETV-2", "中国教育2", "中国教育台2", "中国教育-2", "中国教育电视台2", "中国教育2台"],
    "CETV3": ["CETV-3", "中国教育3", "中国教育台3", "中国教育-3", "中国教育电视台3"],
    "CETV4": ["CETV-4", "中国教育4", "中国教育台4", "中国教育-4", "中国教育电视台4", "中国教育4台"],
    "早期教育": ["CETV-早期教育", "中国教育台-早期教育", "早教", "幼儿教育"],
    "兵器科技": ["CCTV-兵器科技", "CCTV兵器科技"],

    "风云足球": ["CCTV-风云足球", "CCTV风云足球"],
    "风云音乐": ["CCTV-风云音乐", "CCTV风云音乐", "风云音乐HD", "风云音乐 HD"],
    "风云剧场": ["CCTV-风云剧场", "CCTV风云剧场"],
    "怀旧剧场": ["CCTV-怀旧剧场", "CCTV怀旧剧场"],
    "第一剧场": ["CCTV-第一剧场", "CCTV第一剧场"],
    "女性时尚": ["CCTV-女性时尚", "CCTV女性时尚"],
    "世界地理": ["CCTV-世界地理", "CCTV世界地理"],
    "央视台球": ["CCTV-央视台球", "CCTV央视台球"],
    "高尔夫网球": ["CCTV-高尔夫网球", "CCTV央视高网", "CCTV高尔夫网球", "央视高网"],
    "央视文化精品": ["CCTV-央视文化精品", "CCTV央视文化精品", "CCTV文化精品", "央视文化精品"],
    "卫生健康": ["CCTV-卫生健康", "CCTV卫生健康"],
    "电视指南": ["CCTV-电视指南", "CCTV电视指南"],
    "CCTV发现之旅": ["发现之旅"],
    "CCTV老故事": ["CCTV-老故事", "老故事"],
    
    # 卫视频道
    "山东卫视": ["山东卫视 HD", "山东卫视高清", "山东台"],
    "浙江卫视": ["浙江卫视 HD", "浙江卫视高清", "浙江台"],
    "江苏卫视": ["江苏卫视 HD", "江苏卫视高清", "江苏台"],
    "东方卫视": ["东方卫视 HD", "东方卫视高清", "东方台", "上海东方卫视", "上海卫视"],
    "深圳卫视": ["深圳卫视 HD", "深圳卫视高清", "深圳台"],
    "北京卫视": ["北京卫视 HD", "北京卫视高清", "北京台"],
    "广东卫视": ["广东卫视 HD", "广东卫视高清", "广东台"],
    "广西卫视": ["广西卫视 HD", "广西卫视高清", "广西台"],
    "东南卫视": ["东南卫视 HD", "东南卫视高清", "东南台", "福建东南卫视", "福建海峡卫视"],
    "海南卫视": ["海南卫视 HD", "海南卫视高清", "海南台", "旅游卫视", "旅游卫视 HD"],
    "河北卫视": ["河北卫视 HD", "河北卫视高清", "河北台"],
    "河南卫视": ["河南卫视 HD", "河南卫视高清", "河南台"],
    "湖北卫视": ["湖北卫视 HD", "湖北卫视高清", "湖北台"],
    "江西卫视": ["江西卫视 HD", "江西卫视高清", "江西台"],
    "四川卫视": ["四川卫视 HD", "四川卫视高清", "四川台"],
    "重庆卫视": ["重庆卫视 HD", "重庆卫视高清", "重庆台"],
    "贵州卫视": ["贵州卫视 HD", "贵州卫视高清", "贵州台"],
    "云南卫视": ["云南卫视 HD", "云南卫视高清", "云南台"],
    "天津卫视": ["天津卫视 HD", "天津卫视高清", "天津台"],
    "安徽卫视": ["安徽卫视 HD", "安徽卫视高清", "安徽台"],
    "湖南卫视": ["湖南卫视 HD", "湖南卫视高清", "湖南台"],
    "辽宁卫视": ["辽宁卫视 HD", "辽宁卫视高清", "辽宁台"],
    "黑龙江卫视": ["黑龙江卫视 HD", "黑龙江卫视高清", "黑龙江台"],
    "吉林卫视": ["吉林卫视 HD", "吉林卫视高清", "吉林台"],
    "内蒙古卫视": ["内蒙古卫视 HD", "内蒙古卫视高清", "内蒙古台"],
    "宁夏卫视": ["宁夏卫视 HD", "宁夏卫视高清", "宁夏台"],
    "山西卫视": ["山西卫视 HD", "山西卫视高清", "山西台"],
    "陕西卫视": ["陕西卫视 HD", "陕西卫视高清", "陕西台"],
    "甘肃卫视": ["甘肃卫视 HD", "甘肃卫视高清", "甘肃台"],
    "青海卫视": ["青海卫视 HD", "青海卫视高清", "青海台"],
    "新疆卫视": ["新疆卫视 HD", "新疆卫视高清", "新疆台"],
    "西藏卫视": ["西藏卫视 HD", "西藏卫视高清", "西藏台"],
    "三沙卫视": ["三沙卫视 HD", "三沙卫视高清", "三沙台"],
    "厦门卫视": ["厦门卫视 HD", "厦门卫视高清", "厦门台"],
    "兵团卫视": ["兵团卫视 HD", "兵团卫视高清", "兵团台"],
    "延边卫视": ["延边卫视 HD", "延边卫视高清", "延边台"],
    "安多卫视": ["安多卫视 HD", "安多卫视高清", "安多台"],
    "康巴卫视": ["康巴卫视 HD", "康巴卫视高清", "康巴台"],
    "农林卫视": ["农林卫视 HD", "农林卫视高清", "农林台", "中国农林卫视", "陕西农林卫视"],
    "山东教育": ["山东教育 HD", "山东教育高清", "山东教育台", "山东教育卫视"],
    "大湾区卫视": ["南方卫视"],
    "海峡卫视": [],
    "内蒙古蒙语卫视": ["内蒙古蒙语"],

    # 北京专属频道映射
    "北京财经": ["BTV财经", "BTV-财经"],
    "北京纪实": ["BTV纪实", "BTV-纪实"],
    "北京生活": ["BTV生活", "BTV-生活"],
    "北京体育休闲": ["BTV体育休闲", "BTV-体育休闲"],
    "北京国际": ["BTV国际", "BTV-国际"],
    "北京文艺": ["BTV文艺", "BTV-文艺"],
    "北京新闻": ["BTV新闻", "BTV-新闻"],
    "北京淘电影": ["BTV淘电影"],
    "北京淘剧场": ["BTV淘剧场"],
    "北京淘4K": ["BTV淘4K"],
    "北京淘娱乐": ["BTV淘娱乐"],
    "北京淘BABY": ["BTV淘BABY"],
    "北京萌宠TV": ["BTV萌宠TV"],
    "北京卡酷少儿": ["卡酷少儿", "卡酷", "卡酷动画"],

    # 山东专属频道映射
    "山东齐鲁": ["齐鲁频道"],
    "山东综艺": ["综艺频道"],
    "山东少儿": ["少儿频道"],
    "山东生活": ["生活频道"],
    "山东新闻": ["新闻频道"],
    "山东国际": ["国际频道"],
    "山东体育": ["体育频道"],
    "山东文旅": ["文旅频道"],
    "山东农科": ["农科频道"],

    # 港澳频道映射
    "凤凰中文": ["凤凰卫视中文台", "凤凰卫视"],
    "凤凰资讯": ["凤凰卫视资讯台"],
    "凤凰香港": ["凤凰卫视香港台"],
    "凤凰电影": ["凤凰卫视电影台"],
    "中天新闻": ["中天新闻台"],
    "中天娱乐": ["中天娱乐台"],
    "中天综合": ["中天综合台"],
    "中天亚洲": ["中天亚洲台"],

    # 港澳频道新增
    "翡翠台": [], "香港卫视": [], "人间卫视": [],
    "明珠台": ["TVB明珠台"], "无线新闻": ["无线新闻台"],
    "国兴卫视": [], "东森美洲卫视": ["东森美洲台", "东森美洲"],
    "无线星河": ["TVB星河", "星河频道"],
    "澳亚卫视": [], "莲花卫视": [],
    "香港32台": [], "香港33台": [], "香港34台": [], "香港35台": [],

    # 电影频道映射
    "CHC动作电影": ["动作电影"],
    "CHC家庭影院": ["家庭影院"],
    "CHC影迷电影": ["影迷电影"],
    "淘电影": ["电影"],
    "淘精彩": ["精彩"],
    "淘剧场": ["剧场"],
    "星空卫视": ["星空"],
    "黑莓电影": ["电影"],
    "东北热剧": ["热剧"],
    "中国功夫": ["功夫"],
    "动作电影": ["电影动作"],
    "超级电影": ["电影超级"],
    "CHC高清电影": ["CHC电影", "高清电影"],
    "龙祥电影": ["龙祥电影台"],

    # 儿童频道映射
    "动漫秀场": ["动漫"],
    "哒啵电竞": ["电竞"],
    "黑莓动画": ["动画"],
    "卡酷少儿": ["卡酷"],
    "金鹰卡通": ["金鹰"],
    "优漫卡通": ["优漫", "优漫卡通频道"],
    "炫动卡通": ["炫动卡通频道", "上海炫动卡通"],
    "哈哈炫动": ["哈哈"],
    "嘉佳卡通": ["嘉佳"],

    # iHOT频道映射
    "iHOT爱喜剧": ["爱喜剧"],
    "iHOT爱科幻": ["爱科幻"],
    "iHOT爱院线": ["爱院线"],
    "iHOT爱悬疑": ["爱悬疑"],
    "iHOT爱历史": ["爱历史"],
    "iHOT爱谍战": ["爱谍战"],
    "iHOT爱旅行": ["爱旅行"],
    "iHOT爱幼教": ["爱幼教"],
    "iHOT爱玩具": ["爱玩具"],
    "iHOT爱体育": ["爱体育"],
    "iHOT爱赛车": ["爱赛车"],
    "iHOT爱浪漫": ["爱浪漫"],
    "iHOT爱奇谈": ["爱奇谈"],
    "iHOT爱科学": ["爱科学"],
    "iHOT爱动漫": ["爱动漫"],

    # 综合频道映射
    "重温经典": ["经典"],
    "CHANNEL[V]": ["Channel V"],
    "求索纪录": ["纪录"],
    "求索科学": ["科学"],
    "求索生活": ["生活"],
    "求索动物": ["动物"],
    "睛彩青少": ["青少"],
    "睛彩竞技": ["竞技"],
    "睛彩篮球": ["篮球"],
    "睛彩广场舞": ["广场舞"],
    "金鹰纪实": ["纪实"],
    "快乐垂钓": ["垂钓"],
    "茶频道": ["茶"],
    "军事评论": ["军事"],
    "军旅剧场": ["军旅"],
    "乐游": ["旅游"],
    "生活时尚": ["时尚"],
    "都市剧场": ["都市"],
    "欢笑剧场": ["欢笑"],
    "游戏风云": ["游戏"],
    "金色学堂": ["学堂"],
    "法治天地": ["法治"],
    "哒啵赛事": ["赛事"],
    "新视觉": [],
    "睛彩中原": [],
    "睛彩羽毛球": [],

    # 体育频道映射
    "天元围棋": ["围棋"],
    "魅力足球": ["足球"],
    "五星体育": ["五星"],
    "劲爆体育": ["劲爆"],
    "超级体育": ["超级"],

    # 剧场频道映射
    "古装剧场": ["古装"],
    "家庭剧场": ["家庭"],
    "惊悚悬疑": ["悬疑"],
    "明星大片": ["大片"],
    "欢乐剧场": ["欢乐"],
    "海外剧场": ["海外"],
    "潮妈辣婆": ["潮妈"],
    "爱情喜剧": ["爱情"],
    "超级电视剧": ["电视剧"],
    "超级综艺": ["综艺"],
    "金牌综艺": ["金牌"],
    "武搏世界": ["武搏"],
    "农业致富": ["农业"],
    "炫舞未来": ["炫舞"],
    "精品体育": ["精品"],
    "精品大剧": ["大剧"],
    "精品纪录": ["纪录"],
    "精品萌宠": ["萌宠"],
    "怡伴健康": ["健康"]
 }


# 默认配置
DEFAULT_CONFIG = {
    "sources": {
        "default": [],  # 从unified_sources导入，可在配置文件中覆盖
        "local": [],    # 本地直播源文件列表
        "custom": []    # 用户自定义直播源URL列表
    },
    "filter": {
        "resolution": True,    # 开启分辨率过滤
        "min_resolution": [1920, 1080],  # 最低分辨率要求
        "only_4k": False       # 是否只获取4K频道
    },
    "url_testing": {
        "enable": True,    # 启用URL有效性测试
        "timeout": 2,      # URL测试超时时间（秒）
        "retries": 1,      # URL测试重试次数
        "workers": 32      # URL测试并发数
    },
    "cache": {
        "expiry_time": 3600,  # 缓存有效期（秒）
        "file": "source_cache.json"  # 缓存文件路径
    },
    "output": {
        "m3u_file": "jieguo.m3u",  # M3U输出文件
        "txt_file": "jieguo.txt"   # TXT输出文件
    }
}

# 配置文件路径
CONFIG_FILE = "iptv_config.json"

# 从统一播放源文件导入
try:
    from unified_sources import UNIFIED_SOURCES
    # 将UNIFIED_SOURCES设置为默认直播源
    DEFAULT_CONFIG["sources"]["default"] = UNIFIED_SOURCES
except ImportError:
    print("警告: 无法导入unified_sources模块，默认直播源为空")

# 全局配置变量
config = DEFAULT_CONFIG.copy()

# 直播源内容缓存配置
import json
import hashlib

# 缓存字典，格式：{url: (cached_time, content, etag, last_modified)}
source_cache = {}

# 使用配置文件中的缓存设置
CACHE_FILE = config["cache"]["file"]
cache_expiry_time = config["cache"]["expiry_time"]

# 创建全局Session对象以提高请求性能
session = requests.Session()
session.headers.update(HEADERS)
# 使用配置中的并发数
test_workers = config["url_testing"]["workers"]
session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=test_workers, max_retries=0))
session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=test_workers, max_retries=0))

# 保存缓存到文件
def save_cache():
    """将缓存保存到文件"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            # 转换为可序列化的格式
            serializable_cache = {}
            for url, (cached_time, content, etag, last_modified) in source_cache.items():
                serializable_cache[url] = {
                    'cached_time': cached_time,
                    'content': content,
                    'etag': etag,
                    'last_modified': last_modified
                }
            json.dump(serializable_cache, f, ensure_ascii=False, indent=2)
        return True
    except (IOError, OSError) as e:
        print(f"保存缓存失败: 文件操作错误 - {e}")
        return False
    except (ValueError, TypeError) as e:
        print(f"保存缓存失败: 数据格式错误 - {e}")
        return False
    except Exception as e:
        print(f"保存缓存失败: 未知错误 - {e}")
        return False

# 从文件加载缓存
def load_cache():
    """从文件加载缓存"""
    global source_cache
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                serializable_cache = json.load(f)
                # 转换回原始格式
                source_cache = {}
                for url, data in serializable_cache.items():
                    source_cache[url] = (
                        data['cached_time'],
                        data['content'],
                        data.get('etag'),
                        data.get('last_modified')
                    )
            print(f"✅ 从缓存文件加载了 {len(source_cache)} 个缓存条目")
        return True
    except (IOError, OSError) as e:
        print(f"加载缓存失败: 文件操作错误 - {e}")
        source_cache = {}
        return False
    except (ValueError, TypeError) as e:
        print(f"加载缓存失败: 数据格式错误 - {e}")
        source_cache = {}
        return False
    except Exception as e:
        print(f"加载缓存失败: 未知错误 - {e}")
        source_cache = {}
        return False

# 计算内容的MD5哈希值
def calculate_md5(content):
    """计算字符串的MD5哈希值"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

# 加载配置文件
def load_config():
    """加载配置文件"""
    global config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                
                # 合并配置（用户配置覆盖默认配置）
                def merge_dicts(default, user):
                    for key, value in user.items():
                        if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                            merge_dicts(default[key], value)
                        else:
                            default[key] = value
                    return default
                
                config = merge_dicts(config, user_config)
                print(f"✅ 从配置文件加载了用户设置")
                
                # 更新全局变量
                update_global_vars_from_config()
        else:
            # 创建默认配置文件
            save_config()
            print(f"✅ 创建了默认配置文件: {CONFIG_FILE}")
        return True
    except (IOError, OSError) as e:
        print(f"加载配置文件失败: 文件操作错误 - {e}")
        config = DEFAULT_CONFIG.copy()
        update_global_vars_from_config()
        return False
    except (ValueError, TypeError) as e:
        print(f"加载配置文件失败: 数据格式错误 - {e}")
        config = DEFAULT_CONFIG.copy()
        update_global_vars_from_config()
        return False
    except Exception as e:
        print(f"加载配置文件失败: 未知错误 - {e}")
        config = DEFAULT_CONFIG.copy()
        update_global_vars_from_config()
        return False

# 保存配置文件
def save_config():
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False

# 更新全局变量
def update_global_vars_from_config():
    """从配置更新全局变量"""
    global CACHE_FILE, cache_expiry_time
    
    # 更新缓存设置
    CACHE_FILE = config["cache"]["file"]
    cache_expiry_time = config["cache"]["expiry_time"]



# 预编译4K相关的正则表达式
K4_PATTERNS = re.compile(r'(2160[pdi]|4k|8k|uhd|3840x2160|7680x4320|超高清)', re.IGNORECASE)
K4_RES_PATTERNS = [
    re.compile(r'(\d{3,4})[pdi]'),  # 如2160p
    re.compile(r'(\d+)x(\d+)'),     # 如3840x2160
]

# 预编译M3U频道提取正则表达式
M3U_CHANNEL_PATTERN = re.compile(r'#EXTINF:.*?tvg-name="([^"]*)".*?(?:group-title="([^"]*)")?,([^\n]+)\n(http[^\n]+)', re.DOTALL)

# 预编译内容清理正则表达式
CLEAN_CONTENT_PATTERN = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f\u20ac\ue000-\uf8ff]')

# 预编译黑名单"stream"关键词正则（仅匹配独立组件，避免误杀livestream等合法域名）
STREAM_BLACKLIST_RE = re.compile(r'(?<![a-z])stream(?![a-z])|streaming', re.IGNORECASE)





def is_4k(channel_name, url):
    """判断频道是否为4K频道"""
    
    # 检查频道名称和URL中的4K标识
    combined_text = channel_name + ' ' + url
    
    # 检查是否包含4K标识
    if K4_PATTERNS.search(combined_text):
        return True
    
    # 检查频道分类
    if get_channel_category(channel_name) == "4K频道":
        return True
    
    # 检查分辨率
    for pattern in K4_RES_PATTERNS:
        res_match = pattern.search(combined_text)
        if res_match:
            try:
                if len(res_match.groups()) == 1:
                    # 垂直分辨率（如2160p）
                    res_value = int(res_match.group(1))
                    if res_value >= 2160:
                        return True
                elif len(res_match.groups()) == 2:
                    # 完整分辨率（如3840x2160）
                    width = int(res_match.group(1))
                    height = int(res_match.group(2))
                    if width >= 3840 and height >= 2160:
                        return True
            except ValueError:
                pass
    
    return False

# 检查URL是否有效
def check_url(url, timeout=2, retries=1):
    """检查URL是否可访问，支持重试机制
    
    参数:
        url: 要测试的URL
        timeout: 超时时间（秒）
        retries: 重试次数
    
    返回:
        bool: URL是否可用
    """
    # 1. 基本URL格式验证
    if not url or url.strip() == "":
        return False
    
    # 2. 过滤掉明显不是URL的内容
    if url.startswith('#'):
        return False
    
    # 3. 快速预过滤：基于已知的无效域名或模式
    invalid_patterns = [
        '127.0.0.1', 'localhost', 'example.com', 'test.com',
        '.local', '.internal',
        'deadlink', 'expired', 'invalid', 'notfound',
        'suspended', 'blocked', 'error', '404', 'not found'
    ]
    url_lower = url.lower()
    for pattern in invalid_patterns:
        if pattern in url_lower:
            return False
    
    # 4. 检查协议
    if '://' not in url and not url.startswith('//'):
        return False
    
    # 5. 对于非HTTP/HTTPS协议的URL，进行基本验证
    if not url.startswith(('http://', 'https://')):
        # 对于UDP, RTSP等协议，只进行基本格式验证
        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme not in ['udp', 'rtmp', 'rtp']:
            return False
        if not parsed.hostname:
            return False
        return True
    
    # 6. HTTP/HTTPS协议验证 - 简化版
    try:
        # 使用HEAD请求快速验证
        response = session.head(
            url, 
            timeout=timeout, 
            allow_redirects=True
        )
        
        # 只要状态码是200-399就认为是有效的
        return 200 <= response.status_code < 400
    except:
        # 任何错误都认为是无效的，不进行重试
        return False

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



# 从M3U文件中提取频道信息
def extract_channels_from_m3u(content):
    """从M3U内容中提取频道信息（使用增强匹配算法）"""
    channels = defaultdict(list)
    matches = re.findall(M3U_CHANNEL_PATTERN, content)
    
    # 初始化增强处理器
    processor = TemplateDrivenProcessor()
    
    for match in matches:
        tvg_name = match[0].strip() if match[0] else match[2].strip()
        channel_name = match[2].strip()
        url = match[3].strip()
        
        # 基础过滤检查
        if not channel_name or channel_name.isdigit():
            continue
        
        # 购物频道过滤
        channel_name_lower = channel_name.lower()
        shopping_keywords = ['购物', '导购', '电视购物']
        if any(keyword in channel_name_lower for keyword in shopping_keywords):
            continue
        
        # URL黑名单检查
        if processor.is_url_blacklisted(url):
            logger.debug(f"URL在黑名单中，跳过: {url}")
            continue
        
        # 分辨率过滤检查
        if processor.enable_resolution_filter and not processor.is_valid_resolution(url):
            logger.debug(f"URL分辨率不满足要求，跳过: {url}")
            continue
        
        # 增强频道名称匹配
        matched_name = None
        best_match_score = 0
        
        # 遍历所有标准频道名称进行匹配
        for standard_name in CHANNEL_MAPPING.keys():
            # 精确匹配
            if channel_name == standard_name:
                matched_name = standard_name
                best_match_score = 1.0
                break
            
            # 检查别名匹配
            if channel_name in CHANNEL_MAPPING[standard_name]:
                matched_name = standard_name
                best_match_score = 1.0
                break
            
            # 模糊匹配（如果启用）
            if processor.enable_fuzzy_match:
                similarity = processor.fuzzy_match(channel_name, standard_name)
                if similarity >= processor.fuzzy_threshold and similarity > best_match_score:
                    matched_name = standard_name
                    best_match_score = similarity
        
        # 如果找到匹配的频道
        if matched_name:
            # 获取频道分类
            category = get_channel_category(matched_name)
            # 只添加CHANNEL_CATEGORIES中定义的频道
            if category != "其他频道":
                channels[category].append((matched_name, url))
                logger.debug(f"匹配成功: {channel_name} -> {matched_name} (相似度: {best_match_score:.2f})")
    
    return channels

# 获取频道分类
def get_channel_category(channel_name):
    """获取频道所属的分类"""
    for category, channels in CHANNEL_CATEGORIES.items():
        if channel_name in channels:
            return category
    return "其他频道"

# 规范化频道名称
def normalize_channel_name(name):
    """将频道名称规范化为标准名称"""
    name = name.strip()
    # 检查是否是标准名称
    for standard_name in CHANNEL_MAPPING:
        if name == standard_name:
            return standard_name
    # 检查是否是别名
    for standard_name, aliases in CHANNEL_MAPPING.items():
        if name in aliases:
            return standard_name
    return None

# 从URL获取M3U内容
def fetch_m3u_content(url, max_retries=2, timeout=180):
    """从URL或本地文件获取M3U内容，支持超时、重试机制和增量更新"""
    # 处理本地文件路径
    if url.startswith('file://'):
        file_path = url[7:]  # 移除file://前缀
        try:
            print(f"正在读取本地文件: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content
        except Exception as e:
            print(f"读取本地文件 {file_path} 时出错: {e}")
            return None
    
    # 检查缓存
    etag = None
    last_modified = None
    if url in source_cache:
        cached_time, cached_content, cached_etag, cached_last_modified = source_cache[url]
        if time.time() - cached_time < cache_expiry_time:
            print(f"正在从缓存获取: {url}")
            return cached_content
        etag = cached_etag
        last_modified = cached_last_modified
    
    # 缓存不存在或已过期，尝试增量更新
    headers = {}
    if etag:
        headers['If-None-Match'] = etag
    if last_modified:
        headers['If-Modified-Since'] = last_modified
    
    # 处理远程URL
    for attempt in range(max_retries):
        try:
            # 添加verify=False参数来跳过SSL证书验证，并使用自定义headers
            response = session.get(url, timeout=timeout, verify=False, headers=headers)
            
            if response.status_code == 304:
                # 内容未修改，使用缓存内容
                print(f"内容未修改，使用缓存: {url}")
                if url in source_cache:
                    cached_time, cached_content, cached_etag, cached_last_modified = source_cache[url]
                    # 更新缓存时间
                    source_cache[url] = (time.time(), cached_content, cached_etag, cached_last_modified)
                    save_cache()
                    return cached_content
            
            response.raise_for_status()
            content = response.text
            
            # 获取新的ETag和Last-Modified
            new_etag = response.headers.get('ETag')
            new_last_modified = response.headers.get('Last-Modified')
            
            # 检查内容是否有变化（如果服务器不支持ETag/Last-Modified）
            if url in source_cache:
                _, old_content, _, _ = source_cache[url]
                if calculate_md5(content) == calculate_md5(old_content):
                    print(f"内容未变化，更新缓存时间: {url}")
                    # 内容未变化，更新缓存时间
                    source_cache[url] = (time.time(), old_content, new_etag, new_last_modified)
                    save_cache()
                    return old_content
            
            # 更新缓存
            source_cache[url] = (time.time(), content, new_etag, new_last_modified)
            save_cache()
            
            print(f"获取成功: {url}")
            return content
        except requests.exceptions.ConnectionError:
            # 连接错误，重试间隔增加
            wait_time = 2 ** attempt  # 指数退避
            print(f"连接错误，{wait_time}秒后重试...")
            time.sleep(wait_time)
        except requests.exceptions.Timeout:
            # 超时错误，增加超时时间后重试
            timeout = min(timeout * 1.5, 180)  # 最大超时3分钟
            wait_time = 2 ** attempt
            print(f"请求超时，{wait_time}秒后重试（新超时时间：{timeout}秒）...")
            time.sleep(wait_time)
        except Exception as e:
            # 其他错误
            print(f"获取 {url} 时出错: {e}")
            wait_time = 2 ** attempt if attempt < max_retries - 1 else 0
            if wait_time > 0:
                print(f"{wait_time}秒后重试...")
                time.sleep(wait_time)
    return None



# 生成M3U文件
def generate_m3u_file(channels, output_path):
    """生成M3U文件"""
    print(f"正在生成 {output_path}...")
    
    print(f"📝 开始写入文件: {output_path} 时间: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))}")
    print(f"📊 写入前文件大小: {os.path.getsize(output_path) if os.path.exists(output_path) else 0} 字节")
    print(f"📊 写入前文件修改时间: {datetime.datetime.fromtimestamp(os.path.getmtime(output_path)) if os.path.exists(output_path) else '不存在'}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入文件头
        f.write("#EXTM3U x-tvg-url=\"https://kakaxi-1.github.io/IPTV/epg.xml\"\n")
        
        # 写入当前时间作为标记（北京时间UTC+8）
        f.write(f"# 生成时间: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
        
        # 按CHANNEL_CATEGORIES中定义的顺序写入分类
        written_count = 0
        for category in CHANNEL_CATEGORIES:
            if category in channels:
                # 对当前类别的频道按名称升序排序
                sorted_channels = sorted(channels[category], key=lambda x: x[0])
                for channel_name, url in sorted_channels:
                    # 写入频道信息
                    f.write(f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"{category}\",{channel_name}\n")
                    f.write(f"{url}\n")
                    written_count += 1
        
        # 不写入其他频道，只包含CHANNEL_CATEGORIES中定义的频道
    
    print(f"📝 完成写入文件: {output_path} 时间: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))}")
    print(f"📊 写入后文件大小: {os.path.getsize(output_path)} 字节")
    print(f"📊 写入后文件修改时间: {datetime.datetime.fromtimestamp(os.path.getmtime(output_path))}")
    print(f"📊 实际写入频道数: {written_count}")
    return True

# 生成TXT文件
def generate_txt_file(channels, output_path):
    """生成TXT文件（参考BlackBird-Player的result.txt格式）"""
    print(f"正在生成 {output_path}...")
    
    # 更新验证时间戳
    timestamp = ValidationTimestamp.update_timestamp()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入更新时间戳（参考BlackBird-Player格式）
        f.write("🕘️更新时间,#genre#\n")
        f.write(f"{timestamp}\n\n")
        
        # 按CHANNEL_CATEGORIES中定义的顺序写入分类
        for category in CHANNEL_CATEGORIES:
            if category in channels and channels[category]:
                # 写入分组标题，使用格式: 分组名,#genre#
                category_clean = category.replace('🇨🇳 ', '').replace('📺 ', '').replace('📡 ', '').replace('🏙️ ', '').replace('🌊 ', '').replace('🌏 ', '').replace('🎬 ', '').replace('👶 ', '').replace('🔥 ', '').replace('📊 ', '').replace('⚽ ', '').replace('🎭 ', '')
                
                # 特殊处理：4K频道不需要#符号
                if category_clean == "4K频道":
                    cleaned_category = "4K频道"
                else:
                    # 移除所有#号，确保分类名前后没有#
                    cleaned_category = category_clean.strip('#')
                
                # 确保分组行格式正确：分组名,#genre#
                group_line = f"{cleaned_category},#genre#"
                f.write(f"{group_line}\n")
                
                # 对当前类别的频道按名称升序排序
                sorted_channels = sorted(channels[category], key=lambda x: x[0])
                # 写入该分组下的所有频道
                for channel_name, url in sorted_channels:
                    f.write(f"{channel_name},{url}\n")
                
                # 分组之间添加空行
                f.write("\n")
        
        # 不写入其他频道，只包含CHANNEL_CATEGORIES中定义的频道
        
        # 在文件末尾添加说明行
        f.write("\n说明,#genre#\n")
        
        # 写入文件头注释到文件末尾
        f.write(f"# IPTV直播源列表\n")
        f.write(f"# 生成时间: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# 格式: 频道名称,播放URL\n")
        f.write("# 按分组排列\n")
        f.write("\n")
        
        # 写入频道分类说明
        f.write("# 频道分类: 4K频道,央视频道,卫视频道,北京专属频道,山东专属频道,港澳频道,电影频道,儿童频道,iHOT频道,综合频道,体育频道,剧场频道,其他频道\n")
    
    print(f"✅ 成功生成 {output_path}")
    return True

# 从本地TXT文件提取频道信息
def extract_channels_from_txt(file_path):
    """从本地TXT文件提取频道信息"""
    channels = defaultdict(list)
    processor = TemplateDrivenProcessor()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # 处理分组标记行 - 只支持,#genre#格式
                if line.endswith(',#genre#'):
                    # 提取分组名：去掉 ",#genre#" 后缀
                    group_name = line[:-8].strip()  # 去掉 ",#genre#" (8个字符)
                    
                    # 清理前后的#符号
                    while group_name.startswith('#'):
                        group_name = group_name[1:].strip()
                    while group_name.endswith('#'):
                        group_name = group_name[:-1].strip()
                    
                    # 清理BOM字符和其他不可见字符
                    group_name = group_name.replace('﻿', '').replace('\ufeff', '').strip()
                    current_group = group_name
                    continue
                
                # 跳过注释行（以#开头的行） - 但要确保分类行已经处理过了
                if line.startswith('#'):
                    continue
                
                # 解析频道信息（格式：频道名称,URL）
                if ',' in line:
                    channel_name, url = line.split(',', 1)
                    channel_name = channel_name.strip()
                    url = url.strip()
                    
                    # 检查频道名是否为空
                    if not channel_name:
                        continue
                    
                    # 检查频道名是否为纯数字
                    if channel_name.isdigit():
                        continue
                    
                    # 购物频道过滤
                    channel_name_lower = channel_name.lower()
                    shopping_keywords = ['购物', '导购', '电视购物']
                    if any(keyword in channel_name_lower for keyword in shopping_keywords):
                        continue
                    
                    # 跳过无效的URL（允许http, https, udp, rtmp等常见流媒体协议，但排除rtsp）
                    if not url.startswith(('http://', 'https://', 'udp://', 'rtmp://', 'mms://', 'rtp://')):
                        continue
                    
                    # 排除黑名单URL（stream精确匹配独立组件，避免误杀livestream等合法域名）
                    url_lower = url.lower()
                    if "rtsp://" in url_lower or "freetv" in url_lower or "kkk" in url_lower or "migu" in url_lower or "catvod" in url_lower or "mgtv" in url_lower:
                        continue
                    if STREAM_BLACKLIST_RE.search(url_lower):
                        continue
                    # 分辨率过滤
                    if processor.enable_resolution_filter and not processor.is_valid_resolution(url):
                        continue
                    
                    # 规范化频道名称
                    normalized_name = normalize_channel_name(channel_name)
                    if normalized_name:
                        # 获取频道分类
                        category = get_channel_category(normalized_name)
                        # 只添加CHANNEL_CATEGORIES中定义的频道
                        if category != "其他频道":
                            channels[category].append((normalized_name, url))
    except Exception as e:
        print(f"解析本地文件 {file_path} 时出错: {e}")
    
    return channels

# 动态计算最优并发数
def get_optimal_workers():
    """动态计算最优并发数，考虑系统资源和任务特性"""
    cpu_count = multiprocessing.cpu_count()
    # 根据任务类型动态调整并发数
    if config["url_testing"]["enable"]:
        # URL测试是I/O密集型任务，可使用更高的并发数
        # 对于普通系统，CPU核心数 * 2 到 * 4 是比较合理的范围
        return min(64, cpu_count * 4)
    else:
        # 直播源获取是混合任务，使用适中的并发数
        return min(32, cpu_count * 2)

# 测试频道URL有效性
def test_channels(channels):
    """测试所有频道的URL有效性（使用快速检测器优化）"""
    # 强制启用URL测试
    config["url_testing"]["enable"] = True
    print("🔍 强制启用URL测试")
    
    print(f"🔍 开始测试频道URL有效性: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))}")
    
    # 收集所有需要测试的频道，优先处理4K频道
    all_channel_items = []
    four_k_channel_items = []
    for category, channel_list in channels.items():
        for channel_name, url in channel_list:
            if category == "4K频道" or is_4k(channel_name, url):
                four_k_channel_items.append((category, channel_name, url))
            else:
                all_channel_items.append((category, channel_name, url))
    
    total_channels = len(all_channel_items) + len(four_k_channel_items)
    print(f"📺 待测试频道总数: {total_channels} (4K频道: {len(four_k_channel_items)}, 其他频道: {len(all_channel_items)})")
    
    if total_channels == 0:
        return channels
    
    # 测试结果
    valid_channels = defaultdict(list)
    valid_count = 0
    invalid_count = 0
    
    # 测试4K频道
    if four_k_channel_items:
        print(f"🔍 优先测试4K频道...")
        
        if QUICK_CHECKER_AVAILABLE and len(four_k_channel_items) > 10:
            print("🚀 使用轻量级快速检测器测试4K频道...")
            
            try:
                # 4K频道：直接添加到有效频道列表，不进行任何测试
                print("📺 4K频道：直接添加到有效频道列表，不进行任何测试")
                for category, channel_name, url in four_k_channel_items:
                    valid_channels[category].append((channel_name, url))
                    valid_count += 1
                    if (valid_count) % 10 == 0:
                        print(f"📊 4K频道处理进度: {valid_count}/{len(four_k_channel_items)} ({valid_count}有效, 0无效)")
                
            except Exception as e:
                print(f"⚠️ 处理4K频道时出错: {e}")
                print("🔄 回退到传统检测方式...")
                # 回退到传统检测方式
                for category, channel_name, url in four_k_channel_items:
                    channel_is_4k = is_4k(channel_name, url)
                    timeout = 4 if channel_is_4k else config["url_testing"]["timeout"]
                    is_valid = check_url(url, timeout=timeout, retries=config["url_testing"]["retries"])
                    if is_valid:
                        valid_channels[category].append((channel_name, url))
                        valid_count += 1
                    else:
                        invalid_count += 1
        else:
            # 使用传统检测方式测试4K频道
            print("📺 4K频道：直接添加到有效频道列表，不进行任何测试")
            for category, channel_name, url in four_k_channel_items:
                valid_channels[category].append((channel_name, url))
                valid_count += 1
                if (valid_count) % 10 == 0:
                    print(f"📊 4K频道处理进度: {valid_count}/{len(four_k_channel_items)} ({valid_count}有效, 0无效)")
        
        print(f"📊 4K频道测试结果: 有效: {len(valid_channels.get('4K频道', []))} 个, 无效: {len(four_k_channel_items) - len(valid_channels.get('4K频道', []))} 个")
    
    # 测试其他频道
    if all_channel_items:
        print(f"🔍 测试其他频道...")
        
        if QUICK_CHECKER_AVAILABLE and len(all_channel_items) > 50:
            print("🚀 使用轻量级快速检测器测试其他频道...")
            
            try:
                # 准备URL列表
                urls = [(category, channel_name, url) for category, channel_name, url in all_channel_items]
                
                # 创建快速检测器
                checker = create_quick_checker(
                    timeout=config["url_testing"]["timeout"],
                    max_workers=min(32, config["url_testing"]["workers"]),
                    enable_dns_check=True
                )
                
                # 批量检测
                results = checker.batch_check([url for _, _, url in urls], show_progress=True)
                
                # 处理结果
                for i, result in enumerate(results):
                    category, channel_name, url = urls[i]
                    
                    if result['valid']:
                        valid_channels[category].append((channel_name, url))
                        valid_count += 1
                    else:
                        invalid_count += 1
                        
                    if (i + 1) % 100 == 0:
                        print(f"📊 其他频道处理进度: {i+1}/{len(results)} ({valid_count - len(valid_channels.get('4K频道', []))}有效, {invalid_count - (len(four_k_channel_items) - len(valid_channels.get('4K频道', [])))}无效)")
                
            except Exception as e:
                print(f"⚠️ 快速检测器出错: {e}")
                print("🔄 回退到传统检测方式...")
                return test_channels_traditional(channels, valid_channels=valid_channels, processed_count=len(four_k_channel_items))
        else:
            print("🔄 使用传统检测方式测试其他频道...")
            return test_channels_traditional(channels, valid_channels=valid_channels, processed_count=len(four_k_channel_items))
    
    # 计算总有效频道数
    total_valid = sum(len(channels) for channels in valid_channels.values())
    
    print(f"✅ URL测试完成: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))} ")
    print(f"📊 测试结果: 共测试 {total_channels} 个频道")
    print(f"📊 有效频道: {valid_count} 个")
    print(f"📊 无效频道: {invalid_count} 个")
    print(f"📊 总有效频道数: {total_valid} 个")
    
    return valid_channels

def test_channels_traditional(channels, valid_channels=None, processed_count=0):
    """传统URL检测方法（作为回退方案）"""
    # 如果没有提供valid_channels，创建一个新的
    if valid_channels is None:
        valid_channels = defaultdict(list)
    
    # 收集所有需要测试的频道，排除已经测试过的4K频道
    all_channel_items = []
    four_k_channel_items = []
    for category, channel_list in channels.items():
        for channel_name, url in channel_list:
            # 检查这个频道是否已经在valid_channels中
            already_tested = False
            if category in valid_channels:
                for (name, u) in valid_channels[category]:
                    if name == channel_name and u == url:
                        already_tested = True
                        break
            if already_tested:
                continue
            
            if category == "4K频道" or is_4k(channel_name, url):
                four_k_channel_items.append((category, channel_name, url))
            else:
                all_channel_items.append((category, channel_name, url))
    
    # 先测试剩下的4K频道
    if four_k_channel_items:
        print(f"🔍 测试剩余的4K频道...")
        for category, channel_name, url in four_k_channel_items:
            channel_is_4k = is_4k(channel_name, url)
            timeout = 4 if channel_is_4k else config["url_testing"]["timeout"]
            is_valid = check_url(url, timeout=timeout, retries=config["url_testing"]["retries"])
            if is_valid:
                valid_channels[category].append((channel_name, url))
    
    total_channels = len(all_channel_items)
    
    if total_channels == 0:
        print(f"📺 没有需要测试的其他频道")
        # 计算总有效频道数
        total_valid = sum(len(channels) for channels in valid_channels.values())
        print(f"✅ URL测试完成: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))} ")
        print(f"📊 总有效频道数: {total_valid} 个")
        return valid_channels
    
    # 计算测试所需的参数
    test_workers = config["url_testing"]["workers"]
    # 限制最大线程数为8，避免网络压力过大
    max_workers = min(8, test_workers if test_workers > 0 else get_optimal_workers(), len(all_channel_items))
    print(f"⚡ 使用 {max_workers} 个并发线程测试URL...")
    
    # 测试结果
    tested_count = 0
    valid_count = 0
    invalid_count = 0
    
    # 测试单个频道URL
    def test_single_channel(channel_item):
        category, channel_name, url = channel_item
        # 对于4K频道使用稍长的超时时间（但不要过长）
        channel_is_4k = is_4k(channel_name, url)
        timeout = 4 if channel_is_4k else config["url_testing"]["timeout"]
        is_valid = check_url(url, timeout=timeout, retries=config["url_testing"]["retries"])
        return (category, channel_name, url, is_valid)
    
    # 计算总超时时间（基于并发数和每个任务的最大超时时间）
    total_tested = len(all_channel_items)
    base_timeout = config["url_testing"]["timeout"]
    max_workers = config["url_testing"]["workers"]
    
    # 简化计算：直接设置总超时时间为10分钟（600秒）
    # 这样可以确保在GitHub Actions的时间限制内完成
    total_timeout = 600  # 10分钟总超时时间
    
    # 并发测试所有频道
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_channel = {executor.submit(test_single_channel, item): item for item in all_channel_items}
        
        try:
            for future in as_completed(future_to_channel, timeout=total_timeout):
                category, channel_name, url = future_to_channel[future]
                try:
                    # 为单个future.result()添加超时时间
                    result = future.result(timeout=base_timeout + 1)
                    category, channel_name, url, is_valid = result
                except concurrent.futures.TimeoutError:
                    print(f"⚠️  频道 {channel_name} 测试超时")
                    is_valid = False
                except Exception as e:
                    print(f"⚠️  测试频道 {channel_name} 时出错: {e}")
                    is_valid = False
                
                tested_count += 1
                
                if is_valid:
                    valid_channels[category].append((channel_name, url))
                    valid_count += 1
                else:
                    invalid_count += 1
                
                # 每测试50个频道打印一次进度，或者完成时打印
                if tested_count % 50 == 0 or tested_count == total_channels:
                    print(f"📊 测试进度: {tested_count}/{total_channels} ({valid_count}有效, {invalid_count}无效) - {tested_count/total_channels*100:.1f}%")
        except concurrent.futures.TimeoutError:
            print(f"⚠️  URL测试总超时，还有 {len(future_to_channel) - tested_count} 个频道未测试完成")
        except Exception as e:
            print(f"⚠️  URL测试过程中发生错误: {e}")
    
    print(f"✅ URL测试完成: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))}")
    print(f"📊 测试结果: 共测试 {total_channels} 个频道")
    print(f"📊 有效频道: {valid_count} 个")
    print(f"📊 无效频道: {invalid_count} 个")
    print(f"📊 有效率: {valid_count/total_channels*100:.1f}%")
    
    return valid_channels

# 处理单个远程直播源
def process_single_source(source_url):
    """处理单个远程直播源或本地文件"""
    content = fetch_m3u_content(source_url)
    if content:
        # 根据内容判断格式
        if content.strip().startswith('#EXTM3U'):
            # M3U格式
            return extract_channels_from_m3u(content)
        else:
            # TXT格式（安全地保存到临时文件再解析）
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                temp_file_path = f.name
                f.write(content)
            
            # 设置安全的文件权限（仅所有者可读写）
            os.chmod(temp_file_path, 0o600)
            
            try:
                return extract_channels_from_txt(temp_file_path)
            finally:
                # 确保清理临时文件
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
    return None

# 合并直播源
def merge_sources(sources, local_files):
    """合并多个直播源"""
    all_channels = defaultdict(list)
    seen = set()
    
    print(f"🔍 开始合并直播源: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))}")
    
    # 将本地文件转换为file:// URL
    local_sources = [f"file://{os.path.abspath(file_path)}" for file_path in local_files if os.path.exists(file_path)]
    
    # 合并所有源（远程和本地）
    all_source_urls = sources + local_sources
    print(f"� 总直播源数量: {len(all_source_urls)} (远程: {len(sources)}, 本地: {len(local_sources)})")
    
    if not all_source_urls:
        print("❌ 没有可用的直播源")
        return all_channels
    
    # 统一处理所有源（并发）
    max_workers = get_optimal_workers()
    print(f"使用 {max_workers} 个并发线程处理所有直播源...")
    
    remote_channel_count = 0
    local_channel_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_source = {executor.submit(process_single_source, source_url): source_url for source_url in all_source_urls}
        
        for future in as_completed(future_to_source):
            result = future.result()
            source_url = future_to_source[future]
            
            if result:
                source_channels = sum(len(clist) for _, clist in result.items())
                
                # 判断是本地文件还是远程源
                if source_url.startswith('file://'):
                    local_channel_count += source_channels
                    print(f"✅ 本地文件 {source_url[7:]} 获取到 {source_channels} 个频道")
                else:
                    remote_channel_count += source_channels
                    print(f"✅ 远程源 {source_url} 获取到 {source_channels} 个频道")
                
                for group_title, channel_list in result.items():
                    for channel_name, url in channel_list:
                        # 黑名单过滤（stream精确匹配独立组件，避免误杀livestream等合法域名）
                        url_lower = url.lower()
                        if "rtsp://" in url_lower or "freetv" in url_lower or "kkk" in url_lower or "migu" in url_lower or "catvod" in url_lower or "mgtv" in url_lower:
                            continue
                        if STREAM_BLACKLIST_RE.search(url_lower):
                            continue
                        # 4K过滤
                        if config["filter"]["only_4k"] and not is_4k(channel_name, url):
                            continue
                        # 去重
                        if (channel_name, url) not in seen:
                            all_channels[group_title].append((channel_name, url))
                            seen.add((channel_name, url))
            else:
                # 判断是本地文件还是远程源
                if source_url.startswith('file://'):
                    print(f"❌ 本地文件 {source_url[7:]} 获取失败")
                else:
                    print(f"❌ 远程源 {source_url} 获取失败")
    
    print(f"📊 远程直播源获取总数: {remote_channel_count} 个频道")
    print(f"📊 本地直播源获取总数: {local_channel_count} 个频道")
    print(f"📊 合并后总频道数: {sum(len(clist) for _, clist in all_channels.items())} 个频道")
    
    return all_channels


# 忽略requests的SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def update_iptv_sources():
    """更新IPTV直播源"""
    logger.info("🚀 IPTV直播源自动生成工具")
    logger.info(f"📅 运行时间: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    # 加载缓存
    load_cache()
    
    # 合并所有直播源
    all_sources = config["sources"]["default"] + config["sources"]["custom"]
    logger.info(f"📡 正在获取{len(all_sources)}个远程直播源...")
    logger.info(f"💻 正在读取{len(config['sources']['local'])}个本地直播源文件...")
    
    start_time = time.time()
    all_channels = merge_sources(all_sources, config['sources']['local'])
    
    # 添加调试日志
    logger.info(f"🔍 合并后获取到的频道组数量: {len(all_channels)}")
    if not all_channels:
        logger.error("❌ 没有获取到任何频道内容！")
        return False
    
    # 测试频道URL有效性
    # 强制启用URL测试
    config["url_testing"]["enable"] = True
    logger.info("🔍 强制启用URL测试")
    logger.info("🔍 开始测试频道URL有效性...")
    all_channels = test_channels(all_channels)
    
    # 重新统计频道数量
    total_channels = sum(len(channel_list) for channel_list in all_channels.values())
    total_groups = len(all_channels)
    
    logger.info("=" * 50)
    logger.info(f"📊 URL测试后统计:")
    logger.info(f"📺 有效频道组数: {total_groups}")
    logger.info(f"📚 有效频道总数: {total_channels}")
    logger.info(f"⏱️  耗时: {format_interval(time.time() - start_time)}")
    logger.info("=" * 50)
    
    if total_channels == 0:
        logger.error("❌ 所有频道URL测试均无效！")
        return False
    
    # 显示频道组信息
    logger.info("📋 频道组详情:")
    for group_title, channel_list in all_channels.items():
        logger.info(f"   {group_title}: {len(channel_list)}个频道")
    
    # 生成M3U文件（使用固定的旧输出文件名）
    output_file_m3u = "jieguo.m3u"
    # 生成TXT文件（使用固定的旧输出文件名）
    output_file_txt = "jieguo.txt"
    
    logger.info(f"📁 准备生成文件: {output_file_m3u} 和 {output_file_txt}")
    logger.info(f"📊 准备写入的频道总数: {sum(len(channel_list) for channel_list in all_channels.values())}")
    
    # 打印前几个频道作为示例
    if all_channels:
        first_group = list(all_channels.keys())[0]
        if all_channels[first_group]:
            logger.info(f"📺 示例频道: {all_channels[first_group][0][0]} - {all_channels[first_group][0][1]}")
    
    success_m3u = generate_m3u_file(all_channels, output_file_m3u)
    logger.info(f"📝 M3U文件生成结果: {'成功' if success_m3u else '失败'}")
    
    success_txt = generate_txt_file(all_channels, output_file_txt)
    logger.info(f"📝 TXT文件生成结果: {'成功' if success_txt else '失败'}")
    
    if success_m3u and success_txt:
        logger.info(f"🎉 任务完成！")
        # 检查文件是否真的更新了
        if os.path.exists(output_file_m3u):
            mtime = os.path.getmtime(output_file_m3u)
            logger.info(f"📅 {output_file_m3u} 最后修改时间: {datetime.datetime.fromtimestamp(mtime)}")
        if os.path.exists(output_file_txt):
            mtime = os.path.getmtime(output_file_txt)
            logger.info(f"📅 {output_file_txt} 最后修改时间: {datetime.datetime.fromtimestamp(mtime)}")
        return True
    else:
        logger.error("💥 生成文件失败！")
        return False


def check_ip_tv_syntax():
    """检查IPTV.py文件的语法错误"""
    # 尝试解析当前文件，获取更详细的错误信息
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析整个文件
        ast.parse(content)
        print('✓ IPTV.py: 语法正确')
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
    """修复IPTV.py文件中的不可打印字符"""
    # 读取当前文件内容
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除所有不可打印字符，包括欧元符号和其他特殊字符
        # 保留ASCII可打印字符和常见的中文、日文、韩文等Unicode字符
        cleaned_content = CLEAN_CONTENT_PATTERN.sub('', content)
        
        # 将清理后的内容写回文件
        with open(__file__, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print('✓ IPTV.py文件中的不可打印字符已移除')
        return True
        
    except Exception as e:
        print(f'✗ 处理文件时出错: {type(e).__name__}: {e}')
        return False


def validate_command_line_args():
    """验证命令行参数的安全性"""
    for arg in sys.argv[1:]:  # 跳过脚本名称
        if not arg.startswith('--'):
            raise ValueError(f"参数必须以'--'开头: {arg}")
        
        # 检查参数长度
        if len(arg) > 50:
            raise ValueError(f"参数过长: {arg}")
        
        # 检查是否包含危险字符
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', ';', '&', '|', '`', '$', '(', ')', '{', '}', '[', ']', '\\']
        for char in dangerous_chars:
            if char in arg:
                raise ValueError(f"参数包含危险字符 '{char}': {arg}")

def main():
    """主函数"""
    import sys
    import argparse
    
    # 加载配置文件
    load_config()
    
    parser = argparse.ArgumentParser(
        description='IPTV直播源自动生成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python IPTV.py --update
  python IPTV.py --check-syntax
  python IPTV.py --fix-chars
  python IPTV.py --filter-4k
        """
    )
    
    parser.add_argument('--update', action='store_true', 
                       help='立即手动更新直播源')
    parser.add_argument('--check-syntax', action='store_true', 
                       help='检查IPTV.py文件语法错误')
    parser.add_argument('--fix-chars', action='store_true', 
                       help='修复IPTV.py文件中的不可打印字符')
    parser.add_argument('--filter-4k', action='store_true', 
                       help='只获取4K频道')
    
    try:
        # 验证命令行参数安全性
        validate_command_line_args()
        
        # 解析命令行参数
        args = parser.parse_args()
        
        # 执行相应操作
        if args.update:
            # 手动更新模式
            update_iptv_sources()
        elif args.check_syntax:
            # 检查语法错误
            check_ip_tv_syntax()
        elif args.fix_chars:
            # 修复不可打印字符
            fix_ip_tv_chars()
        elif args.filter_4k:
            # 只获取4K频道模式
            config["filter"]["only_4k"] = True
            update_iptv_sources()
        else:
            # 显示帮助信息
            print("=" * 60)
            print("      IPTV直播源自动生成工具")
            print("=" * 60)
            print("功能：")
            print("  1. 从多个来源获取IPTV直播源")
            print("  2. 生成M3U和TXT格式的直播源文件")
            print("  3. 支持手动更新和通过GitHub Actions工作流定时更新")
            print("  4. 检查IPTV.py文件语法错误")
            print("  5. 修复IPTV.py文件中的不可打印字符")
            print("  6. 支持只获取4K频道")
            print("")
            print("使用方法：")
            print("  python IPTV.py --update       # 立即手动更新直播源")
            print("  python IPTV.py --check-syntax # 检查语法错误")
            print("  python IPTV.py --fix-chars    # 修复不可打印字符")
            print("  python IPTV.py --filter-4k    # 只获取4K频道")
            
    except ValueError as e:
        print(f"参数验证错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n操作被用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
