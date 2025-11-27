#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非常简单的日志测试脚本
"""

import os
import time
import logging

# 直接打印当前工作目录
print(f"当前工作目录: {os.getcwd()}")

# 获取当前日期
today = time.strftime('%Y-%m-%d')
log_file = f'get_cgq_sources_{today}.log'
print(f"计划创建的日志文件: {log_file}")

# 测试1: 直接写入文件
print("\n测试1: 直接写入文件")
try:
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("=== 测试直接写入 ===\n")
        f.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"当前目录: {os.getcwd()}\n")
    print(f"✓ 直接写入成功")
    # 验证文件是否存在
    if os.path.exists(log_file):
        size = os.path.getsize(log_file)
        print(f"✓ 文件存在，大小: {size} 字节")
    else:
        print(f"✗ 文件不存在")
except Exception as e:
    print(f"✗ 直接写入失败: {e}")

# 测试2: 使用logging.basicConfig
print("\n测试2: 使用logging.basicConfig")
try:
    # 清除之前的handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=log_file,
        filemode='a',
        encoding='utf-8'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("这是一条测试信息")
    logger.warning("这是一条警告信息")
    print(f"✓ logging.basicConfig调用成功")
    
    # 验证文件是否存在且有内容
    if os.path.exists(log_file):
        size = os.path.getsize(log_file)
        print(f"✓ 文件存在，大小: {size} 字节")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"✓ 文件内容:")
            print(content)
    else:
        print(f"✗ 文件不存在")
except Exception as e:
    print(f"✗ logging.basicConfig失败: {e}")

print("\n测试完成")