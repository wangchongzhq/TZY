import requests
import re
from datetime import datetime
import time
from collections import defaultdict

# 导入核心模块
from core.config import get_config
from core.logging_config import setup_logging, get_logger, log_exception

# 设置日志
setup_logging()
logger = get_logger(__name__)

# 数据源列表
SOURCES = get_config('sources.collect_sources', [
    {"name": "iptv-org-cn", "url": "https://iptv-org.github.io/iptv/countries/cn.m3u"},
    {"name": "iptv-org-hk", "url": "https://iptv-org.github.io/iptv/countries/hk.m3u"},
    {"name": "iptv-org-mo", "url": "https://iptv-org.github.io/iptv/countries/mo.m3u"},
    {"name": "iptv-org-tw", "url": "https://iptv-org.github.io/iptv/countries/tw.m3u"},
    {"name": "iptv-org-all", "url": "https://iptv-org.github.io/iptv/index.m3u"},
    {"name": "fanmingming", "url": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/global.m3u"},
    {"name": "free-iptv", "url": "https://raw.githubusercontent.com/Free-IPTV/Countries/master/China.m3u"},
    {"name": "moonkeyhoo", "url": "https://ghfast.top/https://raw.githubusercontent.com/moonkeyhoo/iptv-api/master/output/result.m3u"},
    {"name": "kakaxi-ipv6", "url": "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv6.m3u"},
    {"name": "kakaxi-ipv4", "url": "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv4.txt"},
    {"name": "2025", "url": "http://106.53.99.30/2025.txt"},
    {"name": "9390107", "url": "http://tv.html-5.me/i/9390107.txt"},
    {"name": "Supprise0901", "url": "https://ghfast.top/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt"},
    {"name": "ffmking", "url": "https://ghfast.top/raw.githubusercontent.com/ffmking/tv1/main/888.txt"},
    {"name": "qingtingjjjjjjj", "url": "https://ghfast.top/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt"},
    {"name": "Heiwk", "url": "https://ghfast.top/https://raw.githubusercontent.com/Heiwk/iptv67/refs/heads/main/iptv.m3u"},
    ])

# 分类规则
CATEGORY_RULES = get_config('category.rules', {
    "央视": [
        r'CCTV', r'中央电视台', r'CGTN', r'央视'
    ],
    "卫视": [
        r'卫视', r'湖南卫视', r'浙江卫视', r'东方卫视', r'北京卫视', r'江苏卫视',
        r'安徽卫视', r'重庆卫视', r'东南卫视', r'甘肃卫视', r'广东卫视',
        r'广西卫视', r'贵州卫视', r'海南卫视', r'河北卫视', r'黑龙江卫视',
        r'河南卫视', r'湖北卫视', r'江西卫视', r'吉林卫视', r'辽宁卫视',
        r'山东卫视', r'深圳卫视', r'四川卫视', r'天津卫视', r'云南卫视'
    ],
    "港澳台": [
        r'凤凰', r'TVB', r'翡翠', r'明珠', r'本港', r'国际', r'澳视', r'澳门',
        r'华视', r'中视', r'台视', r'民视', r'三立', r'东森', r'星空', r'香港',
        r'澳門', r'台灣', r'台湾'
    ],
    "电影": [
        r'电影', r'电影频道'
    ],
    "综艺": [
        r'综艺', r'综艺频道'
    ],
    "体育": [
        r'体育', r'体育频道', r'CCTV5', r'CCTV5+', r'风云足球', r'高尔夫', r'网球'
    ],
    "少儿": [
        r'少儿', r'卡通', r'动漫', r'CCTV少儿', r'金鹰卡通', r'卡酷少儿'
    ],
    "新闻": [
        r'新闻', r'资讯', r'财经', r'CCTV新闻'
    ],
    "教育": [
        r'教育', r'学习', r'教学', r'考试'
    ],
    "音乐": [
        r'音乐', r'音乐频道', r'MTV', r'MTV音乐', r'风云音乐'
    ],
    "戏曲": [
        r'戏曲', r'京剧', r'越剧', r'黄梅戏', r'豫剧', r'评剧', r'昆曲'
    ],
    "购物": [
        r'购物', r'导购', r'电视购物'
    ],
    "其他": [
        r'其他', r'综合', r'影视', r'高清'
    ]
})

# 过滤规则
FILTER_RULES = get_config('filter.rules', {
    "exclude_patterns": [
        r'测试', r'广告', r'购物', r'导购', r'电视购物', r'付费', r'加密',
        r'4K', r'8K', r'超清', r'高清',  # 可以根据需要保留或移除
        r'备用', r'备用线路', r'备用源'
    ],
    "include_patterns": [
        r'CCTV', r'卫视', r'央视', r'凤凰', r'TVB'
    ],
    "exclude_suffixes": [
        r'\.ts$', r'\.m3u8$', r'\.flv$'  # 可以根据需要保留或移除
    ],
    "include_suffixes": [
        r'\.m3u$', r'\.txt$'
    ]
})

# 输出文件
OUTPUT_FILE = get_config('output.file', 'ipzy_channels.txt')

# 网络设置
NETWORK_CONFIG = get_config('network.config', {
    "timeout": 10,
    "max_retries": 3,
    "verify_ssl": False
})

# 日志设置
LOG_CONFIG = get_config('logging.config', {
    "level": "INFO",
    "log_file": "logs/collect_ipzy.log",
    "log_rotation": "daily"
})

# 其他配置
OTHER_CONFIG = get_config('other.config', {
    "max_channels": 1000,
    "sort_by_category": True,
    "remove_duplicates": True
})

# 加载所有配置
logger.info("配置加载完成")
logger.debug(f"数据源列表: {len(SOURCES)} 个源")
logger.debug(f"分类规则: {list(CATEGORY_RULES.keys())}")
logger.debug(f"输出文件: {OUTPUT_FILE}")

# 主要执行函数

def main():
    """主函数"""
    try:
        logger.info("开始执行IPTV频道收集脚本")
        
        # 记录开始时间
        start_time = time.time()
        
        # 收集所有频道
        channels = collect_all_channels()
        
        # 过滤频道
        filtered_channels = filter_channels(channels)
        
        # 分类频道
        categorized_channels = categorize_channels(filtered_channels)
        
        # 去重
        if OTHER_CONFIG.get('remove_duplicates', True):
            categorized_channels = remove_duplicates(categorized_channels)
        
        # 排序
        if OTHER_CONFIG.get('sort_by_category', True):
            categorized_channels = sort_channels(categorized_channels)
        
        # 限制数量
        max_channels = OTHER_CONFIG.get('max_channels', 1000)
        if max_channels > 0:
            categorized_channels = limit_channels(categorized_channels, max_channels)
        
        # 输出到文件
        output_channels(categorized_channels, OUTPUT_FILE)
        
        # 记录结束时间
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        logger.info(f"IPTV频道收集完成")
        logger.info(f"收集频道数: {len(channels)}")
        logger.info(f"过滤后频道数: {len(filtered_channels)}")
        logger.info(f"分类后频道数: {sum(len(channels) for channels in categorized_channels.values())}")
        logger.info(f"输出到文件: {OUTPUT_FILE}")
        logger.info(f"总耗时: {elapsed_time:.2f} 秒")
        
    except Exception as e:
        logger.error(f"执行脚本时发生错误: {e}")
        log_exception(logger, "执行脚本失败", e)
        return False
    
    return True

# 收集所有频道

def collect_all_channels():
    """从所有数据源收集频道"""
    channels = []
    
    for source in SOURCES:
        try:
            logger.info(f"开始收集数据源: {source['name']}")
            
            # 收集单个数据源的频道
            source_channels = collect_from_source(source)
            
            # 添加到总列表
            channels.extend(source_channels)
            
            logger.info(f"数据源 {source['name']} 收集完成，新增 {len(source_channels)} 个频道")
            
            # 休息一下，避免请求过于频繁
            time.sleep(NETWORK_CONFIG.get('retry_delay', 1))
            
        except Exception as e:
            logger.error(f"收集数据源 {source['name']} 时发生错误: {e}")
            log_exception(logger, f"收集数据源 {source['name']} 失败", e)
    
    return channels

# 从单个数据源收集频道

def collect_from_source(source):
    """从单个数据源收集频道"""
    channels = []
    
    try:
        # 发送请求获取内容
        response = requests.get(source['url'], timeout=NETWORK_CONFIG.get('timeout', 10), verify=NETWORK_CONFIG.get('verify_ssl', False))
        response.raise_for_status()
        content = response.text
        
        # 根据数据源类型解析内容
        if source['url'].endswith('.m3u'):
            # M3U格式
            channels = parse_m3u(content, source)
        elif source['url'].endswith('.txt'):
            # TXT格式
            channels = parse_txt(content, source)
        else:
            # 默认尝试两种格式
            try:
                channels = parse_m3u(content, source)
            except Exception as e:
                logger.debug(f"尝试M3U解析失败，尝试TXT解析: {e}")
                channels = parse_txt(content, source)
        
    except requests.RequestException as e:
        logger.error(f"请求数据源 {source['name']} 时发生错误: {e}")
        log_exception(logger, f"请求数据源 {source['name']} 失败", e)
    except Exception as e:
        logger.error(f"解析数据源 {source['name']} 时发生错误: {e}")
        log_exception(logger, f"解析数据源 {source['name']} 失败", e)
    
    return channels

# 解析M3U格式

def parse_m3u(content, source):
    """解析M3U格式的频道列表"""
    channels = []
    
    try:
        # 分割内容为行
        lines = content.split('\n')
        
        # 解析M3U内容
        for i in range(len(lines)):
            line = lines[i].strip()
            if line.startswith('#EXTINF:-1'):
                # 频道信息行
                channel_info = line
                # 下一行应该是频道URL
                if i + 1 < len(lines):
                    channel_url = lines[i + 1].strip()
                    if channel_url:
                        # 提取频道名称
                        channel_name = extract_channel_name(channel_info)
                        # 创建频道对象
                        channel = {
                            'name': channel_name,
                            'url': channel_url,
                            'source': source['name'],
                            'format': 'm3u',
                            'category': '未分类',
                            'added_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        channels.append(channel)
        
    except Exception as e:
        logger.error(f"解析M3U内容时发生错误: {e}")
        log_exception(logger, "解析M3U内容失败", e)
    
    return channels

# 解析TXT格式

def parse_txt(content, source):
    """解析TXT格式的频道列表"""
    channels = []
    
    try:
        # 分割内容为行
        lines = content.split('\n')
        
        # 解析TXT内容
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # 尝试分割频道名称和URL
                if ',,,' in line:
                    # 格式: 频道名称,,网址
                    parts = line.split(',,,', 1)
                    if len(parts) == 2:
                        channel_name = parts[0].strip()
                        channel_url = parts[1].strip()
                        if channel_url:
                            # 创建频道对象
                            channel = {
                                'name': channel_name,
                                'url': channel_url,
                                'source': source['name'],
                                'format': 'txt',
                                'category': '未分类',
                                'added_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            channels.append(channel)
                elif '|' in line:
                    # 格式: 频道名称|网址
                    parts = line.split('|', 1)
                    if len(parts) == 2:
                        channel_name = parts[0].strip()
                        channel_url = parts[1].strip()
                        if channel_url:
                            # 创建频道对象
                            channel = {
                                'name': channel_name,
                                'url': channel_url,
                                'source': source['name'],
                                'format': 'txt',
                                'category': '未分类',
                                'added_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            channels.append(channel)
                elif ' ' in line:
                    # 格式: 频道名称 网址
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        channel_name = parts[0].strip()
                        channel_url = parts[1].strip()
                        if channel_url:
                            # 创建频道对象
                            channel = {
                                'name': channel_name,
                                'url': channel_url,
                                'source': source['name'],
                                'format': 'txt',
                                'category': '未分类',
                                'added_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            channels.append(channel)
        
    except Exception as e:
        logger.error(f"解析TXT内容时发生错误: {e}")
        log_exception(logger, "解析TXT内容失败", e)
    
    return channels

# 提取频道名称

def extract_channel_name(extinf_line):
    """从#EXTINF行提取频道名称"""
    try:
        # 移除#EXTINF:-1部分
        if '#EXTINF:-1' in extinf_line:
            extinf_line = extinf_line.replace('#EXTINF:-1', '')
        
        # 移除其他扩展信息
        if 'tvg-name=' in extinf_line:
            # 格式: #EXTINF:-1 tvg-name="频道名称" tvg-id="" tvg-logo="" group-title="",频道名称
            match = re.search(r'tvg-name="([^"]+)"', extinf_line)
            if match:
                return match.group(1)
        
        # 尝试从行末提取
        if ',' in extinf_line:
            return extinf_line.split(',', 1)[1].strip()
        
        # 默认返回整行
        return extinf_line.strip()
        
    except Exception as e:
        logger.error(f"提取频道名称时发生错误: {e}")
        log_exception(logger, "提取频道名称失败", e)
        return "未知频道"

# 过滤频道

def filter_channels(channels):
    """根据过滤规则过滤频道"""
    filtered_channels = []
    
    for channel in channels:
        try:
            # 检查排除模式
            exclude = False
            for pattern in FILTER_RULES.get('exclude_patterns', []):
                if re.search(pattern, channel['name'], re.IGNORECASE):
                    exclude = True
                    break
            
            if exclude:
                continue
            
            # 检查包含模式
            include = True
            if FILTER_RULES.get('include_patterns', []):
                include = False
                for pattern in FILTER_RULES.get('include_patterns', []):
                    if re.search(pattern, channel['name'], re.IGNORECASE):
                        include = True
                        break
            
            if not include:
                continue
            
            # 检查URL后缀排除
            url = channel['url']
            exclude_suffix = False
            for suffix in FILTER_RULES.get('exclude_suffixes', []):
                if url.endswith(suffix):
                    exclude_suffix = True
                    break
            
            if exclude_suffix:
                continue
            
            # 检查URL后缀包含
            include_suffix = True
            if FILTER_RULES.get('include_suffixes', []):
                include_suffix = False
                for suffix in FILTER_RULES.get('include_suffixes', []):
                    if url.endswith(suffix):
                        include_suffix = True
                        break
            
            if not include_suffix:
                continue
            
            # 检查URL是否有效
            if not is_valid_url(url):
                continue
                
            # 检查是否应该排除该URL
            if should_exclude_url(url):
                continue
            
            # 通过所有过滤规则
            filtered_channels.append(channel)
            
        except Exception as e:
            logger.error(f"过滤频道 {channel.get('name', '未知')} 时发生错误: {e}")
            log_exception(logger, "过滤频道失败", e)
    
    return filtered_channels

# 分类频道

def categorize_channels(channels):
    """根据分类规则分类频道"""
    categorized_channels = defaultdict(list)
    
    for channel in channels:
        try:
            # 查找匹配的分类
            category = "其他"
            for cat, patterns in CATEGORY_RULES.items():
                for pattern in patterns:
                    if re.search(pattern, channel['name'], re.IGNORECASE):
                        category = cat
                        break
                if category != "其他":
                    break
            
            # 添加到分类
            channel['category'] = category
            categorized_channels[category].append(channel)
            
        except Exception as e:
            logger.error(f"分类频道 {channel.get('name', '未知')} 时发生错误: {e}")
            log_exception(logger, "分类频道失败", e)
            # 默认分类为其他
            channel['category'] = "其他"
            categorized_channels["其他"].append(channel)
    
    return dict(categorized_channels)

# 去重

def remove_duplicates(categorized_channels):
    """去除重复频道"""
    unique_channels = defaultdict(list)
    seen = set()
    
    for category, channels in categorized_channels.items():
        for channel in channels:
            try:
                # 使用频道名称和URL的组合作为唯一标识
                key = (channel['name'], channel['url'])
                if key not in seen:
                    seen.add(key)
                    unique_channels[category].append(channel)
                    
            except Exception as e:
                logger.error(f"去重频道 {channel.get('name', '未知')} 时发生错误: {e}")
                log_exception(logger, "去重频道失败", e)
                # 保留出错的频道
                unique_channels[category].append(channel)
    
    return dict(unique_channels)

# 排序

def sort_channels(categorized_channels):
    """对频道进行排序"""
    sorted_channels = defaultdict(list)
    
    # 按分类名称排序
    sorted_categories = sorted(categorized_channels.keys())
    
    for category in sorted_categories:
        channels = categorized_channels[category]
        # 按频道名称排序
        sorted_channels_list = sorted(channels, key=lambda x: x['name'])
        sorted_channels[category] = sorted_channels_list
    
    return dict(sorted_channels)

# 限制数量

def limit_channels(categorized_channels, max_channels):
    """限制频道总数"""
    limited_channels = defaultdict(list)
    total = 0
    
    for category, channels in categorized_channels.items():
        for channel in channels:
            if total >= max_channels:
                break
            limited_channels[category].append(channel)
            total += 1
        
        if total >= max_channels:
            break
    
    return dict(limited_channels)

# 输出到文件

def output_channels(categorized_channels, output_file):
    """将频道输出到文件"""
    try:
        with open(output_file, 'w', encoding=OTHER_CONFIG.get('output_encoding', 'utf-8')) as f:
            # 写入标题
            f.write(f"# IPTV频道列表\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 总频道数: {sum(len(channels) for channels in categorized_channels.values())}\n")
            f.write(f"# 分类数: {len(categorized_channels)}\n")
            f.write("\n")
            
            # 写入每个分类的频道
            for category, channels in categorized_channels.items():
                f.write(f"# {category}({len(channels)})\n")
                for channel in channels:
                    f.write(f"{channel['name']},,,{channel['url']}\n")
                f.write("\n")
        
        logger.info(f"频道成功输出到文件: {output_file}")
        
    except Exception as e:
        logger.error(f"输出频道到文件时发生错误: {e}")
        log_exception(logger, "输出频道到文件失败", e)
        raise

# 检查URL是否有效

def should_exclude_url(url):
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
            r'http://example\.',
            r'https://example\.',
            r'demo',
            r'sample',
            r'samples'
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
            if should_exclude_resolution(url, min_resolution):
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"检查URL是否应该排除时发生错误: {e}")
        log_exception(logger, "检查URL排除失败", e)
        return True

def is_valid_url(url):
    """检查URL是否有效"""
    try:
        if not url or not isinstance(url, str):
            return False
            
        # 检查协议
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('rtmp://') or url.startswith('rtsp://') or url.startswith('m3u8://')):
            return False
            
        # 简单检查格式
        if '.' not in url:
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"检查URL有效性时发生错误: {e}")
        log_exception(logger, "检查URL有效性失败", e)
        return False

# 主函数入口
if __name__ == '__main__':
    main()
