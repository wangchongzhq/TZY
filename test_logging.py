#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日志功能的简单脚本
"""

import time
import logging

# 测试日志配置
today = time.strftime('%Y-%m-%d')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'test_log_{today}.log', encoding='utf-8', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

print("开始测试日志功能...")
logger.info("这是一条测试信息")
logger.warning("这是一条警告信息")
logger.error("这是一条错误信息")

# 测试写入文件
print("测试直接写入文件...")
try:
    with open('direct_write_test.txt', 'w', encoding='utf-8') as f:
        f.write("直接写入测试内容\n")
    print("直接写入成功")
except Exception as e:
    print(f"直接写入失败: {e}")

print("测试完成")