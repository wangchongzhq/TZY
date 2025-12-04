#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块单元测试
"""

import os
import sys
import unittest
import logging
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入要测试的模块
from core.logging_config import setup_logging, get_logger, log_exception
from core.config import get_config


class TestLoggingConfig(unittest.TestCase):
    """日志配置模块测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 清除之前的日志配置
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            handler.close()
        logging.root.setLevel(logging.NOTSET)
    
    @patch('core.config.get_config')
    def test_setup_logging_with_config(self, mock_get_config):
        """测试使用配置管理系统设置日志"""
        # 设置模拟的配置返回值
        mock_get_config.side_effect = lambda section, default=None: {
            'logging': {
                'level': 'DEBUG',
                'file_path': 'logs/test.log',
                'max_bytes': 1048576,
                'backup_count': 3
            }
        }.get(section, default)
        
        # 调用setup_logging
        setup_logging()
        
        # 验证根日志级别是否正确设置
        self.assertEqual(logging.root.level, logging.DEBUG)
        
        # 验证是否添加了FileHandler
        file_handlers = [h for h in logging.root.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        self.assertTrue(len(file_handlers) > 0)
        
        # 验证FileHandler的配置
        file_handler = file_handlers[0]
        self.assertEqual(file_handler.maxBytes, 1048576)
        self.assertEqual(file_handler.backupCount, 3)
    
    @patch('core.config.get_config')
    def test_setup_logging_with_defaults(self, mock_get_config):
        """测试使用默认值设置日志"""
        # 设置模拟的配置返回值为空，这样会使用默认值
        mock_get_config.side_effect = lambda section, default=None: {
            'logging': {
                'file_path': 'logs/test.log'
            }
        }.get(section, default)
        
        # 调用setup_logging
        setup_logging()
        
        # 验证根日志级别是否使用默认值
        self.assertEqual(logging.root.level, logging.INFO)
        
        # 验证是否添加了FileHandler
        file_handlers = [h for h in logging.root.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        self.assertTrue(len(file_handlers) > 0)
    
    def test_get_logger(self):
        """测试获取日志记录器"""
        # 设置日志
        setup_logging()
        
        # 获取日志记录器
        logger = get_logger('test_module')
        
        # 验证日志记录器是否正确创建
        self.assertEqual(logger.name, 'test_module')
        self.assertIsInstance(logger, logging.Logger)
    
    def test_log_exception(self):
        """测试异常日志记录"""
        # 设置日志，使用MemoryHandler以便测试
        setup_logging()
        
        # 创建一个MemoryHandler来捕获日志输出
        from io import StringIO
        import logging.handlers
        
        log_capture_string = StringIO()
        ch = logging.StreamHandler(log_capture_string)
        ch.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logging.root.addHandler(ch)
        
        # 测试记录异常
        logger = get_logger("test_module")
        try:
            raise ValueError("测试异常")
        except Exception as e:
            log_exception(logger, "发生异常")
        
        # 获取捕获的日志
        log_contents = log_capture_string.getvalue()
        
        # 验证日志中是否包含异常信息
        self.assertIn("ERROR", log_contents)
        self.assertIn("test_module", log_contents)
        self.assertIn("ValueError", log_contents)
        self.assertIn("测试异常", log_contents)
        
        # 清理
        log_capture_string.close()


if __name__ == '__main__':
    unittest.main()
