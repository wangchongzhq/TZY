#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试IP-TV.py的文件生成功能
"""

import os
import sys
import logging
import importlib.util

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入需要的模块
from core.config import get_config
from core.file_utils import write_file

# 从IP-TV.py导入generate_m3u_file和generate_txt_file函数
# 使用importlib因为文件名包含连字符
spec = importlib.util.spec_from_file_location("iptv", "IP-TV.py")
iptv = importlib.util.module_from_spec(spec)
sys.modules["iptv"] = iptv
spec.loader.exec_module(iptv)

# 获取需要的函数
generate_m3u_file = iptv.generate_m3u_file
generate_txt_file = iptv.generate_txt_file

def main():
    logger.info("开始测试IP-TV.py的文件生成功能")
    
    # 检查配置
    output_config = get_config('output', {})
    logger.info(f"Output配置: {output_config}")
    
    # 创建测试频道数据
    test_channels = {
        "央视频道": [
            ("CCTV-1", "http://example.com/cctv1"),
            ("CCTV-2", "http://example.com/cctv2")
        ],
        "卫视频道": [
            ("湖南卫视", "http://example.com/hunan"),
            ("浙江卫视", "http://example.com/zhejiang")
        ]
    }
    
    # 测试文件生成
    logger.info("\n测试M3U文件生成...")
    m3u_path = output_config.get('m3u_file', 'output/iptv.m3u')
    success = generate_m3u_file(test_channels, m3u_path)
    logger.info(f"M3U文件生成{'成功' if success else '失败'}")
    
    logger.info("\n测试TXT文件生成...")
    txt_path = output_config.get('txt_file', 'output/channels.txt')
    success = generate_txt_file(test_channels, txt_path)
    logger.info(f"TXT文件生成{'成功' if success else '失败'}")
    
    # 检查文件是否生成在正确位置
    logger.info("\n检查文件位置...")
    if os.path.exists(m3u_path):
        logger.info(f"✅ M3U文件生成在正确位置: {os.path.abspath(m3u_path)}")
    else:
        logger.error(f"❌ M3U文件未找到: {os.path.abspath(m3u_path)}")
    
    if os.path.exists(txt_path):
        logger.info(f"✅ TXT文件生成在正确位置: {os.path.abspath(txt_path)}")
    else:
        logger.error(f"❌ TXT文件未找到: {os.path.abspath(txt_path)}")
    
    # 检查主目录是否有意外生成的文件
    logger.info("\n检查主目录是否有意外生成的文件...")
    main_dir_files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith(('.m3u', '.txt')) and f not in ['test_file_generation.py', 'test_ip_tv_file_generation.py']]
    if main_dir_files:
        logger.warning(f"⚠️  主目录中发现意外文件: {main_dir_files}")
    else:
        logger.info("✅ 主目录中没有意外生成的文件")
    
    logger.info("\n测试完成")

if __name__ == "__main__":
    main()
