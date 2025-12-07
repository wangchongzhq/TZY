#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
频道处理工具模块
功能：提供频道的去重、过滤、分组、验证和质量评估等功能
"""

import re
import hashlib
import time
import subprocess
import os
from typing import List, Dict, Tuple, Optional, Callable, Any
from core.parser import ChannelInfo
from core.network import check_url_availability, is_streaming_url
from core.config import get_config

# 导入日志配置
from .logging_config import get_logger, log_exception, log_performance

# 获取日志记录器
logger = get_logger(__name__)

def generate_channel_hash(channel: ChannelInfo, use_name: bool = True, use_url: bool = True, use_group: bool = False, use_tvg_id: bool = False) -> str:
    """
    生成频道的哈希值，用于去重
    
    参数:
        channel: 频道信息对象
        use_name: 是否使用频道名称进行哈希
        use_url: 是否使用URL进行哈希
        use_group: 是否使用分组信息进行哈希
        use_tvg_id: 是否使用TVG ID进行哈希
        
    返回:
        频道的哈希值
    """
    hash_input = []
    
    if use_tvg_id and channel.tvg_id:
        hash_input.append(channel.tvg_id.lower())
    
    if use_name and channel.name:
        # 标准化频道名称（去除特殊字符、空格，转换为小写）
        normalized_name = re.sub(r'[^\w\u4e00-\u9fa5]+', '', channel.name).lower()
        hash_input.append(normalized_name)
    
    if use_url and channel.url:
        # 标准化URL（去除参数，转换为小写）
        url = channel.url.lower()
        # 去除URL参数
        param_index = url.find('?')
        if param_index != -1:
            url = url[:param_index]
        # 去除尾部斜杠
        url = url.rstrip('/')
        hash_input.append(url)
    
    if use_group and channel.group:
        hash_input.append(channel.group.lower())
    
    if not hash_input:
        return hashlib.md5(str(time.time()).encode()).hexdigest()  # 避免空输入
    
    return hashlib.md5('|'.join(hash_input).encode()).hexdigest()

def deduplicate_channels(channels: List[ChannelInfo], by_name: bool = True, by_url: bool = True, by_group: bool = False, by_tvg_id: bool = False, keep_higher_quality: bool = False) -> List[ChannelInfo]:
    """
    频道去重
    
    参数:
        channels: 频道信息列表
        by_name: 是否按名称去重
        by_url: 是否按URL去重
        by_group: 是否考虑分组信息
        by_tvg_id: 是否按TVG ID去重
        keep_higher_quality: 是否保留质量更高的频道（基于URL质量评估）
        
    返回:
        去重后的频道信息列表
    """
    if not channels:
        return []
    
    start_time = time.time()
    logger.info(f"开始频道去重，输入频道数: {len(channels)}")
    
    # 按哈希值分组
    hash_groups = {}
    for channel in channels:
        channel_hash = generate_channel_hash(channel, use_name=by_name, use_url=by_url, use_group=by_group, use_tvg_id=by_tvg_id)
        
        if channel_hash not in hash_groups:
            hash_groups[channel_hash] = []
        hash_groups[channel_hash].append(channel)
    
    # 处理每个分组
    unique_channels = []
    for channel_hash, group_channels in hash_groups.items():
        if len(group_channels) == 1:
            # 只有一个频道，直接保留
            unique_channels.append(group_channels[0])
        else:
            # 有多个重复频道，需要选择保留哪个
            if keep_higher_quality:
                # 评估质量并选择最好的
                best_channel = None
                best_score = -1
                
                for channel in group_channels:
                    # 简单的质量评估
                    score = 0
                    
                    # URL中包含高清标记的加分
                    if 'hd' in channel.url.lower() or '1080' in channel.url.lower():
                        score += 20
                    if '4k' in channel.url.lower():
                        score += 30
                    
                    # 完整的tvg信息加分
                    if channel.tvg_id and channel.tvg_logo:
                        score += 20
                    
                    # 响应时间短的加分（如果有）
                    if hasattr(channel, 'response_time') and channel.response_time:
                        if channel.response_time < 1:
                            score += 30
                        elif channel.response_time < 3:
                            score += 20
                        elif channel.response_time < 5:
                            score += 10
                    
                    # 有分组信息的加分
                    if channel.group:
                        score += 10
                    
                    # 更新最好的频道
                    if score > best_score:
                        best_score = score
                        best_channel = channel
                
                if best_channel:
                    logger.debug(f"选择质量更高的频道: {best_channel.name} (质量分数: {best_score})")
                    unique_channels.append(best_channel)
                else:
                    # 默认保留第一个
                    unique_channels.append(group_channels[0])
            else:
                # 默认保留第一个
                unique_channels.append(group_channels[0])
    
    elapsed_time = time.time() - start_time
    removed_count = len(channels) - len(unique_channels)
    logger.info(f"频道去重完成，去重后频道数: {len(unique_channels)}")
    logger.info(f"去除重复频道数: {removed_count}")
    log_performance(logger, "频道去重", elapsed_time, input_count=len(channels), output_count=len(unique_channels), removed_count=removed_count, duplicate_groups=len(hash_groups))
    
    return unique_channels

def filter_channels(channels: List[ChannelInfo], 
                    name_pattern: Optional[str] = None, 
                    url_pattern: Optional[str] = None, 
                    group_pattern: Optional[str] = None, 
                    exclude_name_pattern: Optional[str] = None, 
                    exclude_url_pattern: Optional[str] = None, 
                    exclude_group_pattern: Optional[str] = None, 
                    custom_filter: Optional[Callable[[ChannelInfo], bool]] = None) -> List[ChannelInfo]:
    """
    频道过滤
    
    参数:
        channels: 频道信息列表
        name_pattern: 名称匹配正则表达式
        url_pattern: URL匹配正则表达式
        group_pattern: 分组匹配正则表达式
        exclude_name_pattern: 排除的名称正则表达式
        exclude_url_pattern: 排除的URL正则表达式
        exclude_group_pattern: 排除的分组正则表达式
        custom_filter: 自定义过滤函数
        
    返回:
        过滤后的频道信息列表
    """
    if not channels:
        return []
    
    filtered_channels = []
    
    for channel in channels:
        # 检查排除条件
        if exclude_name_pattern and re.search(exclude_name_pattern, channel.name, re.IGNORECASE):
            continue
        
        if exclude_url_pattern and re.search(exclude_url_pattern, channel.url, re.IGNORECASE):
            continue
        
        if exclude_group_pattern and re.search(exclude_group_pattern, channel.group, re.IGNORECASE):
            continue
        
        # 检查包含条件
        if name_pattern and not re.search(name_pattern, channel.name, re.IGNORECASE):
            continue
        
        if url_pattern and not re.search(url_pattern, channel.url, re.IGNORECASE):
            continue
        
        if group_pattern and not re.search(group_pattern, channel.group, re.IGNORECASE):
            continue
        
        # 检查自定义过滤函数
        if custom_filter and not custom_filter(channel):
            continue
        
        filtered_channels.append(channel)
    
    logger.info(f"频道过滤完成，输入: {len(channels)}，输出: {len(filtered_channels)}")
    return filtered_channels

def group_channels(channels: List[ChannelInfo]) -> Dict[str, List[ChannelInfo]]:
    """
    按分组对频道进行分组
    
    参数:
        channels: 频道信息列表
        
    返回:
        字典，键为分组名称，值为该分组下的频道列表
    """
    if not channels:
        return {}
    
    grouped = {}
    
    for channel in channels:
        group_name = channel.group or '未分组'
        
        if group_name not in grouped:
            grouped[group_name] = []
        
        grouped[group_name].append(channel)
    
    logger.info(f"频道分组完成，共 {len(grouped)} 个分组")
    return grouped

def sort_channels(channels: List[ChannelInfo], key: str = 'name', reverse: bool = False) -> List[ChannelInfo]:
    """
    对频道进行排序
    
    参数:
        channels: 频道信息列表
        key: 排序键，可选值: 'name', 'url', 'group'
        reverse: 是否逆序排列
        
    返回:
        排序后的频道信息列表
    """
    if not channels:
        return []
    
    if key not in ['name', 'url', 'group']:
        logger.error(f"不支持的排序键: {key}")
        return channels
    
    def get_sort_value(channel: ChannelInfo) -> str:
        if key == 'name':
            return channel.name
        elif key == 'url':
            return channel.url
        else:
            return channel.group
    
    sorted_channels = sorted(channels, key=get_sort_value, reverse=reverse)
    logger.info(f"频道排序完成，按 {key} {'逆序' if reverse else '正序'}")
    
    return sorted_channels

def validate_channels(channels: List[ChannelInfo], check_availability: bool = False, timeout: int = 3) -> Tuple[List[ChannelInfo], List[ChannelInfo]]:
    """
    验证频道的有效性
    
    参数:
        channels: 频道信息列表
        check_availability: 是否检查URL可用性
        timeout: 检查超时时间（秒）
        
    返回:
        (有效频道列表, 无效频道列表)
    """
    if not channels:
        return [], []
    
    valid_channels = []
    invalid_channels = []
    
    logger.info(f"开始验证 {len(channels)} 个频道")
    
    for i, channel in enumerate(channels, 1):
        logger.debug(f"验证频道 {i}/{len(channels)}: {channel.name}")
        
        # 基本验证
        if not channel.name or not channel.url:
            logger.warning(f"频道验证失败 {channel.name}: 名称或URL为空")
            invalid_channels.append(channel)
            continue
        
        # 验证URL格式
        if not channel.url.startswith(('http://', 'https://', 'rtmp://', 'rtsp://', 'm3u8://')):
            logger.warning(f"频道验证失败 {channel.name}: URL格式无效")
            invalid_channels.append(channel)
            continue
        
        # 检查URL可用性
        if check_availability:
            try:
                result = check_url_availability(channel.url, timeout=timeout)
                
                if not result['available']:
                    logger.warning(f"频道验证失败 {channel.name}: URL不可用 ({result.get('error', '未知错误')})")
                    invalid_channels.append(channel)
                    continue
                
                # 检查是否为流媒体URL
                if not is_streaming_url(channel.url, timeout=timeout):
                    logger.warning(f"频道验证失败 {channel.name}: 不是有效的流媒体URL")
                    invalid_channels.append(channel)
                    continue
                    
            except Exception as e:
                logger.warning(f"频道验证异常 {channel.name}: {e}")
                # 不中断验证，将其视为有效频道
        
        valid_channels.append(channel)
    
    logger.info(f"频道验证完成，有效: {len(valid_channels)}，无效: {len(invalid_channels)}")
    return valid_channels, invalid_channels

def evaluate_channel_quality(channel: ChannelInfo, timeout: int = 5) -> Dict[str, Any]:
    """
    评估频道质量
    
    参数:
        channel: 频道信息对象
        timeout: 检查超时时间（秒）
        
    返回:
        质量评估结果字典
    """
    quality = {
        'name': channel.name,
        'url': channel.url,
        'available': False,
        'response_time': None,
        'status_code': None,
        'is_streaming': False,
        'quality_score': 0,
        'error': None
    }
    
    try:
        # 检查URL可用性
        availability = check_url_availability(channel.url, timeout=timeout)
        
        quality['available'] = availability['available']
        quality['response_time'] = availability['response_time']
        quality['status_code'] = availability['status_code']
        quality['error'] = availability['error']
        
        if availability['available']:
            # 检查是否为流媒体URL
            quality['is_streaming'] = is_streaming_url(channel.url, timeout=timeout)
            
            # 计算质量分数
            score = 50  # 基础分数
            
            # 根据响应时间评分（越快分数越高）
            if availability['response_time']:
                if availability['response_time'] < 1:
                    score += 30
                elif availability['response_time'] < 3:
                    score += 20
                elif availability['response_time'] < 5:
                    score += 10
            
            # 根据是否为流媒体URL评分
            if quality['is_streaming']:
                score += 20
            
            quality['quality_score'] = min(100, max(0, score))
        
    except Exception as e:
        logger.error(f"频道质量评估失败 {channel.name}: {e}")
        quality['error'] = str(e)
    
    return quality

def batch_evaluate_quality(channels: List[ChannelInfo], max_workers: int = 10, timeout: int = 5, update_channels: bool = False) -> List[Dict[str, Any]]:
    """
    批量评估频道质量
    
    参数:
        channels: 频道信息列表
        max_workers: 最大并发数
        timeout: 检查超时时间（秒）
        update_channels: 是否将质量评估结果更新到频道对象中
        
    返回:
        质量评估结果列表
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    if not channels:
        return []
    
    results = []
    
    logger.info(f"开始批量评估 {len(channels)} 个频道的质量")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_channel = {
            executor.submit(evaluate_channel_quality, channel, timeout): channel for channel in channels
        }
        
        # 处理结果
        for i, future in enumerate(as_completed(future_to_channel), 1):
            channel = future_to_channel[future]
            try:
                result = future.result()
                results.append(result)
                logger.debug(f"频道质量评估完成 {i}/{len(channels)}: {channel.name} (分数: {result['quality_score']})")
                
                # 更新频道对象
                if update_channels:
                    channel.response_time = result.get('response_time')
                    channel.quality_score = result.get('quality_score')
                    channel.is_available = result.get('available')
                    channel.is_streaming = result.get('is_streaming')
                    
            except Exception as e:
                logger.error(f"频道质量评估异常 {i}/{len(channels)}: {channel.name}: {e}")
    
    logger.info(f"批量频道质量评估完成")
    return results

def get_channel_statistics(channels: List[ChannelInfo]) -> Dict[str, Any]:
    """
    获取频道统计信息
    
    参数:
        channels: 频道信息列表
        
    返回:
        统计信息字典
    """
    if not channels:
        return {
            'total_channels': 0,
            'total_groups': 0,
            'groups': {},
            'cctv_channels': 0,
            'cctv_ratio': 0,
            'average_name_length': 0,
            'average_url_length': 0
        }
    
    # 分组统计
    grouped = group_channels(channels)
    
    # 计算平均长度
    total_name_length = sum(len(channel.name) for channel in channels)
    total_url_length = sum(len(channel.url) for channel in channels)
    
    # 统计CCTV频道数量
    cctv_count = 0
    for channel in channels:
        if 'CCTV' in channel.name.upper():
            cctv_count += 1
    
    cctv_ratio = cctv_count / len(channels) if len(channels) > 0 else 0
    
    stats = {
        'total_channels': len(channels),
        'total_groups': len(grouped),
        'groups': {group: len(channels) for group, channels in grouped.items()},
        'cctv_channels': cctv_count,
        'cctv_ratio': cctv_ratio,
        'average_name_length': total_name_length / len(channels),
        'average_url_length': total_url_length / len(channels)
    }
    
    logger.info(f"获取频道统计信息完成")
    return stats

def search_channels(channels: List[ChannelInfo], keyword: str, search_in_name: bool = True, search_in_group: bool = False) -> List[ChannelInfo]:
    """
    搜索频道
    
    参数:
        channels: 频道信息列表
        keyword: 搜索关键词
        search_in_name: 是否在名称中搜索
        search_in_group: 是否在分组中搜索
        
    返回:
        匹配的频道列表
    """
    if not channels or not keyword:
        return []
    
    keyword = keyword.lower()
    matched_channels = []
    
    for channel in channels:
        match = False
        
        if search_in_name and keyword in channel.name.lower():
            match = True
        
        if search_in_group and keyword in (channel.group.lower() if channel.group else ''):
            match = True
        
        if match:
            matched_channels.append(channel)
    
    logger.info(f"频道搜索完成，关键词: '{keyword}'，找到 {len(matched_channels)} 个匹配结果")
    return matched_channels

def get_video_resolution_ffmpeg(url: str, timeout: int = 5) -> Optional[Tuple[int, int]]:
    """
    使用FFmpeg获取视频流的分辨率
    
    参数:
        url: 视频流URL
        timeout: 超时时间（秒）
        
    返回:
        Tuple[int, int]: (宽度, 高度)，如果获取失败返回None
    """
    try:
        # 构建FFmpeg命令
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            url
        ]
        
        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        
        # 解析输出
        output = result.stdout.strip()
        if output:
            width, height = map(int, output.split(','))
            return (width, height)
        
        return None
    except subprocess.TimeoutExpired:
        logger.warning(f"获取分辨率超时: {url}")
        return None
    except subprocess.CalledProcessError as e:
        logger.warning(f"FFmpeg获取分辨率失败: {url} - {e.stderr.strip()}")
        return None
    except Exception as e:
        logger.error(f"获取视频分辨率失败: {url} - {e}")
        return None

def get_video_resolution_from_url(url: str) -> Optional[Tuple[int, int]]:
    """
    从URL模式中提取分辨率信息
    优点: 速度极快
    缺点: 准确性有限，依赖URL命名规范
    
    参数:
        url: 视频流URL
        
    返回:
        Tuple[int, int]: (宽度, 高度)，如果无法提取返回None
    """
    url_lower = url.lower()
    
    # 常见的分辨率模式
    resolution_patterns = [
        # 如 1080p, 720p, 480p, 2160p(4K)
        r'(\d{3,4})p',
        # 如 1920x1080, 1280x720, 3840x2160
        r'(\d{3,4})[x_](\d{3,4})',
        # 如 1920*1080, 1280*720
        r'(\d{3,4})\*(\d{3,4})',
        # 如 ?width=1920&height=1080
        r'width=(\d{3,4})[^0-9]*height=(\d{3,4})',
        # 如 &w=1920&h=1080
        r'w=(\d{3,4})[^0-9]*h=(\d{3,4})',
        # 如 /hd/, /high/, /1080/, /720/ 等路径中的高清标识
        r'/(hd|high|1080|720|2160|4k)/',
        # 如 -hd-, _hd_, .hd., .high. 等分隔符中的高清标识
        r'[-_.](hd|high|1080|720|2160|4k)[-_.]'
    ]
    
    for pattern in resolution_patterns:
        match = re.search(pattern, url_lower)
        if match:
            groups = match.groups()
            if len(groups) == 1:
                # 只有高度的情况，如 1080p 或高清标识
                if groups[0].isdigit():
                    height = int(groups[0])
                    # 根据常见宽高比计算宽度
                    if height == 2160:  # 4K
                        return (3840, 2160)
                    elif height == 1080:
                        return (1920, 1080)
                    elif height == 720:
                        return (1280, 720)
                    elif height == 480:
                        return (854, 480)
                    elif height == 360:
                        return (640, 360)
                else:
                    # 高清标识，默认返回1080p
                    return (1920, 1080)
            elif len(groups) == 2:
                # 同时有宽度和高度的情况
                width = int(groups[0])
                height = int(groups[1])
                return (width, height)
    
    return None

def get_video_resolution_from_stream_type(url: str) -> Optional[Tuple[int, int]]:
    """
    根据视频流类型判断分辨率
    优点: 速度极快
    缺点: 准确性低，仅作参考
    
    参数:
        url: 视频流URL
        
    返回:
        Tuple[int, int]: (宽度, 高度)，如果无法判断返回None
    """
    url_lower = url.lower()
    
    # 根据文件扩展名或路径判断
    hd_extensions = ['.ts', '.m3u8', '.mp4']
    hd_keywords = ['hd', 'high', 'quality', '1080', '1920', '4k', 'ultra']
    
    # 检查是否是高清格式
    if any(ext in url_lower for ext in hd_extensions):
        # 检查是否包含高清关键词
        if any(keyword in url_lower for keyword in hd_keywords):
            return (1920, 1080)
    
    return None

def get_video_resolution(url: str, timeout: int = 5) -> Optional[Tuple[int, int]]:
    """
    获取视频流的分辨率
    采用分层筛选策略：
    1. URL模式匹配（速度最快）
    2. 流类型检测（速度快）
    3. FFmpeg实际检测（最准确但速度慢，在GitHub Actions环境中默认不使用）
    
    参数:
        url: 视频流URL
        timeout: 超时时间（秒）
        
    返回:
        Tuple[int, int]: (宽度, 高度)，如果获取失败返回None
    """
    # 第一层：URL模式匹配
    resolution = get_video_resolution_from_url(url)
    if resolution:
        logger.debug(f"从URL模式获取分辨率: {url} -> {resolution[0]}x{resolution[1]}")
        return resolution
    
    # 第二层：流类型检测
    resolution = get_video_resolution_from_stream_type(url)
    if resolution:
        logger.debug(f"从流类型获取分辨率: {url} -> {resolution[0]}x{resolution[1]}")
        return resolution
    
    # 第三层：FFmpeg实际检测
    # 检查是否在GitHub Actions环境中
    is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    
    if is_github_actions:
        logger.debug(f"GitHub Actions环境中跳过FFmpeg检测: {url}")
        # 在GitHub Actions环境中，我们可以更宽松地判断，例如认为某些流类型默认是高清
        url_lower = url.lower()
        if any(ext in url_lower for ext in ['.ts', '.m3u8', '.mp4']):
            logger.debug(f"GitHub Actions环境中默认将 {url} 视为高清")
            return (1920, 1080)
        return None
    else:
        logger.debug(f"使用FFmpeg检测分辨率: {url}")
        return get_video_resolution_ffmpeg(url, timeout)

def should_exclude_resolution(url: str, channel_name: str = '', min_resolution: str = '1920x1080') -> bool:
    """
    判断是否应该根据分辨率排除URL
    仅检查频道名称中括号内的分辨率标识，如 (576p), (720p), (1080p)
    
    参数:
        url: 视频流URL
        channel_name: 频道名称
        min_resolution: 最小分辨率，格式为 'widthxheight'
        
    返回:
        bool: 应该排除返回True，否则返回False
    """
    try:
        # 解析最小分辨率高度
        min_height = int(min_resolution.split('x')[1])
        
        # 仅检查频道名称中括号内的分辨率标识
        if channel_name:
            # 匹配括号中的分辨率信息，如 (576p), (720p), (1080p)
            name_resolution_match = re.search(r'\((\d{3,4})p\)', channel_name, re.IGNORECASE)
            if name_resolution_match:
                height = int(name_resolution_match.group(1))
                
                # 检查是否低于最小分辨率
                if height < min_height:
                    logger.info(f"排除低分辨率频道: {channel_name} (分辨率: {height}p)")
                    return True
    
        # 不在频道名称中显示低分辨率的，默认不排除
        return False
    except Exception as e:
        logger.error(f"检查分辨率是否应该排除时发生错误: {e}")
        return False

def normalize_channel_name(name: str) -> str:
    """
    标准化频道名称
    
    参数:
        name: 原始频道名称
        
    返回:
        标准化后的频道名称
    """
    if not name:
        return ''
    
    # 去除前后空格
    name = name.strip()
    
    # 替换常见的特殊字符和分隔符
    name = re.sub(r'[\s_\-\.]+', ' ', name)
    
    # 去除多余的空格
    name = re.sub(r'\s+', ' ', name)
    
    # 去除常见的前缀后缀
    prefixes = [r'[\s\[\(]*(高清|HD|标清|SD|超清|4K|蓝光)[\s\]\)]*', r'[\s\[\(]*(直播|卫视|电视台|频道)[\s\]\)]*']
    for prefix in prefixes:
        name = re.sub(r'^' + prefix, '', name, flags=re.IGNORECASE)
        name = re.sub(r'' + prefix + '$', '', name, flags=re.IGNORECASE)
    
    # 去除多余的空格
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def enrich_channel_info(channel: ChannelInfo) -> ChannelInfo:
    """
    丰富频道信息
    
    参数:
        channel: 频道信息对象
        
    返回:
        丰富后的频道信息对象
    """
    # 标准化频道名称
    channel.name = normalize_channel_name(channel.name)
    
    # 尝试从URL中提取信息
    if channel.url and not channel.tvg_logo:
        # 可以在这里添加从URL提取logo等信息的逻辑
        pass
    
    # 尝试从名称中提取分组信息
    if not channel.group:
        # 简单的分组逻辑（根据名称中的关键字）
        if 'CCTV' in channel.name or '央视' in channel.name:
            channel.group = '央视'
        elif '卫视' in channel.name:
            channel.group = '卫视'
        elif '电影' in channel.name:
            channel.group = '电影'
        elif '体育' in channel.name:
            channel.group = '体育'
    
    return channel

if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    # 创建测试频道
    test_channels = [
        ChannelInfo(name='CCTV-1综合', url='http://example.com/cctv1.m3u8', group='央视'),
        ChannelInfo(name='CCTV-2财经', url='http://example.com/cctv2.m3u8', group='央视'),
        ChannelInfo(name='CCTV-1 高清', url='http://example.com/cctv1_hd.m3u8', group='央视'),  # 重复名称
        ChannelInfo(name='湖南卫视', url='http://example.com/hunan.m3u8', group='卫视'),
        ChannelInfo(name='浙江卫视', url='http://example.com/zhejiang.m3u8', group='卫视'),
        ChannelInfo(name='湖南卫视', url='http://example.com/hunan2.m3u8', group='卫视'),  # 重复名称
        ChannelInfo(name='未知频道', url='http://example.com/unknown.m3u8'),  # 无分组
    ]
    
    print("测试频道去重:")
    deduplicated = deduplicate_channels(test_channels, by_name=True, by_url=False)
    for channel in deduplicated:
        print(f"  {channel}")
    
    print("\n测试频道过滤（只保留央视）:")
    filtered = filter_channels(test_channels, group_pattern='央视')
    for channel in filtered:
        print(f"  {channel}")
    
    print("\n测试频道分组:")
    grouped = group_channels(test_channels)
    for group, channels in grouped.items():
        print(f"  分组 '{group}': {len(channels)}个频道")
    
    print("\n测试频道排序:")
    sorted_ch = sort_channels(test_channels, key='name')
    for channel in sorted_ch:
        print(f"  {channel}")
    
    print("\n测试频道验证:")
    valid, invalid = validate_channels(test_channels, check_availability=False)
    print(f"  有效频道: {len(valid)}")
    print(f"  无效频道: {len(invalid)}")
    
    print("\n测试频道统计:")
    stats = get_channel_statistics(test_channels)
    print(f"  {stats}")
    
    print("\n测试频道搜索:")
    searched = search_channels(test_channels, '央视')
    for channel in searched:
        print(f"  {channel}")
    
    print("\n测试频道标准化:")
    print(f"  '[高清] CCTV-1 综合 直播': {normalize_channel_name('[高清] CCTV-1 综合 直播')}")
    print(f"  '湖南卫视_HD.': {normalize_channel_name('湖南卫视_HD.')}")