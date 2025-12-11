#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_and_convert.py

合并iptv_i4.m3u和iptv_i6.m3u文件，并转换为TXT格式
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from core.logging_config import setup_logging, get_logger, log_exception
from core.file_utils import read_file, write_file
from core.parser import parse_m3u_content
from core.channel_utils import group_channels, sort_channels, get_channel_statistics
from core.chinese_conversion import simplify_chinese
from core.config import get_config
# 使用importlib导入带连字符的模块
import importlib.util

spec = importlib.util.spec_from_file_location("ip_tv", "IP-TV.py")
ip_tv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ip_tv)

# 设置日志
setup_logging()
logger = get_logger(__name__)


def apply_channel_alias(channel_name):
    """应用频道别名映射，将频道名转换为通用名称
    
    Args:
        channel_name (str): 原始频道名称
        
    Returns:
        str: 应用别名映射后的通用频道名称
    """
    # 使用ip_tv模块中的normalize_channel_name函数
    normalized_name = ip_tv.normalize_channel_name(channel_name)
    return normalized_name if normalized_name else channel_name  # 如果无法规范化，返回原始名称


def get_config_group_order():
    """
    获取配置中的分组顺序
    """
    categories = get_config("channels.categories", {})
    return list(categories.keys())


def sort_groups_by_config_order(grouped_channels):
    """
    按照配置中的顺序对分组进行排序
    """
    config_order = get_config_group_order()
    sorted_groups = []
    
    # 先添加配置中定义的分组
    for group_name in config_order:
        if group_name in grouped_channels and grouped_channels[group_name]:
            sorted_groups.append((group_name, grouped_channels[group_name]))
    
    # 然后添加其他分组（按字母顺序）
    other_groups = [g for g in sorted(grouped_channels.keys()) 
                   if g not in config_order and grouped_channels[g]]
    
    for group_name in other_groups:
        sorted_groups.append((group_name, grouped_channels[group_name]))
    
    return sorted_groups

def merge_m3u_files(file1, file2, output_file):
    """合并两个M3U文件"""
    try:
        # 检查文件是否存在
        if not os.path.exists(file1):
            logger.error(f"文件不存在: {file1}")
            return False
        if not os.path.exists(file2):
            logger.error(f"文件不存在: {file2}")
            return False
        
        # 读取两个文件的内容
        content1 = read_file(file1)
        content2 = read_file(file2)
        
        if content1 is None:
            logger.error(f"无法读取文件: {file1}")
            return False
        if content2 is None:
            logger.error(f"无法读取文件: {file2}")
            return False
        
        # 分离文件头和频道内容
        lines1 = content1.strip().split('\n')
        lines2 = content2.strip().split('\n')
        
        # 确保合并后的文件只有一个文件头
        header = None
        channels = []
        
        # 处理第一个文件
        for line in lines1:
            if line.startswith('#EXTM3U'):
                if not header:
                    header = line
            elif line.strip():
                channels.append(line)
        
        # 处理第二个文件，跳过文件头
        for line in lines2:
            if not line.startswith('#EXTM3U') and line.strip():
                channels.append(line)
        
        # 确保有头部
        if not header:
            header = '#EXTM3U tvg-url="https://diyp020.112114.xyz"'
        
        # 合并内容
        merged_content = header + '\n' + '\n'.join(channels)
        
        # 写入合并后的文件
        return write_file(output_file, merged_content, encoding='utf-8-sig')
        
    except Exception as e:
        logger.error(f"合并文件失败: {str(e)}")
        return False

def convert_m3u_content_to_txt(content, output_file, source_file_name):
    """将M3U内容转换为TXT格式"""
    try:
        # 处理BOM（字节顺序标记）
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # 预处理内容，确保#EXTM3U头部被正确识别
        content = content.strip()
        if not content.startswith('#EXTM3U'):
            # 尝试查找#EXTM3U头部
            lines = content.split('\n')
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if line_stripped.startswith('#EXTM3U'):
                    # 重新组织内容，将头部放在第一行
                    new_lines = [line] + lines[:i] + lines[i+1:]
                    content = '\n'.join(new_lines)
                    break
        
        # 解析M3U内容
        channels = parse_m3u_content(content)
        
        if not channels:
            return False
        
        # 应用频道别名映射和简繁体转换
        processed_channels = []
        for channel in channels:
            # 转换频道名和分组名为简体中文
            channel.name = simplify_chinese(channel.name)
            channel.group = simplify_chinese(channel.group)
            
            # 应用频道别名
            channel.name = apply_channel_alias(channel.name)
            
            processed_channels.append(channel)
        
        # 分组频道
        grouped_channels = group_channels(processed_channels)
        
        # 统计信息
        stats = get_channel_statistics(processed_channels)
        total_groups = len([g for g in grouped_channels if grouped_channels[g]])
        total_sources = stats['total_channels']
        
        # 生成输出内容
        output_lines = []
        
        # 添加文件头信息
        output_lines.append(f"# M3U Conversion Result - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"# Source File: {source_file_name}")
        output_lines.append(f"# Groups: {total_groups}, Total Sources: {total_sources}")
        output_lines.append("")
        
        # 按照配置顺序排序分组
        sorted_groups = sort_groups_by_config_order(grouped_channels)
        
        # 添加频道信息
        for group, group_channels_list in sorted_groups:
            if group_channels_list:  # 只写入有频道的分组
                if group:  # 只有当分组名称非空时才写入分组标题
                    output_lines.append(f"{group},#genre#")
                # 写入该分组下的所有频道URL
                for channel in group_channels_list:
                    line = f"{channel.name},{channel.url}"
                    output_lines.append(line)
                # 分组之间空一行
                output_lines.append("")
        
        # 写入TXT文件
        content_to_write = '\n'.join(output_lines)
        return write_file(output_file, content_to_write, encoding='utf-8-sig')
            
    except Exception as e:
        logger.error(f"转换失败: {str(e)}")
        log_exception(logger, "转换失败")
        return False

def main():
    """主函数"""
    # 定义文件路径
    output_dir = "output"
    iptv_i4 = os.path.join(output_dir, "ip-tv_i4.m3u")
    iptv_i6 = os.path.join(output_dir, "ip-tv_i6.m3u")
    # 使用新的文件名作为主要输出
    merged_m3u = os.path.join(output_dir, "ip-tv_merged.m3u")
    merged_txt = os.path.join(output_dir, "ip-tv_merged.txt")
    # 兼容旧的文件名
    old_merged_m3u = os.path.join(output_dir, "jieguo_merged.m3u")
    old_merged_txt = os.path.join(output_dir, "jieguo_merged.txt")
    
    logger.info(f"开始合并文件: {iptv_i4} 和 {iptv_i6}")
    
    # 合并M3U文件
    if not merge_m3u_files(iptv_i4, iptv_i6, merged_m3u):
        logger.error("合并M3U文件失败")
        sys.exit(1)
    
    logger.info(f"合并成功，生成: {merged_m3u}")
    
    # 转换为TXT格式
    logger.info(f"开始转换为TXT格式: {merged_txt}")
    
    # 直接读取合并后的M3U内容并转换
    content = read_file(merged_m3u)
    if content is None:
        logger.error(f"无法读取文件: {merged_m3u}")
        sys.exit(1)
    
    if not convert_m3u_content_to_txt(content, merged_txt, os.path.basename(merged_m3u)):
        logger.error("转换为TXT格式失败")
        sys.exit(1)
    
    logger.info(f"转换成功，生成: {merged_txt}")
    
    # 生成兼容旧文件名的版本
    if merged_m3u != old_merged_m3u:
        write_file(old_merged_m3u, content, encoding='utf-8-sig')
        logger.info(f"同时生成兼容版本: {old_merged_m3u}")
    
    txt_content = read_file(merged_txt)
    if txt_content is not None and merged_txt != old_merged_txt:
        write_file(old_merged_txt, txt_content, encoding='utf-8-sig')
        logger.info(f"同时生成兼容版本: {old_merged_txt}")
    
    logger.info("所有操作完成")

if __name__ == "__main__":
    main()