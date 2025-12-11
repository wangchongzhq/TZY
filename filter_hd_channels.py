#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用高清线路分层筛选方法到整个频道库
功能：使用新的分层筛选方法筛选出所有高清线路，生成新的频道列表
"""

import time
import logging
from typing import List, Dict

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入频道处理工具
from core.channel_utils import get_video_resolution, should_exclude_resolution

# 导入配置管理器
from core.config import get_config

# 获取本地源开关设置
local_sources_enabled = get_config('local_sources.enabled', True)
local_sources_files = get_config('local_sources.files', [])


def load_channels(file_path: str) -> List[Dict[str, str]]:
    """
    加载频道文件
    参数:
        file_path: 频道文件路径
    返回:
        List[Dict[str, str]]: 频道列表，每个频道包含名称和URL
    """
    # 检查本地源开关
    if not local_sources_enabled:
        logger.error("本地源功能已关闭，无法加载本地频道文件")
        return []
    
    # 检查文件是否在允许的本地源列表中
    file_name = file_path.split('\\')[-1] if '\\' in file_path else file_path
    if file_name not in local_sources_files:
        logger.error(f"文件 '{file_name}' 不在允许的本地源列表中，无法加载")
        return []
    
    channels = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '#genre#' in line:
                    continue
                # 格式: 频道名称,URL
                if ',' in line:
                    name, url = line.split(',', 1)
                    channels.append({
                        'name': name.strip(),
                        'url': url.strip()
                    })
        logger.info(f"成功加载 {len(channels)} 个频道")
    except Exception as e:
        logger.error(f"加载频道文件失败: {e}")
    return channels


def filter_hd_channels(channels: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    筛选高清频道
    参数:
        channels: 原始频道列表
    返回:
        List[Dict[str, str]]: 高清频道列表
    """
    hd_channels = []
    total = len(channels)
    processed = 0
    
    start_time = time.time()
    
    for channel in channels:
        processed += 1
        
        # 打印进度
        if processed % 100 == 0 or processed == total:
            elapsed_time = time.time() - start_time
            logger.info(f"处理进度: {processed}/{total} ({processed/total*100:.1f}%) - 已筛选出 {len(hd_channels)} 个高清频道 - 耗时: {elapsed_time:.2f} 秒")
        
        try:
            # 使用新的分层筛选方法判断是否为高清
            # 如果不应该排除（即满足最小分辨率要求），则添加到高清频道列表
            if not should_exclude_resolution(channel['url'], min_resolution='1920x1080'):
                # 获取实际分辨率（用于日志记录）
                resolution = get_video_resolution(channel['url'], timeout=3)
                if resolution:
                    logger.debug(f"高清频道: {channel['name']} - 分辨率: {resolution[0]}x{resolution[1]} - URL: {channel['url']}")
                else:
                    logger.debug(f"高清频道: {channel['name']} - 分辨率: 未知（但通过筛选） - URL: {channel['url']}")
                hd_channels.append(channel)
        except Exception as e:
            logger.error(f"处理频道 {channel['name']} 失败: {e}")
            continue
    
    end_time = time.time()
    logger.info(f"筛选完成，共处理 {total} 个频道，得到 {len(hd_channels)} 个高清频道，耗时: {end_time - start_time:.2f} 秒")
    
    return hd_channels


def save_hd_channels(hd_channels: List[Dict[str, str]], output_file: str) -> bool:
    """
    保存高清频道到文件
    参数:
        hd_channels: 高清频道列表
        output_file: 输出文件路径
    返回:
        bool: 保存是否成功
    """
    try:
        with open(output_file, 'w', encoding='utf-8-sig') as f:
            # 写入文件头
            f.write("# 高清频道列表\n")
            f.write(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 频道总数: {len(hd_channels)}\n")
            f.write("\n")
            
            # 写入频道数据
            for channel in hd_channels:
                f.write(f"{channel['name']},{channel['url']}\n")
        
        logger.info(f"成功保存 {len(hd_channels)} 个高清频道到 {output_file}")
        return True
    except Exception as e:
        logger.error(f"保存高清频道失败: {e}")
        return False


def main():
    """
    主函数
    """
    # 加载原始频道文件
    input_file = 'ipzyauto.txt'
    channels = load_channels(input_file)
    
    if not channels:
        logger.error("没有加载到频道")
        return
    
    # 筛选高清频道
    hd_channels = filter_hd_channels(channels)
    
    if not hd_channels:
        logger.error("没有筛选出高清频道")
        return
    
    # 保存高清频道
    output_file = 'hd_channels.txt'
    if save_hd_channels(hd_channels, output_file):
        logger.info("高清频道筛选完成")
    else:
        logger.error("高清频道筛选失败")


if __name__ == "__main__":
    main()