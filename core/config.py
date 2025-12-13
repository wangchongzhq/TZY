#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
功能：提供配置文件加载、解析和访问功能
"""

import os
import json
import time
from typing import Dict, Any, Optional

from .logging_config import get_logger, log_exception, log_performance
from .file_utils import read_file, write_file, file_exists

# 获取日志记录器
logger = get_logger(__name__)

class ConfigManager:
    """
    配置管理器
    单例模式，用于统一加载和访问配置
    """
    _instance = None
    
    def __new__(cls, config_path: str = None):
        if cls._instance is None:
            # 使用绝对路径加载配置文件
            if config_path is None:
                # 获取当前文件所在目录的父目录（项目根目录）
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                config_path = os.path.join(project_root, "config", "config.json")
            cls._instance = super().__new__(cls)
            cls._instance._initialize(config_path)
        return cls._instance
    
    def _initialize(self, config_path: str):
        """
        初始化配置管理器
        
        参数:
            config_path: 配置文件路径
        """
        self._config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> bool:
        """
        加载配置文件
        
        返回:
            bool: 加载成功返回True，失败返回False
        """
        try:
            start_time = time.time()
            
            # 检查配置文件是否存在
            if not file_exists(self._config_path):
                logger.error(f"配置文件不存在: {self._config_path}")
                return False
            
            # 读取并解析配置文件
            file_content = read_file(self._config_path, encoding='utf-8-sig')
            if file_content is None:
                logger.error(f"读取配置文件失败: {self._config_path}")
                return False
            self._config = json.loads(file_content)
            
            elapsed_time = time.time() - start_time
            log_performance(logger, "加载配置文件", elapsed_time, file_path=self._config_path)
            logger.info(f"成功加载配置文件: {self._config_path}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {self._config_path} - {e}")
            log_exception(logger, "解析配置文件失败", e)
            return False
        except Exception as e:
            logger.error(f"加载配置文件失败: {self._config_path} - {e}")
            log_exception(logger, "加载配置文件失败", e)
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        支持点号分隔的嵌套键，如 "network.timeout"
        
        参数:
            key: 配置键，可以是嵌套键（如 "network.timeout"）
            default: 默认值，当键不存在时返回
            
        返回:
            Any: 配置值或默认值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            logger.debug(f"配置键不存在: {key}，使用默认值: {default}")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值
        支持点号分隔的嵌套键，如 "network.timeout"
        
        参数:
            key: 配置键，可以是嵌套键（如 "network.timeout"）
            value: 配置值
            
        返回:
            bool: 设置成功返回True，失败返回False
        """
        keys = key.split('.')
        config = self._config
        
        try:
            # 遍历到最后一个键的父级
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            logger.debug(f"设置配置: {key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"设置配置失败: {key} = {value} - {e}")
            log_exception(logger, "设置配置失败", e)
            return False
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        返回:
            bool: 保存成功返回True，失败返回False
        """
        try:
            start_time = time.time()
            
            # 确保配置文件目录存在
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            
            # 写入配置文件
            config_content = json.dumps(self._config, ensure_ascii=False, indent=2)
            if not write_file(self._config_path, config_content, encoding='utf-8-sig'):
                logger.error(f"写入配置文件失败: {self._config_path}")
                return False
            
            elapsed_time = time.time() - start_time
            log_performance(logger, "保存配置文件", elapsed_time, file_path=self._config_path)
            logger.info(f"成功保存配置文件: {self._config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {self._config_path} - {e}")
            log_exception(logger, "保存配置文件失败", e)
            return False
    
    def reload_config(self) -> bool:
        """
        重新加载配置文件
        
        返回:
            bool: 加载成功返回True，失败返回False
        """
        logger.info("重新加载配置文件...")
        return self.load_config()
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        返回:
            Dict[str, Any]: 所有配置
        """
        return self._config

# 创建全局配置管理器实例
config_manager = ConfigManager()

# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置值的便捷函数
    
    参数:
        key: 配置键
        default: 默认值
        
    返回:
        Any: 配置值
    """
    return config_manager.get(key, default)

def set_config(key: str, value: Any) -> bool:
    """
    设置配置值的便捷函数
    
    参数:
        key: 配置键
        value: 配置值
        
    返回:
        bool: 设置成功返回True
    """
    return config_manager.set(key, value)

def save_config() -> bool:
    """
    保存配置的便捷函数
    
    返回:
        bool: 保存成功返回True
    """
    return config_manager.save_config()

def reload_config() -> bool:
    """
    重新加载配置的便捷函数
    
    返回:
        bool: 加载成功返回True
    """
    return config_manager.reload_config()