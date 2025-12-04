#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理系统单元测试
"""

import os
import sys
import unittest
from unittest.mock import patch, mock_open

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入要测试的模块
from core.config import get_config, ConfigManager


class TestConfigManager(unittest.TestCase):
    """配置管理系统测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.config_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'config.yaml')
        self.config_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'config.json')
        
    def test_get_config_basic(self):
        """测试基本的配置获取功能"""
        # 设置模拟返回值
        mock_config = {
            'logging': {
                'level': 'INFO',
                'max_bytes': 10485760
            },
            'network': {
                'timeout': 10
            }
        }
        
        # 测试获取特定部分的配置
        with patch('core.config.config_manager._config', mock_config):
            logging_config = get_config('logging')
            self.assertEqual(logging_config, mock_config['logging'])
        
        # 测试获取不存在的配置部分
        with patch('core.config.config_manager._config', mock_config):
            nonexistent_config = get_config('nonexistent')
            self.assertIsNone(nonexistent_config)
            
            # 测试获取配置项，并提供默认值
            level = get_config('logging.level', 'DEBUG')
            self.assertEqual(level, 'INFO')
            
            nonexistent_level = get_config('logging.nonexistent', 'DEFAULT')
            self.assertEqual(nonexistent_level, 'DEFAULT')
    
    def test_load_config_json(self):
        """测试加载JSON格式的配置文件"""
        # 创建一个临时的JSON配置文件用于测试
        json_config = '''
{
  "logging": {
    "level": "INFO",
    "max_bytes": 20971520,
    "backup_count": 3
  },
  "output": {
    "m3u_filename": "test.m3u",
    "txt_filename": "test.txt"
  }
}
'''
        
        with patch('builtins.open', mock_open(read_data=json_config)):
            with patch('os.path.exists', return_value=True):
                config_manager = ConfigManager("config/config.json")
                # 由于load_config是在初始化时调用的，我们需要手动重新加载
                with patch.object(config_manager, '_initialize'):
                    result = config_manager.load_config()
                    # 验证配置是否正确加载
                    self.assertTrue(result)
    
    def test_load_config_file_not_found(self):
        """测试配置文件不存在的情况"""
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager("config/config.json")
            # 由于load_config是在初始化时调用的，我们需要手动重新加载
            with patch.object(config_manager, '_initialize'):
                result = config_manager.load_config()
                self.assertFalse(result)
    
    def test_get_config_nested(self):
        """测试获取嵌套的配置项"""
        mock_config = {
            'a': {
                'b': {
                    'c': {
                        'd': 123
                    }
                }
            }
        }
        
        with patch('core.config.config_manager._config', mock_config):
            # 测试深度嵌套的配置获取
            value = get_config('a.b.c.d', 456)
            self.assertEqual(value, 123)
            
            # 测试中间层次不存在的情况
            value = get_config('a.b.x.y', 789)
            self.assertEqual(value, 789)


if __name__ == '__main__':
    unittest.main()
