#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core模块初始化文件
功能：导出core模块的主要功能和类，提供便捷的导入接口
"""

__version__ = "1.0.0"

# 导出配置管理相关功能
from .config import ConfigManager, get_config, set_config, save_config, reload_config

# 导出日志配置相关功能
from .logging_config import setup_logging, get_logger, log_exception, log_performance

# 导出网络请求相关功能
from .network import (
    fetch_content, 
    fetch_multiple,
    fetch_multiple_async,
    async_fetch_content,
    async_fetch_multiple,
    check_url_availability, 
    is_streaming_url,
    clear_cache
)

# 导出文件处理相关功能
from .file_utils import read_file, write_file, delete_file, copy_file, move_file, file_exists, get_file_size

# 导出频道处理相关功能
from .channel_utils import (
    generate_channel_hash,
    deduplicate_channels,
    filter_channels,
    evaluate_channel_quality,
    batch_evaluate_quality,
    get_channel_statistics,
    search_channels,
    normalize_channel_name,
    get_channel_category
)

# 导出解析相关功能
from .parser import ChannelInfo, parse_m3u_content

# 导出中文转换相关功能
from .chinese_conversion import simplify_chinese, traditionalize_chinese, add_traditional_aliases

__all__ = [
    # 配置管理
    'ConfigManager',
    'get_config',
    'set_config',
    'save_config',
    'reload_config',
    
    # 日志配置
    'setup_logging',
    'get_logger',
    'log_exception',
    'log_performance',
    
    # 网络请求
    'fetch_content',
    'fetch_multiple',
    'fetch_multiple_async',
    'async_fetch_content',
    'async_fetch_multiple',
    'check_url_availability',
    'is_streaming_url',
    'clear_cache',
    
    # 文件处理
    'read_file',
    'write_file',
    'delete_file',
    'copy_file',
    'move_file',
    'file_exists',
    'get_file_size',
    
    # 频道处理
    'generate_channel_hash',
    'deduplicate_channels',
    'filter_channels',
    'evaluate_channel_quality',
    'batch_evaluate_quality',
    'get_channel_statistics',
    'search_channels',
    'normalize_channel_name',
    'get_channel_category',
    
    # 解析
    'ChannelInfo',
    'parse_m3u_content',
    
    # 中文转换
    'simplify_chinese',
    'traditionalize_chinese',
    'add_traditional_aliases',
]
