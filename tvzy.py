import os
import re
import requests
import concurrent.futures

# 导入核心模块
from core.logging_config import get_logger, log_exception, log_performance, setup_logging
from core.config import get_config
from core.network import fetch_content
from core.chinese_conversion import add_traditional_aliases

# 设置日志
setup_logging()
logger = get_logger(__name__)

# 从配置获取参数
NETWORK_CONFIG = get_config('network', {})
OUTPUT_CONFIG = get_config('output', {})
MAX_WORKERS = get_config('network.max_workers', 10)
TIMEOUT = get_config('network.timeout', 10)
MIN_LINES_PER_CHANNEL = get_config('output.min_lines_per_channel', 10)
MAX_LINES_PER_CHANNEL = get_config('output.max_lines_per_channel', 90)
# 默认输出文件名
OUTPUT_FILE = get_config('output.output_file_tvzy', 'tzydauto.txt')

# 网络配置
ALLOWED_DOMAINS = get_config('network.allowed_domains', [])

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 数据源列表
# 从统一播放源文件导入
from unified_sources import UNIFIED_SOURCES
GITHUB_SOURCES = UNIFIED_SOURCES

# 从配置获取频道分类和映射
channel_config = get_config('channels', {})
CHANNEL_CATEGORIES = channel_config.get('categories', {})

# 如果配置中没有提供频道分类，使用默认的分类
if not CHANNEL_CATEGORIES:
    CHANNEL_CATEGORIES = {
        "4K频道": ['CCTV4K', 'CCTV16 4K', '北京卫视4K', '北京IPTV4K', '湖南卫视4K', '山东卫视4K', '广东卫视4K', '四川卫视4K',
                    '浙江卫视4K', '江苏卫视4K', '东方卫视4K', '深圳卫视4K', '河北卫视4K', '峨眉电影4K', '求索4K', '咪视界4K', '欢笑剧场4K',
                    '苏州4K', '至臻视界4K', '南国都市4K', '翡翠台4K', '百事通电影4K', '百事通少儿4K', '百事通纪实4K', '华数爱上4K'],
        "央视频道": ['CCTV1', 'CCTV2', 'CCTV3', 'CCTV4', 'CCTV4欧洲', 'CCTV4美洲', 'CCTV5', 'CCTV5+', 'CCTV6', 'CCTV7', 'CCTV8', 'CCTV9',
                    'CCTV10', 'CCTV11', 'CCTV12', 'CCTV13', 'CCTV14', 'CCTV15', 'CCTV16', 'CCTV17', '兵器科技', '风云音乐', '风云足球',
                    '风云剧场', '怀旧剧场', '第一剧场', '女性时尚', '世界地理', '央视台球', '高尔夫网球', '央视文化精品', '北京纪实科教',
                    '卫生健康', '电视指南']
    }

# 从配置获取频道映射
CHANNEL_MAPPING = channel_config.get('mapping', {})

# 如果配置中没有提供频道映射，使用默认的映射逻辑
if not CHANNEL_MAPPING:
    # 填充频道映射字典
    CHANNEL_MAPPING = {}
    for category, channels in CHANNEL_CATEGORIES.items():
        for channel in channels:
            CHANNEL_MAPPING[channel] = [channel]

    additional_mappings = {
        "CCTV4K": ["CCTV 4K", "CCTV-4K"],
        "CCTV16 4K": ["CCTV16 4K", "CCTV16-4K", "CCTV16 奥林匹克 4K", "CCTV16奥林匹克 4K"],
    }
    
    # 添加额外的映射
    for channel, aliases in additional_mappings.items():
        if channel in CHANNEL_MAPPING:
            CHANNEL_MAPPING[channel].extend(aliases)

# 自动为所有频道别名添加繁体中文版本
CHANNEL_MAPPING = add_traditional_aliases(CHANNEL_MAPPING)

# 频道信息类
class ChannelInfo:
    def __init__(self, name, url, category=None, source=None):
        self.name = name
        self.url = url
        self.category = category
        self.source = source
        self.quality = None
        self.language = None

    def __str__(self):
        return f"Channel(name='{self.name}', url='{self.url}', category='{self.category}')"

    def to_dict(self):
        return {
            'name': self.name,
            'url': self.url,
            'category': self.category,
            'source': self.source,
            'quality': self.quality,
            'language': self.language
        }

# 从字符串中提取频道信息
def extract_channel_info(line):
    # 支持多种格式的频道信息提取
    # 格式1: #EXTINF:-1 tvg-id="" tvg-name="频道名称" tvg-logo="" group-title="频道分类",频道名称
    # 格式2: #EXTINF:-1,频道名称
    # 格式3: 频道名称,http://example.com/stream
    # 格式4: http://example.com/stream|频道名称
    
    # 去除行首尾空格
    line = line.strip()
    
    # 跳过空行
    if not line:
        return None
    
    # 处理EXTINF格式
    if line.startswith('#EXTINF:'):
        return None  # 只处理流地址行，不处理EXTINF行
    
    # 处理普通格式
    if ',' in line:
        # 格式3: 频道名称,http://example.com/stream
        parts = line.split(',', 1)
        if len(parts) != 2:
            return None
        
        name = parts[0].strip()
        url = parts[1].strip()
        
        # 验证URL格式
        if not url.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
            return None
        
        return ChannelInfo(name, url)
    elif '|' in line:
        # 格式4: http://example.com/stream|频道名称
        parts = line.split('|', 1)
        if len(parts) != 2:
            return None
        
        url = parts[0].strip()
        name = parts[1].strip()
        
        # 验证URL格式
        if not url.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
            return None
        
        return ChannelInfo(name, url)
    elif line.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
        # 只有URL，没有频道名称
        return None
    else:
        # 只有频道名称，没有URL
        return None

# 从URL中提取域名
def extract_domain(url):
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return None

# 检查URL是否在允许的域名列表中
def is_allowed_domain(url):
    if not ALLOWED_DOMAINS:
        return True  # 如果允许的域名列表为空，则允许所有域名
    
    domain = extract_domain(url)
    if not domain:
        return False
    
    for allowed_domain in ALLOWED_DOMAINS:
        if allowed_domain in domain:
            return True
    
    return False

# 从单一数据源获取频道信息
def get_channels_from_source(source):
    channels = []
    
    try:
        # 获取数据源内容
        content = fetch_content(source, timeout=TIMEOUT, headers=HEADERS)
        if not content:
            logger.warning(f"无法获取数据源内容: {source}")
            return channels
        
        logger.info(f"从数据源 {source} 获取到内容，长度: {len(content)} 字符")
        # 按行处理内容
        lines = content.split('\n')
        logger.info(f"数据源 {source} 共有 {len(lines)} 行内容")
        
        # 打印前20行用于调试
        for i, line in enumerate(lines[:20]):
            if i < 10 or i > len(lines[:20]) - 5:
                logger.debug(f"数据源 {source} 第 {i+1} 行: {repr(line)}")
        
        prev_line = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 跳过空行和分类行
            if not line or line.endswith(',#genre#'):
                continue
            
            if line.startswith('#EXTINF:'):
                logger.debug(f"第 {i+1} 行 - 找到EXTINF行: {repr(line)}")
                # 保存EXTINF行，用于后续提取频道信息
                prev_line = line
            elif line.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
                logger.debug(f"第 {i+1} 行 - 找到流地址行: {repr(line)}")
                # 提取频道信息
                channel = None
                
                if prev_line:
                    logger.debug(f"第 {i+1} 行 - 使用前一行EXTINF: {repr(prev_line)}")
                    # 从EXTINF行和流地址行中提取频道信息
                    name = extract_channel_name_from_extinf(prev_line)
                    if name:
                        logger.debug(f"第 {i+1} 行 - 从EXTINF提取到名称: {name}")
                        channel = ChannelInfo(name, line, source=source)
                    else:
                        logger.debug(f"第 {i+1} 行 - 无法从EXTINF行提取名称")
                    prev_line = None
                else:
                    # 只有流地址行，没有频道名称
                    logger.debug(f"第 {i+1} 行 - 没有前一行EXTINF，使用默认名称")
                    channel = ChannelInfo('未知频道', line, source=source)
                
                if channel:
                    if is_allowed_domain(channel.url):
                        channels.append(channel)
                        logger.debug(f"第 {i+1} 行 - 添加频道: {channel.name} -> {channel.url}")
                    else:
                        logger.debug(f"第 {i+1} 行 - 频道URL {channel.url} 不在允许的域名列表中")
            elif ',' in line:
                logger.debug(f"第 {i+1} 行 - 处理逗号分隔格式行: {repr(line)}")
                # 处理其他格式的频道信息
                channel = extract_channel_info(line)
                if channel:
                    logger.debug(f"第 {i+1} 行 - 提取到频道: {channel.name} -> {channel.url}")
                    if is_allowed_domain(channel.url):
                        channels.append(channel)
                        logger.debug(f"第 {i+1} 行 - 添加频道: {channel.name} -> {channel.url}")
                    else:
                        logger.debug(f"第 {i+1} 行 - 频道URL {channel.url} 不在允许的域名列表中")
                else:
                    logger.debug(f"第 {i+1} 行 - 无法提取频道信息")
                    # 手动测试分割逻辑
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        url = parts[1].strip()
                        logger.debug(f"第 {i+1} 行 - 手动分割: 名称='{name}', URL='{url}'")
                        logger.debug(f"第 {i+1} 行 - URL是否以http开头: {url.startswith(('http://', 'https://'))}")
            else:
                prev_line = None
    except Exception as e:
        logger.error(f"处理数据源时出错: {source}, 错误: {e}")
        log_exception(logger, f"处理数据源时出错: {source}")
    
    logger.info(f"从数据源 {source} 成功提取 {len(channels)} 个频道")
    return channels

# 从EXTINF行中提取频道名称
def extract_channel_name_from_extinf(extinf_line):
    # 格式: #EXTINF:-1 tvg-id="" tvg-name="频道名称" tvg-logo="" group-title="频道分类",频道名称
    try:
        # 查找逗号位置
        comma_pos = extinf_line.rfind(',')
        if comma_pos == -1:
            return None
        
        # 提取频道名称
        name = extinf_line[comma_pos + 1:].strip()
        return name if name else None
    except Exception:
        return None

# 检查是否应该排除购物频道
def should_exclude_channel(name):
    """检查是否应该排除购物频道或CCTV数字超过17的频道"""
    try:
        # 排除购物相关频道
        shopping_keywords = ['购物', '导购', '电视购物']
        
        for keyword in shopping_keywords:
            if keyword in name:
                return True
        
        # 检查CCTV频道数字是否超过17
        cctv_match = re.match(r'^CCTV[- ]?(\d+)', name, re.IGNORECASE)
        if cctv_match:
            cctv_number = int(cctv_match.group(1))
            if cctv_number > 17:
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"检查频道是否应该排除时发生错误: {e}")
        log_exception(logger, "检查频道排除失败", e)
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
            if should_exclude_resolution(url, channel_name, min_resolution):
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"检查URL是否应该排除时发生错误: {e}")
        log_exception(logger, "检查URL排除失败", e)
        return True

# 过滤频道名称
def filter_channel_name(name):
    # 去除频道名称中的特殊字符
    name = re.sub(r'[^一-龥a-zA-Z0-9\s\-\_]+', '', name)
    
    # 去除前后空格
    name = name.strip()
    
    # 过滤CCTV频道名称中的错误别名（如CCTV4a, CCTV4A, CCTV4o等）
    if re.match(r'^[Cc][Cc][Tt][Vv][\s\-]?\d+', name):
        # 保留CCTV和数字部分，移除其他字符
        match = re.match(r'^([Cc][Cc][Tt][Vv][\s\-]?\d+)', name)
        if match:
            # 转换为标准格式（去掉连字符和空格）
            base_name = re.sub(r'[\s\-]', '', match.group(1)).upper()
            # 检查是否有欧洲/美洲等后缀
            if '欧洲' in name or '美洲' in name:
                region = '欧洲' if '欧洲' in name else '美洲'
                name = f"{base_name}{region}"
            else:
                name = base_name
    
    # 去除常见的后缀
    suffixes = ['高清', '超清', '标清', 'HD', 'SD', '1080P', '720P', '4K', '直播']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
            break
    
    return name

# 对频道进行分类
def categorize_channel(channel):
    # 过滤频道名称
    filtered_name = filter_channel_name(channel.name)
    
    # 查找匹配的分类，确保港澳频道优先于卫视频道
    # 首先检查港澳频道
    if "港澳频道" in CHANNEL_CATEGORIES:
        for channel_name in CHANNEL_CATEGORIES["港澳频道"]:
            if channel_name in filtered_name:
                return "港澳频道"
    
    # 然后检查其他分类
    for category, channels in CHANNEL_CATEGORIES.items():
        if category != "港澳频道":  # 已经检查过港澳频道，跳过
            for channel_name in channels:
                if channel_name in filtered_name:
                    return category
    
    # 没有匹配的分类，返回默认分类
    return "其他频道"

# 合并多个数据源的频道信息
def merge_channels(all_channels):
    # 使用字典来存储频道信息，键为频道名称，值为频道列表
    channel_dict = {}
    
    excluded_channels = 0
    excluded_urls = 0
    
    for channel in all_channels:
        # 过滤频道名称
        filtered_name = filter_channel_name(channel.name)
        
        # 跳过空名称
        if not filtered_name:
            continue
        
        # 检查是否应该排除购物频道
        if should_exclude_channel(filtered_name):
            excluded_channels += 1
            continue
        
        # 检查是否应该排除该URL
        if should_exclude_url(channel.url, filtered_name):
            excluded_urls += 1
            continue
        
        # 添加到字典中
        if filtered_name not in channel_dict:
            channel_dict[filtered_name] = []
        
        # 设置频道分类
        channel.category = categorize_channel(channel)
        
        # 添加到频道列表中
        channel_dict[filtered_name].append(channel)
    
    # 对每个频道的流地址进行排序和去重
    merged_channels = []
    for name, channels in channel_dict.items():
        # 去重
        unique_channels = []
        seen_urls = set()
        
        for channel in channels:
            if channel.url not in seen_urls:
                seen_urls.add(channel.url)
                unique_channels.append(channel)
        
        # 排序
        unique_channels.sort(key=lambda x: (x.category, x.name))
        
        # 限制每个频道的流地址数量
        unique_channels = unique_channels[:MAX_LINES_PER_CHANNEL]
        
        # 添加到合并后的列表中
        merged_channels.extend(unique_channels)
    
    return merged_channels

# 生成输出内容
def generate_output(channels):
    output = []
    
    # 获取频道分类顺序
    config_categories = get_config('channels.categories', {})
    category_order = {category: index for index, category in enumerate(config_categories)}
    
    # 按分类顺序排序频道
    def sort_key(channel):
        category = channel.category
        # 未在配置中的分类放在最后，按名称排序
        if category in category_order:
            return (category_order[category], channel.name)
        else:
            return (len(category_order), category, channel.name)
    
    channels.sort(key=sort_key)
    
    # 生成输出内容
    current_category = None
    for channel in channels:
        if channel.category != current_category:
            # 输出分类标题
            current_category = channel.category
            output.append(f"# {current_category}")
        
        # 输出频道信息
        output.append(f"{channel.name},{channel.url}")
    
    return '\n'.join(output)

# 主函数
def main():
    logger.info("开始获取电视频道信息...")
    
    # 获取所有频道信息
    all_channels = []
    
    # 使用多线程获取频道信息
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_source = {executor.submit(get_channels_from_source, source): source for source in GITHUB_SOURCES}
        
        # 处理任务结果
        for future in concurrent.futures.as_completed(future_to_source):
            source = future_to_source[future]
            try:
                channels = future.result()
                logger.info(f"从数据源 {source} 获取到 {len(channels)} 个频道")
                all_channels.extend(channels)
            except Exception as e:
                logger.error(f"从数据源 {source} 获取频道时出错: {e}")
                log_exception(logger, f"从数据源 {source} 获取频道时出错")
    
    logger.info(f"总共获取到 {len(all_channels)} 个频道")
    
    # 合并频道信息
    merged_channels = merge_channels(all_channels)
    logger.info(f"合并后有 {len(merged_channels)} 个频道")
    
    # 生成输出内容
    output = generate_output(merged_channels)
    
    # 写入输出文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(output)
    
    logger.info(f"频道信息已写入文件: {OUTPUT_FILE}")

# 入口函数
if __name__ == "__main__":
    main()