# -*- coding: utf-8 -*-
import os
import sys
import logging
from IP-TV import update_iptv_sources

# 设置日志级别为DEBUG，查看详细信息
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 运行前清理旧文件
if os.path.exists('output/iptv.m3u'):
    os.remove('output/iptv.m3u')
    logger.info('已删除output目录下的旧iptv.m3u文件')

# 运行update_iptv_sources函数
logger.info('开始运行update_iptv_sources函数')
update_iptv_sources()

# 检查文件生成情况
logger.info('\n=== 文件生成结果检查 ===')
if os.path.exists('output/iptv.m3u'):
    logger.info(f'output目录下存在iptv.m3u文件，大小: {os.path.getsize("output/iptv.m3u")} 字节')
else:
    logger.info('output目录下不存在iptv.m3u文件')
