#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：手动触发tvzy.py中的文件生成功能

这个脚本可以在修改tvzy.py后手动运行，立即生成tzydauto.txt文件，
而不需要等待定时任务（每天凌晨3点）执行。
"""

import sys
import os
import logging
import time
from datetime import datetime

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler("test_tvzy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """主函数：导入并执行tvzy.py中的main函数"""
    try:
        start_time = time.time()
        logger.info("开始手动触发tvzy.py文件生成功能...")
        logger.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 导入tvzy模块
        import tvzy
        
        # 执行tvzy中的main函数
        logger.info("执行tvzy.main()函数...")
        tvzy.main()
        
        # 检查生成的文件是否存在
        output_file = os.path.join(os.getcwd(), "tzydauto.txt")
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / 1024  # KB
            logger.info(f"文件生成成功！文件路径: {output_file}")
            logger.info(f"文件大小: {file_size:.2f} KB")
        else:
            logger.error(f"文件生成失败，未找到文件: {output_file}")
        
        end_time = time.time()
        logger.info(f"任务完成，总耗时: {end_time - start_time:.2f} 秒")
        
    except ImportError as e:
        logger.error(f"导入tvzy模块失败: {str(e)}")
        logger.error("请确保tvzy.py文件在当前目录下")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行过程中出错: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    logger.info("==================================")
    logger.info("tvzy文件生成测试脚本启动")
    logger.info("==================================")
    main()
    logger.info("==================================")
    logger.info("测试脚本执行完毕")
    logger.info("==================================")
