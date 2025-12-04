#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块
功能：提供统一的日志配置和管理功能
"""

import logging
import logging.handlers
import os
import sys
from typing import Dict, Any

# 延迟导入配置管理以避免循环导入
# from .config import get_config

# 日志级别映射
LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# 统一的日志格式
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 详细的日志格式（用于文件）
DETAILED_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'

def setup_logging(
    log_level: str = None,
    log_file: str = None,
    max_bytes: int = None,
    backup_count: int = None,
    console_output: bool = True
) -> None:
    """
    配置全局日志系统
    
    参数:
        log_level: 日志级别，可选值: DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_file: 日志文件路径，如果为None则只输出到控制台
        max_bytes: 日志文件最大字节数（日志轮转）
        backup_count: 保留的备份日志文件数量
        console_output: 是否输出到控制台
    """
    # 从配置获取默认值
    from .config import get_config
    logging_config = get_config('logging', {})
    
    # 使用配置值或默认值
    if log_level is None:
        log_level = logging_config.get('level', 'INFO')
    if log_file is None:
        log_file = logging_config.get('file_path', None)
    if max_bytes is None:
        max_bytes = logging_config.get('max_bytes', 10 * 1024 * 1024)  # 默认10MB
    if backup_count is None:
        backup_count = logging_config.get('backup_count', 3)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL_MAP.get(log_level.upper(), logging.INFO))
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(LOG_FORMAT)
    detailed_formatter = logging.Formatter(DETAILED_LOG_FORMAT)
    
    # 添加控制台处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOG_LEVEL_MAP.get(log_level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 添加文件处理器（带轮转功能）
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception as e:
                print(f"创建日志目录失败: {e}")
                return
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别的日志
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

def get_logger(name: str = None) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    参数:
        name: 日志记录器名称，如果为None则返回根日志记录器
        
    返回:
        日志记录器实例
    """
    return logging.getLogger(name)

def log_exception(logger: logging.Logger, message: str, exc_info: bool = True) -> None:
    """
    记录异常信息
    
    参数:
        logger: 日志记录器实例
        message: 错误消息
        exc_info: 是否包含异常堆栈信息
    """
    logger.error(message, exc_info=exc_info)

def log_performance(logger: logging.Logger, operation: str, elapsed_time: float, **kwargs) -> None:
    """
    记录性能信息
    
    参数:
        logger: 日志记录器实例
        operation: 操作名称
        elapsed_time: 耗时（秒）
        **kwargs: 其他性能相关参数
    """
    extra_info = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"性能统计 - {operation} 耗时: {elapsed_time:.4f}秒 {extra_info}")

if __name__ == "__main__":
    # 测试日志配置
    setup_logging(log_level='DEBUG', log_file='test.log', console_output=True)
    
    logger = get_logger(__name__)
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    
    try:
        1 / 0
    except Exception as e:
        log_exception(logger, "发生异常")
    
    import time
    start_time = time.time()
    time.sleep(0.1)
    elapsed_time = time.time() - start_time
    log_performance(logger, "测试操作", elapsed_time, test_param=123)
