#!/usr/bin/env python3
"""
IPTV直播源自动生成工具 - 简化版
功能：从多个来源获取IPTV直播源并生成M3U文件
核心特性：标准频道分类 + 频道列表别名
借鉴fetch.py的优秀解析逻辑和错误处理
"""

import os
import re
import sys
import json
import requests
import logging
import time
import tempfile
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone, timedelta

# 导入配置
try:
    import config
except ImportError:
    print("错误: 找不到config.py配置文件")
    sys.exit(1)

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

def parse_template(template_file):
    """解析频道模板文件 - 借鉴fetch.py的简洁逻辑"""
    template_channels = OrderedDict()
    current_category = None

    try:
        with open(template_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "#genre#" in line:
                        current_category = line.split(",")[0].strip()
                        template_channels[current_category] = []
                        logger.debug(f"解析分类: {current_category}")
                    elif current_category:
                        channel_name = line.split(",")[0].strip()
                        template_channels[current_category].append(channel_name)
                        logger.debug(f"解析频道: {channel_name}")

        logger.info(f"模板解析完成: {len(template_channels)} 个分类")
        return template_channels
        
    except Exception as e:
        logger.error(f"解析模板文件失败 {template_file}: {e}")
        return OrderedDict()

def fetch_channels(url):
    """获取并解析源数据 - 借鉴fetch.py的逻辑"""
    channels = OrderedDict()

    try:
        logger.info(f"获取源数据: {url}")
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        lines = response.text.split("\n")
        current_category = None
        
        # 自动检测格式
        is_m3u = any("#EXTINF" in line for line in lines[:15])
        source_type = "m3u" if is_m3u else "txt"
        logger.info(f"检测到格式: {source_type}")

        if is_m3u:
            # 解析M3U格式
            for line in lines:
                line = line.strip()
                if line.startswith("#EXTINF"):
                    match = re.search(r'group-title="(.*?)",(.*)', line)
                    if match:
                        current_category = match.group(1).strip()
                        channel_name = match.group(2).strip()
                        if current_category not in channels:
                            channels[current_category] = []
                elif line and not line.startswith("#"):
                    channel_url = line.strip()
                    if current_category and channel_name:
                        channels[current_category].append((channel_name, channel_url))
        else:
            # 解析TXT格式
            for line in lines:
                line = line.strip()
                if "#genre#" in line:
                    current_category = line.split(",")[0].strip()
                    channels[current_category] = []
                elif current_category:
                    match = re.match(r"^(.*?),(.*?)$", line)
                    if match:
                        channel_name = match.group(1).strip()
                        channel_url = match.group(2).strip()
                        channels[current_category].append((channel_name, channel_url))
                    elif line:
                        channels[current_category].append((line, ''))

        if channels:
            categories = ", ".join(channels.keys())
            logger.info(f"获取成功✅，包含分类: {categories}")
        else:
            logger.warning(f"获取失败❌: 未能解析到频道数据")

    except requests.RequestException as e:
        logger.error(f"获取失败❌ {url}: {e}")
    except Exception as e:
        logger.error(f"解析失败❌ {url}: {e}")

    return channels

def match_channels(template_channels, all_channels, channel_mapping=None):
    """匹配频道 - 支持别名匹配"""
    matched_channels = OrderedDict()
    channel_mapping = channel_mapping or {}

    logger.info(f"开始频道匹配: 模板{len(template_channels)}分类, 源{len(all_channels)}分类")

    for category, channel_list in template_channels.items():
        matched_channels[category] = OrderedDict()
        logger.debug(f"处理分类: {category} ({len(channel_list)}频道)")
        
        for channel_name in channel_list:
            # 1. 精确匹配
            exact_matches = []
            for online_category, online_channel_list in all_channels.items():
                for online_channel_name, online_channel_url in online_channel_list:
                    if channel_name == online_channel_name:
                        exact_matches.append(online_channel_url)
            
            if exact_matches:
                matched_channels[category][channel_name] = exact_matches
                logger.debug(f"精确匹配: {channel_name} -> {len(exact_matches)}个URL")
            
            # 2. 别名匹配
            if channel_name in channel_mapping:
                alias_matches = []
                for alias in channel_mapping[channel_name]:
                    for online_category, online_channel_list in all_channels.items():
                        for online_channel_name, online_channel_url in online_channel_list:
                            if alias == online_channel_name:
                                alias_matches.append(online_channel_url)
                
                if alias_matches:
                    if channel_name in matched_channels:
                        matched_channels[channel_name].extend(alias_matches)
                    else:
                        matched_channels[category][channel_name] = alias_matches
                    logger.debug(f"别名匹配: {channel_name} -> {len(alias_matches)}个URL")

    # 统计匹配结果
    total_matched = sum(len(channels) for channels in matched_channels.values() 
                      for channels in channels.values())
    logger.info(f"频道匹配完成: 总计匹配{total_matched}个URL")

    return matched_channels

def generate_output(matched_channels, template_channels, output_file_m3u="jieguo.m3u", output_file_txt="jieguo.txt"):
    """生成输出文件 - 简化的版本，只保留核心功能"""
    
    logger.info(f"开始生成输出文件: {output_file_m3u}, {output_file_txt}")
    
    with open(output_file_m3u, "w", encoding="utf-8") as f_m3u, \
         open(output_file_txt, "w", encoding="utf-8") as f_txt:
        
        # 写入M3U头部
        f_m3u.write("#EXTM3U\n")
        
        # 处理每个分类
        for category, channel_list in template_channels.items():
            if category in matched_channels:
                f_txt.write(f"{category},#genre#\n")
                
                for channel_name in channel_list:
                    if channel_name in matched_channels[category]:
                        urls = matched_channels[category][channel_name]
                        
                        for url in urls:
                            # 写入M3U
                            logo_url = f"https://gcore.jsdelivr.net/gh/yuanzl77/TVlogo@master/png/{channel_name}.png"
                            f_m3u.write(f'#EXTINF:-1 tvg-name="{channel_name}" tvg-logo="{logo_url}" group-title="{category}",{channel_name}\n')
                            f_m3u.write(f"{url}\n")
                            
                            # 写入TXT
                            f_txt.write(f"{channel_name},{url}\n")
                
                f_txt.write("\n")  # 分类间空行
    
    logger.info(f"输出文件生成完成")

def main():
    """主函数 - 简化版本"""
    print("🚀 IPTV直播源自动生成工具")
    print(f"📅 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 读取配置
    config = {}
    try:
        if os.path.exists('iptv_config.json'):
            with open('iptv_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("✅ 配置文件加载成功")
    except Exception as e:
        logger.error(f"❌ 配置文件加载失败: {e}")
        config = {}
    
    # 获取源URL列表
    source_urls = getattr(config, 'source_urls', config.get('sources', {}).get('default', []))
    if not source_urls:
        try:
            source_urls = config.source_urls
        except AttributeError:
            source_urls = []
    
    if not source_urls:
        logger.error("❌ 未找到源URL配置")
        return
    
    logger.info(f"🔧 使用标准频道分类 + 别名匹配架构")
    
    # 处理所有源
    all_channels = OrderedDict()
    for url in source_urls:
        channels = fetch_channels(url)
        for category, channel_list in channels.items():
            if category not in all_channels:
                all_channels[category] = []
            all_channels[category].extend(channel_list)
    
    # 获取频道别名映射
    channel_mapping = getattr(config, 'channel_mapping', {})
    
    # 使用默认模板结构
    template_channels = OrderedDict()
    # 这里可以添加标准频道分类，或者从模板文件读取
    
    # 如果没有模板文件，使用获取到的所有频道
    if not template_channels:
        logger.info("未找到模板文件，使用获取到的频道结构")
        template_channels = OrderedDict()
        for category, channel_list in all_channels.items():
            template_channels[category] = []
            seen_channels = set()
            for channel_name, url in channel_list:
                if channel_name not in seen_channels:
                    template_channels[category].append(channel_name)
                    seen_channels.add(channel_name)
    
    # 匹配频道
    matched_channels = match_channels(template_channels, all_channels, channel_mapping)
    
    # 生成输出
    output_m3u = config.get('output', {}).get('m3u_file', 'jieguo.m3u')
    output_txt = config.get('output', {}).get('txt_file', 'jieguo.txt')
    
    generate_output(matched_channels, template_channels, output_m3u, output_txt)
    
    logger.info("🎉 IPTV源生成完成")

if __name__ == "__main__":
    main()
DEFAULT_CONFIG = {
    "sources": {
        "default": [],  # 从unified_sources导入，可在配置文件中覆盖
        "local": [],    # 本地直播源文件列表
        "custom": []    # 用户自定义直播源URL列表
    },
    "template": {
        "enabled": True,     # 启用模板驱动处理
        "file": "channels_template.txt",  # 频道模板文件路径
        "preserve_order": True,  # 保留原模板中的频道顺序
        "use_alias_matching": True  # 启用别名匹配
    },
    "filter": {
        "resolution": True,    # 开启分辨率过滤
        "min_resolution": [1920, 1080],  # 最低分辨率要求
        "only_4k": False       # 是否只获取4K频道
    },
    "url_testing": {
        "enable": False,   # 禁用URL有效性测试以避免超时 - 2026-01-01优化
        "timeout": 3,      # URL测试超时时间（秒）- 增加到3秒
        "retries": 0,      # URL测试重试次数
        "workers": 8      # URL测试并发数 - 降低到8个线程避免网络压力
    },
    "network": {
        "ip_version_priority": "ipv4",  # IP版本优先级: ipv4, ipv6, auto
        "url_blacklist": [],            # URL黑名单
        "enable_ipv6": True,           # 启用IPv6支持
        "timeout": 30,                 # 网络请求超时
        "retries": 3                   # 网络请求重试次数
    },
    "matching": {
        "channel_mapping": {},         # 频道别名映射表
        "enable_fuzzy_match": True,    # 启用模糊匹配
        "fuzzy_threshold": 0.8,        # 模糊匹配阈值
        "enable_aliases": True,        # 启用别名匹配
        "case_sensitive": False        # 频道名称匹配是否区分大小写
    },
    "cache": {
        "expiry_time": 3600,  # 缓存有效期（秒）
        "file": "source_cache.json"  # 缓存文件路径
    },
    "output": {
        "m3u_file": "jieguo.m3u",  # M3U输出文件
        "txt_file": "jieguo.txt",   # TXT输出文件
        "include_invalid": True,    # 在输出中包含无效频道
        "separate_valid_invalid": False,  # 分别保存有效和无效频道
        "preserve_categories": True  # 保留频道分类结构
    },
    "logging": {
        "level": "INFO",            # 日志级别
        "file": "iptv_update.log",  # 日志文件
        "enable_console": True,     # 启用控制台输出
        "enable_file": True         # 启用文件输出
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

# 清晰度正则表达式 - 用于识别高清线路
HD_PATTERNS = [
    # 4K及以上
    r'[48]k',
    r'2160[pdi]',
    r'uhd',
    r'超高清',
    r'4k',
    # 2K
    r'1440[pdi]',
    r'qhd',
    # 1080P及以上
    r'1080[pdi]',
    r'fhd',
    # 其他高清标识
    r'高清',
    r'超清',
    r'hd',
    r'high.?definition',
    r'high.?def',
    # 特定的高清标识
    r'hdmi',
    r'蓝光',
    r'blue.?ray',
    r'hd.?live',
    # 码率标识
    r'[89]m',
    r'[1-9]\d+m',
    # 特定的URL参数标识
    r'quality=high',
    r'resolution=[1-9]\d{3}',
    r'hd=true',
    r'fhd=true'
]

HD_REGEX = re.compile('|'.join(HD_PATTERNS), re.IGNORECASE)

# 预编译常用正则表达式
URL_REGEX = re.compile(r'(?:https?|udp|rtsp|rtmp|mms|rtp)://', re.IGNORECASE)

# 预编译分辨率和质量相关的正则表达式
HIGH_DEF_PATTERNS = re.compile(r'(1080[pdi]|1440[pdi]|2160[pdi]|fhd|uhd|超高清)', re.IGNORECASE)
RES_PATTERNS = [
    re.compile(r'(\d{3,4})[pdi]'),  # 如1080p, 2160i
    re.compile(r'(\d+)x(\d+)'),     # 如1920x1080, 3840x2160
    re.compile(r'(\d+)_(\d+)'),     # 如1920_1080
    re.compile(r'res=([1-9]\d+)'),       # 如res=1080
    re.compile(r'resolution=([1-9]\d+)x?([1-9]\d+)'),  # 如resolution=1920x1080
    re.compile(r'width=([1-9]\d+).*?height=([1-9]\d+)'),  # 如width=1920 height=1080
]

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

# 获取URL列表
def get_urls_from_file(file_path):
    """从文件中读取URL列表"""
    urls = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            print(f"读取URL文件时出错: {e}")
    return urls

# 测试频道过滤
def should_exclude_url(url):
    """检查是否应该排除特定URL（测试频道过滤）"""
    if not url:
        return True
    
    # 测试频道过滤：过滤example、demo、sample等关键词
    test_patterns = ['example', 'demo', 'sample', 'samples']
    url_lower = url.lower()
    for pattern in test_patterns:
        if pattern in url_lower:
            return True
    
    # 过滤example域名
    if 'example.com' in url_lower or 'example.org' in url_lower:
        return True
    
    return False

# 分辨率过滤

def is_high_quality(line):
    """判断线路是否为高清线路（1080P以上）"""
    # 从line中提取频道名称和URL
    if 'http://' in line or 'https://' in line:
        # 提取URL之前的部分作为频道名称
        channel_name = line.split('http://')[0].split('https://')[0].strip()
        # 提取URL部分
        url_part = line[len(channel_name):].strip()
    else:
        channel_name = line.strip()
        url_part = ''
    
    # 检查频道名称中的高清标识
    if HIGH_DEF_PATTERNS.search(channel_name):
        return True
    
    # 检查其他高清标识
    channel_name_lower = channel_name.lower()
    # 高清标识列表
    hd_keywords = ['高清', '超清', 'hd', 'high definition', 'high def']
    # 低质量标识列表
    low_quality_keywords = ['360', '480', '576', '标清', 'sd', 'low']
    
    # 检查是否包含高清标识且不包含低质量标识
    if any(hd in channel_name_lower for hd in hd_keywords) and not any(low in channel_name_lower for low in low_quality_keywords):
        return True
    
    # 分辨率过滤：如果开启了分辨率过滤，检查是否满足最小分辨率要求
    if config["filter"]["resolution"]:
        # 增强的分辨率检测
        combined_text = channel_name + ' ' + url_part
        
        for pattern in RES_PATTERNS:
            res_match = pattern.search(combined_text)
            if res_match:
                try:
                    if len(res_match.groups()) == 1:
                        # 垂直分辨率（如1080p）
                        res_value = int(res_match.group(1))
                        if res_value >= config["filter"]["min_resolution"][1]:
                            return True
                    elif len(res_match.groups()) == 2:
                        # 完整分辨率（如1920x1080）
                        width = int(res_match.group(1))
                        height = int(res_match.group(2))
                        if width >= config["filter"]["min_resolution"][0] and height >= config["filter"]["min_resolution"][1]:
                            return True
                except ValueError:
                    pass
    
    return False

def is_4k(channel_name, url):
    """判断频道是否为4K频道"""
    
    # 检查频道名称和URL中的4K标识
    combined_text = channel_name + ' ' + url
    
    # 检查是否包含4K标识
    if K4_PATTERNS.search(combined_text):
        return True
    
    # 检查频道分类
    if get_simple_category(channel_name) == "4K频道":
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
def check_url(url, timeout=2, retries=0):
    """检查URL是否可访问，支持重试机制"""
    # 先检查URL格式是否正确
    if not URL_REGEX.match(url):
        return False
    
    # 对于非HTTP/HTTPS协议的URL，直接返回True（这些协议无法通过HEAD请求验证）
    if not url.startswith(('http://', 'https://')):
        return True
    
    for attempt in range(retries + 1):
        try:
            # 使用HEAD请求以避免下载整个文件（仅适用于HTTP/HTTPS）
            # 添加Range头减少流量，只请求文件的第一个字节
            response = session.head(
                url, 
                timeout=timeout, 
                allow_redirects=True,  # 允许重定向以提高测试准确性
                headers={'Range': 'bytes=0-0'}  # 请求部分内容减少流量
            )
            # 检查状态码，2xx表示成功
            return response.status_code < 400
        except requests.exceptions.RequestException as e:
            # 如果是最后一次尝试或者是特定错误，返回False
            if attempt == retries:
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

# 获取IP地址
def get_ip_address():
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"获取IP地址失败: {e}")
        return "127.0.0.1"

# 检查IPv6支持
def check_ipv6_support():
    """检查系统是否支持IPv6"""
    try:
        socket.inet_pton(socket.AF_INET6, '::1')
        return True
    except Exception as e:
        logger.error(f"IPv6支持检查失败: {e}")
        return False

# 从M3U文件中提取频道信息
def extract_channels_from_m3u(content):
    """从M3U内容中提取频道信息"""
    channels = defaultdict(list)
    matches = re.findall(M3U_CHANNEL_PATTERN, content)
    
    for match in matches:
        tvg_name = match[0].strip() if match[0] else match[2].strip()
        channel_name = match[2].strip()
        url = match[3].strip()
        
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
        
        # 简化处理：直接使用频道名称，简单分类
        category = get_simple_category(channel_name)
        channels[category].append((channel_name, url))
    
    return channels

# 简化频道分类
def get_simple_category(channel_name):
    """简单的频道分类"""
    name_lower = channel_name.lower()
    
    # 4K频道
    if any(keyword in name_lower for keyword in ['4k', '2160p', '超高清', 'uhd']):
        return "4K频道"
    
    # 央视频道
    if any(keyword in name_lower for keyword in ['央视', 'cctv', 'cnn']):
        return "央视频道"
    
    # 卫视频道
    if any(keyword in name_lower for keyword in ['卫视', '东方卫视', '湖南卫视', '江苏卫视', '浙江卫视']):
        return "卫视频道"
    
    # 港澳台
    if any(keyword in name_lower for keyword in ['香港', '台湾', '澳门', 'hktv', 'cti', 'ctv']):
        return "港澳频道"
    
    # 电影频道
    if any(keyword in name_lower for keyword in ['电影', 'movie', 'cinema']):
        return "电影频道"
    
    # 儿童频道
    if any(keyword in name_lower for keyword in ['儿童', '少儿', '动画', '卡通', 'kids']):
        return "儿童频道"
    
    # 体育频道
    if any(keyword in name_lower for keyword in ['体育', 'sports', '足球', '篮球']):
        return "体育频道"
    
    # 综艺频道
    if any(keyword in name_lower for keyword in ['综艺', 'variety', '娱乐']):
        return "综艺频道"
    
    # 新闻频道
    if any(keyword in name_lower for keyword in ['新闻', 'news', '资讯']):
        return "新闻频道"
    
    # 音乐频道
    if any(keyword in name_lower for keyword in ['音乐', 'music', 'MTV']):
        return "音乐频道"
    
    # 默认分类
    return "综合频道"

# 从URL获取M3U内容
def fetch_m3u_content(url, max_retries=3, timeout=120):
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
            timeout = min(timeout * 1.5, 300)  # 最大超时5分钟
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
    
    print(f"📝 开始写入文件: {output_path} 时间: {datetime.now(timezone(timedelta(hours=8)))}")
    print(f"📊 写入前文件大小: {os.path.getsize(output_path) if os.path.exists(output_path) else 0} 字节")
    print(f"📊 写入前文件修改时间: {datetime.fromtimestamp(os.path.getmtime(output_path)) if os.path.exists(output_path) else '不存在'}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入文件头
        f.write("#EXTM3U x-tvg-url=\"https://kakaxi-1.github.io/IPTV/epg.xml\"\n")
        
        # 写入当前时间作为标记（北京时间UTC+8）
        f.write(f"# 生成时间: {datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
        
        # 按分类顺序写入频道
        written_count = 0
        # 定义标准分类顺序
        category_order = ["4K频道", "央视频道", "卫视频道", "港澳频道", "电影频道", "儿童频道", "体育频道", "综艺频道", "新闻频道", "音乐频道", "综合频道"]
        
        for category in category_order:
            if category in channels:
                # 对当前类别的频道按名称升序排序
                sorted_channels = sorted(channels[category], key=lambda x: x[0])
                for channel_name, url in sorted_channels:
                    # 写入频道信息
                    f.write(f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"{category}\",{channel_name}\n")
                    f.write(f"{url}\n")
                    written_count += 1
    
    print(f"📝 完成写入文件: {output_path} 时间: {datetime.now(timezone(timedelta(hours=8)))}")
    print(f"📊 写入后文件大小: {os.path.getsize(output_path)} 字节")
    print(f"📊 写入后文件修改时间: {datetime.fromtimestamp(os.path.getmtime(output_path))}")
    print(f"📊 实际写入频道数: {written_count}")
    return True

# 生成TXT文件
def generate_txt_file(channels, output_path):
    """生成TXT文件（参考BlackBird-Player的result.txt格式）"""
    print(f"正在生成 {output_path}...")
    
    # 更新时间戳
    timestamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入更新时间戳（参考BlackBird-Player格式）
        f.write("🕘️更新时间,#genre#\n")
        f.write(f"{timestamp}\n\n")
        
        # 按分类顺序写入频道
        category_order = ["4K频道", "央视频道", "卫视频道", "港澳频道", "电影频道", "儿童频道", "体育频道", "综艺频道", "新闻频道", "音乐频道", "综合频道"]
        
        for category in category_order:
            if category in channels and channels[category]:
                # 写入分组标题，使用格式: 分组名,#genre#
                f.write(f"{category},#genre#\n")
                
                # 对当前类别的频道按名称升序排序
                sorted_channels = sorted(channels[category], key=lambda x: x[0])
                # 写入该分组下的所有频道
                for channel_name, url in sorted_channels:
                    f.write(f"{channel_name},{url}\n")
                
                # 分组之间添加空行
                f.write("\n")
        
        # 在文件末尾添加说明行
        f.write("\n说明,#genre#\n")
        
        # 写入文件头注释到文件末尾
        f.write(f"# IPTV直播源列表\n")
        f.write(f"# 生成时间: {datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')}\n")
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
                    
                    # 跳过无效的URL（允许http, https, udp, rtsp, rtmp等常见流媒体协议）
                    if not url.startswith(('http://', 'https://', 'udp://', 'rtsp://', 'rtmp://', 'mms://', 'rtp://')):
                        continue
                    
                    # 简化处理：直接使用频道名称，简单分类
                    category = get_simple_category(channel_name)
                    channels[category].append((channel_name, url))
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
    if not config["url_testing"]["enable"]:
        print("📌 URL测试功能已禁用")
        return channels
    
    print(f"🔍 开始测试频道URL有效性: {datetime.now(timezone(timedelta(hours=8)))}")
    
    # 收集所有需要测试的频道
    all_channel_items = []
    for category, channel_list in channels.items():
        for channel_name, url in channel_list:
            all_channel_items.append((category, channel_name, url))
    
    total_channels = len(all_channel_items)
    print(f"📺 待测试频道总数: {total_channels}")
    
    if total_channels == 0:
        return channels
    
    # 测试结果
    valid_channels = defaultdict(list)
    valid_count = 0
    invalid_count = 0
    
    # 尝试使用快速检测器
    if QUICK_CHECKER_AVAILABLE and total_channels > 50:
        print("🚀 使用轻量级快速检测器进行批量检测...")
        
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
                    print(f"📊 处理进度: {i+1}/{len(results)} ({valid_count}有效, {invalid_count}无效)")
            
        except Exception as e:
            print(f"⚠️ 快速检测器出错: {e}")
            print("🔄 回退到传统检测方式...")
            return test_channels_traditional(channels)
    else:
        print("🔄 使用传统检测方式...")
        return test_channels_traditional(channels)
    
    print(f"✅ URL测试完成: {datetime.now(timezone(timedelta(hours=8)))}")
    print(f"📊 测试结果: 共测试 {total_channels} 个频道")
    print(f"📊 有效频道: {valid_count} 个")
    print(f"📊 无效频道: {invalid_count} 个")
    print(f"📊 有效率: {valid_count/total_channels*100:.1f}%")
    
    return valid_channels

def test_channels_traditional(channels):
    """传统URL检测方法（作为回退方案）"""
    # 收集所有需要测试的频道
    all_channel_items = []
    for category, channel_list in channels.items():
        for channel_name, url in channel_list:
            all_channel_items.append((category, channel_name, url))
    
    total_channels = len(all_channel_items)
    
    # 计算测试所需的参数
    test_workers = config["url_testing"]["workers"]
    # 限制最大线程数为8，避免网络压力过大
    max_workers = min(8, test_workers if test_workers > 0 else get_optimal_workers(), len(all_channel_items))
    print(f"⚡ 使用 {max_workers} 个并发线程测试URL...")
    
    # 测试结果
    valid_channels = defaultdict(list)
    tested_count = 0
    valid_count = 0
    invalid_count = 0
    
    # 测试单个频道URL
    def test_single_channel(channel_item):
        category, channel_name, url = channel_item
        # 对于4K频道使用稍长的超时时间（但不要过长）
        timeout = 4 if is_4k(channel_name, url) else config["url_testing"]["timeout"]
        is_valid = check_url(url, timeout=timeout, retries=config["url_testing"]["retries"])
        return (category, channel_name, url, is_valid)
    
    # 计算总超时时间（基于并发数和每个任务的最大超时时间）
    total_tested = len(all_channel_items)
    base_timeout = config["url_testing"]["timeout"]
    # 使用并发数和批次的概念，而不是任务总数
    # 假设所有任务分批执行，每批最多max_workers个
    batches = (total_tested + max_workers - 1) // max_workers  # 向上取整
    total_timeout = batches * (base_timeout + 2)  # 每批最多超时时间
    
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
    
    print(f"✅ URL测试完成: {datetime.now(timezone(timedelta(hours=8)))}")
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
    
    print(f"🔍 开始合并直播源: {datetime.now(timezone(timedelta(hours=8)))}")
    
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
    logger.info(f"📅 运行时间: {datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    # 加载缓存
    load_cache()
    
    start_time = time.time()
    
    # 检查是否启用模板驱动处理
    # 使用传统处理方式（简化版本）
    logger.info("📡 使用传统处理方式")
    return _update_with_traditional_method(start_time)

def _update_with_traditional_method(start_time):
    """使用传统方法更新直播源"""
    # 合并所有直播源
    all_sources = config["sources"]["default"] + config["sources"]["custom"]
    logger.info(f"📡 正在获取{len(all_sources)}个远程直播源...")
    logger.info(f"💻 正在读取{len(config['sources']['local'])}个本地直播源文件...")
    
    all_channels = merge_sources(all_sources, config['sources']['local'])
    
    # 添加调试日志
    logger.info(f"🔍 合并后获取到的频道组数量: {len(all_channels)}")
    if not all_channels:
        logger.error("❌ 没有获取到任何频道内容！")
        return False
    
    # 测试频道URL有效性
    if config["url_testing"]["enable"]:
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
    
    # 统计频道数量
    total_channels = sum(len(channel_list) for channel_list in all_channels.values())
    total_groups = len(all_channels)
    
    logger.info("=" * 50)
    logger.info(f"📊 统计信息:")
    logger.info(f"📡 直播源数量: {len(all_sources)}")
    logger.info(f"📺 频道组数: {total_groups}")
    logger.info(f"📚 总频道数: {total_channels}")
    logger.info(f"⏱️  耗时: {format_interval(time.time() - start_time)}")
    logger.info("=" * 50)
    
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
            logger.info(f"📅 {output_file_m3u} 最后修改时间: {datetime.fromtimestamp(mtime)}")
        if os.path.exists(output_file_txt):
            mtime = os.path.getmtime(output_file_txt)
            logger.info(f"📅 {output_file_txt} 最后修改时间: {datetime.fromtimestamp(mtime)}")
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
