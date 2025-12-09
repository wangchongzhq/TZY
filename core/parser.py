#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一格式解析模块
功能：提供M3U、TXT等格式的统一解析功能
"""

import re
import time
from typing import List, Dict, Tuple, Optional

# 导入日志配置
from .logging_config import get_logger, log_exception, log_performance

# 获取日志记录器
logger = get_logger(__name__)

class ChannelInfo:
    """
    频道信息类
    """
    def __init__(self, name: str, url: str, group: str = "", tvg_id: str = "", tvg_name: str = "", tvg_logo: str = "", tvg_url: str = ""):
        self.name = name
        self.url = url
        self.group = group
        self.tvg_id = tvg_id
        self.tvg_name = tvg_name
        self.tvg_logo = tvg_logo
        self.tvg_url = tvg_url
        
    def __repr__(self):
        return f"ChannelInfo(name='{self.name}', url='{self.url}', group='{self.group}')"
        
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'name': self.name,
            'url': self.url,
            'group': self.group,
            'tvg_id': self.tvg_id,
            'tvg_name': self.tvg_name,
            'tvg_logo': self.tvg_logo,
            'tvg_url': self.tvg_url
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChannelInfo':
        """从字典创建实例"""
        return cls(
            name=data.get('name', ''),
            url=data.get('url', ''),
            group=data.get('group', ''),
            tvg_id=data.get('tvg_id', ''),
            tvg_name=data.get('tvg_name', ''),
            tvg_logo=data.get('tvg_logo', ''),
            tvg_url=data.get('tvg_url', '')
        )

def parse_m3u_content(content: str) -> List[ChannelInfo]:
    """
    解析M3U格式的直播源内容
    
    参数:
        content: M3U格式的文本内容
        
    返回:
        频道信息列表
    """
    start_time = time.time()
    channels = []
    
    if not content:
        logger.warning("M3U内容为空")
        return channels
    
    lines = content.strip().split('\n')
    
    # 检查是否为M3U格式
    if not lines or not lines[0].strip().startswith('#EXTM3U'):
        logger.error("无效的M3U格式，缺少#EXTM3U头部")
        return channels
    
    current_channel = None
    current_tvg = {}
    current_group = ""
    
    for line in lines[1:]:  # 跳过#EXTM3U行
        line = line.strip()
        if not line:
            continue
        
        # 处理EXTINF行
        if line.startswith('#EXTINF:'):
            # 如果有未完成的频道，保存它
            if current_channel:
                channels.append(current_channel)
            
            # 重置当前频道信息
            current_tvg = {}
            current_group = ""
            
            # 解析EXTINF参数
            extinf_match = re.match(r'#EXTINF:(-?\d+)?\s*(.*?)?,(.*)', line)
            if not extinf_match:
                logger.error(f"无效的EXTINF行: {line}")
                continue
            
            # 解析tvg属性
            extinf_attrs = extinf_match.group(2) or ""
            name = extinf_match.group(3) or ""
            
            # 提取tvg相关属性
            tvg_attrs = {
                'id': re.search(r'tvg-id="(.*?)"', extinf_attrs),
                'name': re.search(r'tvg-name="(.*?)"', extinf_attrs),
                'logo': re.search(r'tvg-logo="(.*?)"', extinf_attrs),
                'url': re.search(r'tvg-url="(.*?)"', extinf_attrs)
            }
            
            for attr, match in tvg_attrs.items():
                if match:
                    current_tvg[f'tvg_{attr}'] = match.group(1)
            
            # 提取group-title
            group_match = re.search(r'group-title="(.*?)"', extinf_attrs)
            if group_match:
                current_group = group_match.group(1)
            
            current_channel = None
            
        elif line.startswith('#'):
            # 忽略其他注释行
            continue
        
        elif line and line.startswith(('http://', 'https://', 'rtmp://', 'rtsp://', 'm3u8://')):
            # 这是一个URL行
            if not current_channel:
                # 创建频道对象
                current_channel = ChannelInfo(
                    name=name,
                    url=line,
                    group=current_group,
                    **current_tvg
                )
            else:
                logger.warning(f"URL行前没有对应的EXTINF行: {line}")
    
    # 保存最后一个频道
    if current_channel:
        channels.append(current_channel)
    
    # 记录性能信息
    elapsed_time = time.time() - start_time
    log_performance(logger, "解析M3U内容", elapsed_time, channel_count=len(channels))
    
    logger.info(f"解析M3U内容，找到 {len(channels)} 个频道")
    return channels

def parse_txt_content(content: str, delimiter: str = '|') -> List[ChannelInfo]:
    """
    解析TXT格式的直播源内容
    
    参数:
        content: TXT格式的文本内容
        delimiter: 分隔符，默认为'|'
        
    返回:
        频道信息列表
    """
    channels = []
    
    if not content:
        logger.warning("TXT内容为空")
        return channels
    
    lines = content.strip().split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        try:
            # 分割频道信息
            parts = line.split(delimiter)
            
            if len(parts) < 2:
                logger.warning(f"第 {line_num} 行格式错误: {line}")
                continue
            
            # 解析频道名称和URL
            if parts[0].startswith(('http://', 'https://', 'rtmp://', 'rtsp://', 'm3u8://')):
                url = parts[0]
                name = delimiter.join(parts[1:])
            else:
                name = parts[0]
                url = parts[1]
            
            # 检查URL格式
            if not url.startswith(('http://', 'https://', 'rtmp://', 'rtsp://', 'm3u8://')):
                logger.warning(f"第 {line_num} 行URL格式错误: {url}")
                continue
            
            # 尝试提取group信息（如果有）
            group = ""
            if len(parts) >= 3:
                group = parts[2]
            
            channel = ChannelInfo(name=name, url=url, group=group)
            channels.append(channel)
            
        except Exception as e:
            logger.error(f"解析第 {line_num} 行时出错: {e}")
            continue
    
    logger.info(f"成功解析TXT格式，共找到 {len(channels)} 个频道")
    return channels

def detect_content_format(content: str) -> str:
    """
    检测内容格式
    
    参数:
        content: 要检测的文本内容
        
    返回:
        格式类型: 'm3u' 或 'txt'
    """
    if not content:
        return 'txt'  # 默认返回txt
    
    # 检查是否为M3U格式
    if content.strip().startswith('#EXTM3U'):
        return 'm3u'
    
    # 检查是否包含M3U特征
    if '#EXTINF:' in content and 'http://' in content:
        return 'm3u'
    
    return 'txt'  # 默认返回txt

def parse_content(content: str, format_type: Optional[str] = None) -> List[ChannelInfo]:
    """
    统一解析接口，自动检测格式
    
    参数:
        content: 要解析的文本内容
        format_type: 格式类型，可选值: 'm3u', 'txt'，如果为None则自动检测
        
    返回:
        频道信息列表
    """
    if format_type is None:
        format_type = detect_content_format(content)
        logger.info(f"自动检测到格式: {format_type}")
    
    if format_type == 'm3u':
        return parse_m3u_content(content)
    elif format_type == 'txt':
        return parse_txt_content(content)
    else:
        logger.error(f"不支持的格式类型: {format_type}")
        return []

def generate_m3u_content(channels: List[ChannelInfo]) -> str:
    """
    生成M3U格式的内容
    
    参数:
        channels: 频道信息列表
        
    返回:
        M3U格式的文本内容
    """
    from collections import defaultdict
    from .config import get_config
    
    # 按分类分组频道
    channels_by_group = defaultdict(list)
    for channel in channels:
        group = channel.group or "未分类"
        channels_by_group[group].append(channel)
    
    # 对每个分类内的频道按名称升序排序
    for group in channels_by_group:
        channels_by_group[group].sort(key=lambda x: x.name)
    
    # 按照要求的固定顺序输出频道分类
    required_order = [
        "4K频道", "央视频道", "卫视频道", "北京专属频道", "山东专属频道", 
        "港澳频道", "电影频道", "儿童频道", "iHOT频道", "综合频道", 
        "体育频道", "剧场频道", "其他频道"
    ]
    
    # 按要求的顺序排序分类
    sorted_groups = []
    for group in required_order:
        if group in channels_by_group:
            sorted_groups.append(group)
    
    # 添加不在要求顺序中的其他分组，按名称升序排序
    other_groups = [group for group in channels_by_group.keys() if group not in required_order]
    sorted_groups.extend(sorted(other_groups))
    
    lines = ['#EXTM3U']
    
    # 生成M3U内容
    for group in sorted_groups:
        for channel in channels_by_group[group]:
            # 构建EXTINF行
            extinf_line = '#EXTINF:-1'
            
            # 添加tvg信息
            if channel.tvg_id:
                extinf_line += f' tvg-id="{channel.tvg_id}"'
            if channel.tvg_name:
                extinf_line += f' tvg-name="{channel.tvg_name}"'
            if channel.tvg_logo:
                extinf_line += f' tvg-logo="{channel.tvg_logo}"'
            if channel.tvg_url:
                extinf_line += f' tvg-url="{channel.tvg_url}"'
            
            # 添加group-title
            if channel.group:
                extinf_line += f' group-title="{channel.group}"'
            
            # 添加频道名称
            extinf_line += f',{channel.name}'
            
            lines.append(extinf_line)
            lines.append(channel.url)
    
    return '\n'.join(lines)

def generate_txt_content(channels: List[ChannelInfo], delimiter: str = '|') -> str:
    """
    生成TXT格式的内容
    
    参数:
        channels: 频道信息列表
        delimiter: 分隔符，默认为'|'
        
    返回:
        TXT格式的文本内容
    """
    from collections import defaultdict
    from .config import get_config
    
    # 按分类分组频道
    channels_by_group = defaultdict(list)
    for channel in channels:
        group = channel.group or "未分类"
        channels_by_group[group].append(channel)
    
    # 对每个分类内的频道按名称升序排序
    for group in channels_by_group:
        channels_by_group[group].sort(key=lambda x: x.name)
    
    # 从配置中获取频道类别顺序
    config_categories = get_config('channels.categories', {})
    config_group_order = list(config_categories.keys())
    
    # 按配置中的顺序排序分类，不在配置中的分类放在最后
    sorted_groups = []
    for group in config_group_order:
        if group in channels_by_group:
            sorted_groups.append(group)
    
    # 添加不在配置中的其他分组，按名称升序排序
    other_groups = [group for group in channels_by_group.keys() if group not in config_group_order]
    sorted_groups.extend(sorted(other_groups))
    
    lines = []
    
    # 生成TXT内容
    for group in sorted_groups:
        for channel in channels_by_group[group]:
            if channel.group:
                lines.append(f'{channel.name}{delimiter}{channel.url}{delimiter}{channel.group}')
            else:
                lines.append(f'{channel.name}{delimiter}{channel.url}')
    
    return '\n'.join(lines)

def generate_content(channels: List[ChannelInfo], format_type: str = 'm3u') -> str:
    """
    统一生成接口
    
    参数:
        channels: 频道信息列表
        format_type: 格式类型，可选值: 'm3u', 'txt'
        
    返回:
        对应格式的文本内容
    """
    if format_type == 'm3u':
        return generate_m3u_content(channels)
    elif format_type == 'txt':
        return generate_txt_content(channels)
    else:
        logger.error(f"不支持的格式类型: {format_type}")
        return ''

if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试M3U解析
    test_m3u = """#EXTM3U
#EXTINF:-1 tvg-id="CCTV1" tvg-name="CCTV1" tvg-logo="https://example.com/cctv1.png" group-title="央视",CCTV-1综合
http://example.com/cctv1.m3u8
#EXTINF:-1 tvg-id="CCTV2" tvg-name="CCTV2" group-title="央视",CCTV-2财经
http://example.com/cctv2.m3u8
"""
    
    print("测试M3U解析:")
    m3u_channels = parse_m3u_content(test_m3u)
    for channel in m3u_channels:
        print(f"  {channel}")
    
    # 测试TXT解析
    test_txt = """CCTV-1综合|http://example.com/cctv1.m3u8|央视
CCTV-2财经|http://example.com/cctv2.m3u8|央视
"""
    
    print("\n测试TXT解析:")
    txt_channels = parse_txt_content(test_txt)
    for channel in txt_channels:
        print(f"  {channel}")
    
    # 测试自动检测
    print("\n测试自动检测:")
    auto_m3u = parse_content(test_m3u)
    auto_txt = parse_content(test_txt)
    print(f"  M3U自动检测结果: {len(auto_m3u)}个频道")
    print(f"  TXT自动检测结果: {len(auto_txt)}个频道")
    
    # 测试生成M3U
    print("\n测试生成M3U:")
    generated_m3u = generate_m3u_content(m3u_channels)
    print(f"  生成的M3U内容: {generated_m3u[:200]}...")
    
    # 测试生成TXT
    print("\n测试生成TXT:")
    generated_txt = generate_txt_content(txt_channels)
    print(f"  生成的TXT内容: {generated_txt}")