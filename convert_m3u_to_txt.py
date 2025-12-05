#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_m3u_to_txt.py

将M3U格式的直播源转换为TXT格式的直播源
"""

import re
import os
import sys
from datetime import datetime

# 导入核心模块
from core.config import get_config
from core.logging_config import setup_logging, get_logger, log_exception
from core.file_utils import read_file, write_file
from core.parser import parse_m3u_content
from core.channel_utils import group_channels, get_channel_statistics

# 设置日志
setup_logging()
logger = get_logger(__name__)

class M3UConverter:
    """M3U文件转换器类"""
    
    def __init__(self):
        """初始化M3U转换器"""
        pass
    
    def convert_m3u_to_txt(self, m3u_file_path, txt_file_path):
        """将M3U文件转换为TXT格式"""
        try:
            # 检查文件是否存在和为空
            if not os.path.exists(m3u_file_path) or os.path.getsize(m3u_file_path) == 0:
                return False
            
            # 读取文件内容
            content = read_file(m3u_file_path)
            if content is None:
                return False
            
            # 解析M3U内容
            channels = parse_m3u_content(content)
            
            if not channels:
                return False
            
            # 分组频道
            grouped_channels = group_channels(channels)
            
            # 统计信息
            stats = get_channel_statistics(channels)
            total_groups = len([g for g in grouped_channels if grouped_channels[g]])
            total_sources = stats['total_channels']
            
            # 生成输出内容
            output_lines = []
            
            # 添加文件头信息
            output_lines.append(f"# M3U Conversion Result - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            output_lines.append(f"# Source File: {os.path.basename(m3u_file_path)}")
            output_lines.append(f"# Groups: {total_groups}, Total Sources: {total_sources}")
            output_lines.append("")
            
            # 添加频道信息
            for group, group_channels_list in sorted(grouped_channels.items()):
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
            return write_file(txt_file_path, content_to_write, encoding='utf-8-sig')
                
        except Exception as e:
            logger.error(f"转换失败: {str(e)}")
            log_exception(logger, "转换失败")
            return False
    


def main():
    """主函数"""
    # 创建转换器实例
    converter = M3UConverter()
    
    # 尝试找到M3U文件
    possible_m3u_files = ["iptv.m3u", "cn.m3u", "4K.m3u", "jieguo.m3u"]
    m3u_file = None
    txt_file = "m3utotxt output.txt"
    
    # 检查命令行参数
    if len(sys.argv) == 3:
        m3u_file = sys.argv[1]
        txt_file = sys.argv[2]
    else:
        # 获取当前目录下所有M3U文件（包括.m3u、.m3a和无扩展名的文件）
        all_m3u_files = [f for f in os.listdir('.') if f.lower().endswith(('.m3u', '.m3a')) or f in possible_m3u_files]
        
        if all_m3u_files:
            # 检查每个文件是否为空
            valid_m3u_files = [f for f in all_m3u_files if os.path.getsize(f) > 0]
            
            if valid_m3u_files:
                # 选择第一个有效文件
                m3u_file = valid_m3u_files[0]
    
    if not m3u_file:
        logger.error("未找到有效的M3U文件")
        sys.exit(1)
    
    # 根据输入文件自动生成输出文件名
    if m3u_file:
        txt_file = f"{os.path.splitext(m3u_file)[0]}.txt"
    else:
        txt_file = "output.txt"
    
    # 执行转换
    success = converter.convert_m3u_to_txt(m3u_file, txt_file)
    
    if not success:
        logger.error(f"转换失败: {m3u_file} -> {txt_file}")
        sys.exit(1)
    else:
        logger.info(f"转换成功: {m3u_file} -> {txt_file}")

if __name__ == "__main__":
    main()
