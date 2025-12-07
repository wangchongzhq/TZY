import requests
import re
from datetime import datetime
import time
from collections import defaultdict

# 导入核心模块
from core.config import get_config, config_manager
from core.logging_config import setup_logging, get_logger, log_exception
from core.channel_utils import should_exclude_resolution

# 设置日志
setup_logging(log_level='DEBUG')
logger = get_logger(__name__)

# 导入统一数据源列表
from unified_sources import SOURCES_WITH_NAMES

# 数据源列表，使用统一的数据源
SOURCES = get_config('sources.collect_sources', [
    {"name": name, "url": url} for name, url in SOURCES_WITH_NAMES
])

# 分类规则
CATEGORY_RULES = get_config('category.rules', {
    "春晚": [
        r'春晚', r'春节联欢晚会'
    ],
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
        r'备用', r'备用线路', r'备用源'
    ],
    "include_patterns": [
        # 确保包含央视频道
        r'CCTV', r'央视', r'中央电视台', r'CGTN',
        # 包含其他常见频道类型
        r'卫视', r'凤凰', r'TVB'
    ],
    "exclude_suffixes": [
        # 不排除常见的直播源后缀
    ],
    "include_suffixes": [
        # 不限制后缀，允许所有常见的直播源格式
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
    "remove_duplicates": True,
    "output_encoding": "utf-8"
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
        
        # 记录分类后的频道结构
        logger.info(f"分类后的频道结构: {[(cat, len(channels)) for cat, channels in categorized_channels.items()]}")
        
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
            
            # 收集单个数据源的频道，增加重试机制
            max_retries = NETWORK_CONFIG.get('max_retries', 3)
            source_channels = []
            
            for retry in range(max_retries):
                try:
                    source_channels = collect_from_source(source)
                    if source_channels:
                        break
                    logger.info(f"数据源 {source['name']} 第一次获取为空，正在重试 ({retry + 1}/{max_retries})...")
                except Exception as e:
                    logger.error(f"数据源 {source['name']} 第 {retry + 1} 次尝试失败: {e}")
                    if retry < max_retries - 1:
                        time.sleep(NETWORK_CONFIG.get('retry_delay', 2))
            
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
    logger.debug(f"正在请求数据源: {source['url']}")
    
    try:
        # 发送请求获取内容
        response = requests.get(source['url'], timeout=NETWORK_CONFIG.get('timeout', 10), verify=NETWORK_CONFIG.get('verify_ssl', False))
        response.raise_for_status()
        # 强制使用UTF-8编码解析内容，解决中文乱码问题
        response.encoding = 'utf-8'
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
            if line and not line.startswith('#') and not '#genre#' in line:
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
                elif ',' in line:
                    # 格式: 频道名称,网址
                    parts = line.split(',', 1)
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
        logger.debug(f"原始#EXTINF行: {extinf_line}")
        
        # 移除#EXTINF:-1部分
        if '#EXTINF:-1' in extinf_line:
            extinf_line = extinf_line.replace('#EXTINF:-1', '')
        
        # 优先从tvg-name提取频道名称（更准确）
        channel_name = None
        if 'tvg-name=' in extinf_line:
            # 格式: #EXTINF:-1 tvg-name="频道名称" tvg-id="" tvg-logo="" group-title="",频道名称
            match = re.search(r'tvg-name="([^"]+)"', extinf_line)
            if match:
                channel_name = match.group(1)
                logger.debug(f"从tvg-name提取到频道名称: {channel_name}")
        
        # 如果没有tvg-name，再从行末提取频道名称
        if not channel_name and ',' in extinf_line:
            line_end_name = extinf_line.split(',', 1)[1].strip()
            if line_end_name and not line_end_name.startswith('2025'):  # 过滤掉日期格式的行末
                channel_name = line_end_name
                logger.debug(f"从行末提取到频道名称: {channel_name}")
        
        # 默认返回整行（如果没有提取到有效的频道名称）
        if not channel_name:
            channel_name = extinf_line.strip()
            logger.debug(f"无法提取频道名称，返回整行: {channel_name}")
        
        # 过滤CCTV频道名称中的错误别名（如CCTV4a, CCTV4A, CCTV4o等）
        if re.match(r'^[Cc][Cc][Tt][Vv][\s\-]?\d+', channel_name):
            # 保留CCTV和数字部分，移除其他字符
            match = re.match(r'^([Cc][Cc][Tt][Vv][\s\-]?\d+)', channel_name)
            if match:
                # 转换为标准格式（去掉连字符和空格）
                base_name = re.sub(r'[\s\-]', '', match.group(1)).upper()
                # 检查是否有欧洲/美洲等后缀
                if '欧洲' in channel_name or '美洲' in channel_name:
                    region = '欧洲' if '欧洲' in channel_name else '美洲'
                    channel_name = f"{base_name}{region}"
                else:
                    channel_name = base_name
        
        # 保留CCTV频道的完整名称（带数字），以便正确分类
        # 如果需要标准化CCTV频道名称，可以在后续步骤中进行
        
        return channel_name
        
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
            if should_exclude_url(url, channel.get('name', '')):
                continue
            
            # 检查CCTV频道数字是否超过17
            channel_name = channel.get('name', '')
            cctv_match = re.match(r'^CCTV[- ]?(\d+)', channel_name, re.IGNORECASE)
            if cctv_match:
                cctv_number = int(cctv_match.group(1))
                if cctv_number > 17:
                    logger.debug(f"排除CCTV频道，数字超过17: {channel_name}")
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
    
    # 按照CATEGORY_RULES定义的顺序排序分类
    sorted_categories = []
    for category in CATEGORY_RULES.keys():
        if category in categorized_channels:
            sorted_categories.append(category)
    
    # 处理不在CATEGORY_RULES中的其他分类
    for category in categorized_channels.keys():
        if category not in sorted_categories:
            sorted_categories.append(category)
    
    for category in sorted_categories:
        channels = categorized_channels[category]
        
        # 按频道名称分组
        channel_groups = defaultdict(list)
        for channel in channels:
            channel_groups[channel['name']].append(channel)
        
        def get_name_sort_key(name):
            """获取频道名称的排序键"""
            name_upper = name.upper()
            
            # 对央视分类下的频道进行特殊处理，确保按数字顺序排序
            if category == '央视' or 'CCTV' in name_upper:
                # 处理各种央视频道格式：CCTV1, CCTV-1, 央视1, 中央电视台1等
                # 提取数字部分
                match = re.search(r'(?:CCTV|央视|中央电视台|中央台)\s*[-_]*\s*(\d+)', name_upper)
                if match:
                    # 返回(数字部分, 原始名称)作为排序键
                    return (int(match.group(1)), name_upper)
                # 对CCTV-5+等特殊频道的处理
                match = re.search(r'(?:CCTV|央视|中央电视台|中央台)\s*[-_]*\s*(\d+)(\+)', name_upper)
                if match:
                    return (int(match.group(1)) + 0.5, name_upper)  # 使用小数处理CCTV5+等情况
                # 对其他央视频道（如CCTV娱乐）的处理
                return (float('inf'), name_upper)
            
            # 对其他频道，直接按名称排序
            return (float('inf'), name_upper)
        
        # 对频道名称按排序键排序
        sorted_names = sorted(channel_groups.keys(), key=get_name_sort_key)
        
        # 合并排序后的频道列表
        sorted_channels_list = []
        for name in sorted_names:
            sorted_channels_list.extend(channel_groups[name])
        
        sorted_channels[category] = sorted_channels_list
    
    return dict(sorted_channels)

# 限制数量

def limit_channels(categorized_channels, max_channels):
    """限制频道总数，均衡地从所有分类中收集频道"""
    limited_channels = defaultdict(list)
    total = 0
    
    # 调试：输出央视分类的初始情况
    if '央视' in categorized_channels:
        cctv_channels = categorized_channels['央视']
        cctv_names = set()
        for ch in cctv_channels:
            name = ch.get('standardized_name', ch['name'])
            cctv_names.add(name)
        logger.debug(f"央视分类初始频道数: {len(cctv_channels)}, 不同频道数: {len(cctv_names)}, 频道名称: {sorted(cctv_names)}")
    
    # 获取所有分类
    categories = list(categorized_channels.keys())
    num_categories = len(categories)
    
    if num_categories == 0:
        return dict(limited_channels)
    
    # 计算每个分类理想情况下应该分配的频道数量
    ideal_per_category = max_channels // num_categories
    remaining = max_channels % num_categories
    
    # 调试：输出每个分类的限制
    logger.debug(f"分类数量: {num_categories}, max_channels: {max_channels}")
    logger.debug(f"每个分类理想分配数量: {ideal_per_category}, 剩余: {remaining}")
    
    for i, category in enumerate(categories):
        channels = categorized_channels[category]
        # 每个分类的分配数量
        allocation = ideal_per_category + (1 if i < remaining else 0)
        
        logger.debug(f"处理分类: {category}, 原始频道数: {len(channels)}, 分配数量: {allocation}")
        
        if allocation <= 0:
            continue
        
        # 如果该分类的频道数量超过分配数量，则需要按频道名称均匀采样
        if len(channels) > allocation:
            # 按频道名称分组
            name_groups = defaultdict(list)
            for channel in channels:
                name = channel.get('standardized_name', channel['name'])
                name_groups[name].append(channel)
            
            # 调试：输出该分类的频道名称数量
            logger.debug(f"{category}分类的频道名称数量: {len(name_groups)}, 名称列表: {list(name_groups.keys())[:10]}...")
            
            # 计算每个频道名称应该分配的线路数
            num_names = len(name_groups)
            ideal_per_name = allocation // num_names
            remaining_names = allocation % num_names
            
            # 收集频道
            collected = 0
            for j, (name, group) in enumerate(name_groups.items()):
                # 为每个频道名称分配的线路数
                name_allocation = ideal_per_name + (1 if j < remaining_names else 0)
                
                # 如果该频道名称的线路数超过分配数量，则只取前name_allocation个
                take = min(name_allocation, len(group))
                
                limited_channels[category].extend(group[:take])
                collected += take
                
                # 如果已经达到该分类的分配数量，则提前退出
                if collected >= allocation:
                    break
            
            total += collected
            logger.debug(f"{category}分类处理后频道数: {collected}")
        else:
            # 如果该分类的频道数量不超过分配数量，则全部添加
            limited_channels[category].extend(channels)
            total += len(channels)
            logger.debug(f"{category}分类处理后频道数: {len(channels)}")
        
        # 如果已经达到总限制，则提前退出
        if total >= max_channels:
            break
    
    # 调试：输出央视分类的最终情况
    if '央视' in limited_channels:
        cctv_channels_final = limited_channels['央视']
        cctv_names_final = set()
        for ch in cctv_channels_final:
            name = ch.get('standardized_name', ch['name'])
            cctv_names_final.add(name)
        logger.debug(f"央视分类最终频道数: {len(cctv_channels_final)}, 不同频道数: {len(cctv_names_final)}, 频道名称: {sorted(cctv_names_final)}")
    
    return dict(limited_channels)

# 输出到文件

def standardize_channel_name(channel_name):
    """标准化频道名称，将别名映射为通用频道名"""
    try:
        # 加载频道别名映射配置
        config = config_manager.get_all()
        name_mappings = config.get('name_mappings', {})
        
        # 首先进行初步标准化，处理各种格式变体
        normalized = channel_name.strip()
        
        # 将所有空白字符（包括空格、制表符等）替换为单个空格
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # 处理CCTV频道的各种格式
        # 支持: CCTV1, CCTV-1, CCTV 1, CCTV - 1, CCTV  1, CCTV- 1, CCTV -1等
        
        # 处理CCTV-数字格式（如CCTV-1, CCTV -1, CCTV- 1等）
        if re.match(r'^CCTV\s*-\s*(\d+)', normalized, re.IGNORECASE):
            number = re.search(r'^CCTV\s*-\s*(\d+)', normalized, re.IGNORECASE).group(1)
            normalized = f'CCTV{number}'
        
        # 处理CCTV数字格式（如CCTV 1, CCTV  1等）
        elif re.match(r'^CCTV\s+(\d+)', normalized, re.IGNORECASE):
            number = re.search(r'^CCTV\s+(\d+)', normalized, re.IGNORECASE).group(1)
            normalized = f'CCTV{number}'
        
        # 处理CCTV频道名称中的错误别名（如CCTV4a, CCTV4A, CCTV4o等）
        elif re.match(r'^CCTV\d+[AaOoMm]', normalized, re.IGNORECASE):
            match = re.match(r'^CCTV(\d+)', normalized, re.IGNORECASE)
            if match:
                normalized = f'CCTV{match.group(1)}'
        
        # 处理CCTV-娱乐/娛樂格式（如CCTV-娱乐, CCTV - 娛樂, CCTV- 娛樂等）
        elif re.match(r'^CCTV\s*(-|\s+)\s*[娱乐娛樂]', normalized, re.IGNORECASE):
            normalized = 'CCTV娱乐'
        
        # 处理CCTV+等格式
        if 'CCTV+' in normalized or 'CCTV +' in normalized:
            normalized = 'CCTV plus'
        
        # 处理CCTV-5+等特殊格式
        if re.match(r'^CCTV(\d+)\s*\+', normalized, re.IGNORECASE):
            number = re.search(r'^CCTV(\d+)', normalized, re.IGNORECASE).group(1)
            normalized = f'CCTV{number}+'
        
        # 确保在处理完CCTV格式后，再次检查是否匹配标准名称
        if normalized in name_mappings:
            return normalized
            
        # 检查标准化后的名称是否为别名
        for general_name, aliases in name_mappings.items():
            if normalized in aliases:
                return general_name
        
        # 处理TVB频道的各种格式
        if normalized.startswith('TVB'):
            # 处理TVB明珠台
            if '明珠' in normalized:
                normalized = 'TVB明珠'
            # 处理TVB星河台
            elif '星河' in normalized:
                normalized = 'TVB星河'
            # 处理TVB翡翠台
            elif '翡翠' in normalized:
                normalized = '翡翠台'
            # 处理TVB新闻台
            elif '新闻' in normalized or '新聞' in normalized:
                normalized = 'TVB新闻台'
            # 处理TVB娱乐台
            elif '娱乐' in normalized or '娛樂' in normalized:
                normalized = 'TVB娱乐台'
            # 处理TVB生活台
            elif '生活' in normalized:
                normalized = 'TVB生活台'
            # 处理TVB功夫台
            elif '功夫' in normalized:
                normalized = 'TVB功夫台'
            # 处理TVB Plus
            elif 'Plus' in normalized or 'PLUS' in normalized:
                normalized = 'TVB Plus'
        
        # 处理CCTV+和CCTV plus的各种格式
        if re.search(r'CCTV\s*\+|CCTV\s*plus', normalized, re.IGNORECASE):
            normalized = 'CCTV plus'
        
        # 移除频道名称中的附加信息（如HD、(咪咕)、频道等）
        # 处理HD/高清后缀
        normalized = re.sub(r'\s*(HD|高清)\b', '', normalized, flags=re.IGNORECASE)
        
        # 处理平台标识（如(咪咕)、(腾讯)等）
        normalized = re.sub(r'\s*\([^)]+\)', '', normalized)
        
        # 处理"频道"后缀
        normalized = re.sub(r'\s*(频道|頻道)\b', '', normalized)
        
        # 处理"综合"、"新闻"、"社会与法"等附加词
        normalized = re.sub(r'\s*(综合|新闻|社会与法|科教|戏曲|音乐|体育|财经|少儿|农业农村|奥林匹克)\b', '', normalized)
        
        # 去除多余的空格
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # 检查标准化后的名称是否为通用频道名
        if normalized in name_mappings:
            return normalized
            
        # 检查标准化后的名称是否为别名
        for general_name, aliases in name_mappings.items():
            if normalized in aliases:
                return general_name
        
        # 再次尝试原始名称是否匹配别名（防止标准化过度）
        for general_name, aliases in name_mappings.items():
            if channel_name in aliases:
                return general_name
        
        # 再次尝试去除附加信息前的名称是否匹配别名
        channel_name_clean = re.sub(r'\s*(HD|高清)\b', '', channel_name, flags=re.IGNORECASE)
        channel_name_clean = re.sub(r'\s*\([^)]+\)', '', channel_name_clean)
        channel_name_clean = re.sub(r'\s*(频道|頻道)\b', '', channel_name_clean)
        channel_name_clean = re.sub(r'\s*(综合|新闻|社会与法|科教|戏曲|音乐|体育|财经|少儿|农业农村|奥林匹克)\b', '', channel_name_clean)
        channel_name_clean = re.sub(r'\s+', ' ', channel_name_clean).strip()
        
        for general_name, aliases in name_mappings.items():
            if channel_name_clean in aliases:
                return general_name
        
        # 直接检查CCTV格式，例如CCTV1, CCTV2等
        if re.match(r'^CCTV\d+$', normalized):
            return normalized
        
        # 如果还是没有匹配，返回标准化后的名称
        return normalized
        
    except Exception as e:
        logger.error(f"标准化频道名称时发生错误: {e}")
        log_exception(logger, "标准化频道名称失败", e)
        # 发生错误时返回原始名称
        return channel_name


def output_channels(categorized_channels, output_file):
    """将频道输出到文件"""
    try:
        # 收集所有频道，不考虑分类
        all_channels = []
        for category, channels in categorized_channels.items():
            all_channels.extend(channels)
        
        # 计算线路总数
        total_lines = len(all_channels)
        
        with open(output_file, 'w', encoding=OTHER_CONFIG.get('output_encoding', 'utf-8')) as f:
            # 写入标题，保持与现有格式一致
            f.write(f"# 中国境内电视直播线路 (仅限1080p高清以上)\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 数据来源: 多个GitHub IPTV项目\n")
            f.write(f"# 频道总数: {len(set(channel['name'] for channel in all_channels))}\n")
            f.write(f"# 线路总数: {total_lines}\n")
            f.write(f"# 清晰度要求: 仅保留1080p高清及以上线路\n")
            f.write("############################################################\n\n")
            
            # 写入每个分类的频道，保持与现有格式一致
            for category, channels in categorized_channels.items():
                f.write(f"{category},#genre#\n")
                for channel in channels:
                    # 标准化频道名称
                    standardized_name = standardize_channel_name(channel['name'])
                    f.write(f"{standardized_name},{channel['url']}\n")
                f.write("\n")
        
        logger.info(f"频道成功输出到文件: {output_file}")
        
    except Exception as e:
        logger.error(f"输出频道到文件时发生错误: {e}")
        log_exception(logger, "输出频道到文件失败", e)
        raise

# 检查URL是否有效

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
        try:
            # 获取所有配置
            config = config_manager.get_all()
            # 从配置中获取最小分辨率要求
            min_resolution = config.get('quality', {}).get('min_resolution', '1920x1080')
            
            # 检查是否开启分辨率过滤
            open_filter_resolution = config.get('quality', {}).get('open_filter_resolution', True)
            
            # 对于央视频道，如果频道名中显示了分辨率，则根据分辨率决定是否排除；否则不排除
            if open_filter_resolution:
                # 对于央视频道，直接调用should_exclude_resolution，它会自动处理：
                # - 频道名中未显示分辨率的 -> 返回False（不排除）
                # - 频道名中显示较低分辨率的 -> 返回True（排除）
                if should_exclude_resolution(url, channel_name, min_resolution):
                    return True
        except Exception as e:
            logger.error(f"检查分辨率时发生错误，但不排除URL: {e}")
            # 分辨率检查失败时，不排除URL
        
        return False
        
    except Exception as e:
        logger.error(f"检查URL是否应该排除时发生错误，但不排除URL: {e}")
        # 发生任何错误时，不排除URL，而是返回False
        return False

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