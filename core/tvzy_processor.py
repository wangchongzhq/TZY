#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVZY频道处理模块
功能：提供频道过滤、分类、合并等功能
"""

import re
from typing import List, Dict

# 导入核心模块
from .parser import ChannelInfo
from .config import get_config
from .logging_config import get_logger, log_exception, log_performance

# 获取日志记录器
logger = get_logger(__name__)

# 从配置获取频道分类和映射
def get_channel_categories() -> Dict[str, List[str]]:
    """
    获取频道分类配置
    
    返回:
        Dict[str, List[str]]: 频道分类字典，键为分类名称，值为该分类包含的频道名称列表
    """
    return get_config('channel.categories', {
        "4K频道": ['CCTV4K', 'CCTV16 4K', '北京卫视4K', '北京IPTV4K', '湖南卫视4K', '山东卫视4K', '广东卫视4K', '四川卫视4K',
                  '浙江卫视4K', '江苏卫视4K', '东方卫视4K', '深圳卫视4K', '河北卫视4K', '峨眉电影4K', '求索4K', '咪视界4K', '欢笑剧场4K',
                  '苏州4K', '至臻视界4K', '南国都市4K', '翡翠台4K', '百事通电影4K', '百事通少儿4K', '百事通纪实4K', '华数爱上4K'],
        "央视频道": ['CCTV1', 'CCTV2', 'CCTV3', 'CCTV4', 'CCTV4欧洲', 'CCTV4美洲', 'CCTV5', 'CCTV5+', 'CCTV6', 'CCTV7', 'CCTV8', 'CCTV9',
                    'CCTV10', 'CCTV11', 'CCTV12', 'CCTV13', 'CCTV14', 'CCTV15', 'CCTV16', 'CCTV17', '兵器科技', '风云音乐', '风云足球',
                    '风云剧场', '怀旧剧场', '第一剧场', '女性时尚', '世界地理', '央视台球', '高尔夫网球', '央视文化精品', '北京纪实科教',
                    '卫生健康', '电视指南']
    })

# 从配置获取频道映射
def get_channel_mapping() -> Dict[str, List[str]]:
    """
    获取频道映射配置
    
    返回:
        Dict[str, List[str]]: 频道映射字典，键为频道名称，值为该频道的别名列表
    """
    channel_config = get_config('channel', {})
    mapping = channel_config.get('mapping', {})
    
    # 如果配置中没有提供频道映射，使用默认的映射逻辑
    if not mapping:
        categories = get_channel_categories()
        mapping = {}
        for category, channels in categories.items():
            for channel in channels:
                mapping[channel] = [channel]
        
        additional_mappings = {
            "CCTV4K": ["CCTV 4K", "CCTV-4K"],
            "CCTV16 4K": ["CCTV16 4K", "CCTV16-4K", "CCTV16 奥林匹克 4K", "CCTV16奥林匹克 4K"],
        }
        
        # 添加额外的映射
        for channel, aliases in additional_mappings.items():
            if channel in mapping:
                mapping[channel].extend(aliases)
    
    return mapping

# 检测频道清晰度
def detect_resolution(channel: ChannelInfo) -> int:
    """
    检测频道的清晰度等级
    
    参数:
        channel: 频道信息对象
    
    返回:
        int: 清晰度等级，数值越大清晰度越高
             - 0: 未知清晰度
             - 1: 标清 (≤720p)
             - 2: 高清 (1080p)
             - 3: 超清 (4K)
    """
    # 组合频道名称和URL进行检测
    text = f"{channel.name} {channel.url}".lower()
    
    # 检查是否包含4K
    if '4k' in text:
        return 3
    
    # 检查是否包含1080p
    if '1080p' in text or 'fullhd' in text or ('hd' in text and '720' not in text):
        return 2
    
    # 检查是否包含720p或更低
    if '720p' in text or '576p' in text or '480p' in text or '360p' in text or 'sd' in text:
        return 1
    
    # 默认返回未知清晰度
    return 0

# 过滤频道名称
def filter_channel_name(name: str) -> str:
    """
    过滤频道名称
    
    参数:
        name: 原始频道名称
    
    返回:
        str: 过滤后的频道名称
    """
    # 移除括号内的清晰度信息，如(576p)、(576)、(1080p)等
    name = re.sub(r'\s*\([0-9]+p?\)\s*', '', name)
    
    # 去除频道名称中的特殊字符
    name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\-\_]+', '', name)
    
    # 去除前后空格
    name = name.strip()
    
    # 去除常见的后缀
    suffixes = ['高清', '超清', '标清', 'HD', 'SD', '1080P', '720P', '4K', '直播']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
            break
    
    return name

# 对频道进行分类
def categorize_channel(channel: ChannelInfo) -> str:
    """
    对频道进行分类
    
    参数:
        channel: 频道信息对象
    
    返回:
        str: 频道的分类名称
    """
    # 过滤频道名称
    filtered_name = filter_channel_name(channel.name)
    
    # 查找匹配的分类
    categories = get_channel_categories()
    for category, channels in categories.items():
        for channel_name in channels:
            if channel_name in filtered_name:
                return category
    
    # 没有匹配的分类，返回默认分类
    return "其他频道"

# 合并多个数据源的频道信息
def merge_channels(all_channels: List[ChannelInfo], max_lines_per_channel: int = 90) -> List[ChannelInfo]:
    """
    合并多个数据源的频道信息
    
    参数:
        all_channels: 所有数据源的频道信息列表
        max_lines_per_channel: 每个频道保留的最大流地址数量
    
    返回:
        List[ChannelInfo]: 合并后的频道信息列表
    """
    # 使用字典来存储频道信息，键为频道名称，值为频道列表
    channel_dict = {}
    
    for channel in all_channels:
        # 过滤频道名称
        filtered_name = filter_channel_name(channel.name)
        
        # 跳过空名称
        if not filtered_name:
            continue
        
        # 检测频道清晰度，只保留1080p及以上的高清线路（清晰度等级2或3）
        resolution = detect_resolution(channel)
        if resolution < 2:
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
        unique_channels = unique_channels[:max_lines_per_channel]
        
        # 添加到合并后的列表中
        merged_channels.extend(unique_channels)
    
    return merged_channels

# 生成输出内容
def generate_output(channels: List[ChannelInfo]) -> str:
    """
    生成输出内容
    
    参数:
        channels: 频道信息列表
    
    返回:
        str: 生成的输出内容
    """
    output = []
    
    # 按分类对频道进行排序
    channels.sort(key=lambda x: (x.category, x.name))
    
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

if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试频道分类
    test_channels = [
        ChannelInfo(name='CCTV1 高清', url='http://example.com/cctv1.m3u8'),
        ChannelInfo(name='CCTV16 4K 奥运', url='http://example.com/cctv16_4k.m3u8'),
        ChannelInfo(name='湖南卫视', url='http://example.com/hunan.m3u8'),
        ChannelInfo(name='未知频道', url='http://example.com/unknown.m3u8')
    ]
    
    print("测试频道分类:")
    for channel in test_channels:
        category = categorize_channel(channel)
        print(f"  频道 {channel.name} 分类为: {category}")
    
    # 测试频道名称过滤
    print("\n测试频道名称过滤:")
    test_names = ['CCTV1 高清', 'CCTV-2财经 HD', '湖南卫视_超清', '东方卫视 1080P']
    for name in test_names:
        filtered = filter_channel_name(name)
        print(f"  原始名称: {name} -> 过滤后: {filtered}")
    
    # 测试合并频道
    print("\n测试合并频道:")
    duplicate_channels = [
        ChannelInfo(name='CCTV1 高清', url='http://example.com/cctv1.m3u8'),
        ChannelInfo(name='CCTV1', url='http://example.com/cctv1_2.m3u8'),
        ChannelInfo(name='CCTV1 高清', url='http://example.com/cctv1.m3u8')  # 重复URL
    ]
    
    merged = merge_channels(duplicate_channels)
    print(f"  合并前: {len(duplicate_channels)} 个频道")
    print(f"  合并后: {len(merged)} 个频道")
    for channel in merged:
        print(f"    {channel.name} -> {channel.url} (分类: {channel.category})")
