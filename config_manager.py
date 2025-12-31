# -*- coding: utf-8 -*-
"""统一的配置管理模块"""

import json
import os
from typing import Dict, Any, Optional


class ConfigManager:
    """统一的配置管理器"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            base_dir: 基础目录路径，用于构建配置文件的绝对路径
        """
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.config_cache = {}
    
    def get_config_file_path(self, filename: str = "iptv_config.json") -> str:
        """
        获取配置文件的完整路径
        
        Args:
            filename: 配置文件名
            
        Returns:
            配置文件的完整路径
        """
        # 如果是相对路径且不在validator目录中，则使用基础目录
        if not os.path.isabs(filename) and 'validator' not in self.base_dir:
            return os.path.join(self.base_dir, filename)
        else:
            # 对于validator目录，使用上级目录
            return os.path.join(os.path.dirname(self.base_dir), filename)
    
    def load_config(self, filename: str = "iptv_config.json") -> Dict[str, Any]:
        """
        加载配置文件，支持缓存
        
        Args:
            filename: 配置文件名
            
        Returns:
            配置字典
        """
        config_path = self.get_config_file_path(filename)
        
        # 检查缓存
        if config_path in self.config_cache:
            return self.config_cache[config_path]
        
        try:
            if os.path.exists(config_path):
                from file_utils import read_json_with_encoding
                config = read_json_with_encoding(config_path) or {}
            else:
                config = {}
        except Exception:
            config = {}
        
        # 缓存配置
        self.config_cache[config_path] = config
        return config
    
    def get_validation_config(self, filename: str = "iptv_config.json") -> Dict[str, Any]:
        """
        获取验证相关的配置
        
        Args:
            filename: 配置文件名
            
        Returns:
            验证配置字典
        """
        config = self.load_config(filename)
        return config.get('validation', {})
    
    def get_timeout_config(self, filename: str = "iptv_config.json") -> int:
        """
        获取默认超时配置
        
        Args:
            filename: 配置文件名
            
        Returns:
            默认超时时间（秒）
        """
        validation_config = self.get_validation_config(filename)
        return validation_config.get('default_timeout', 5)
    
    def get_workers_config(self, filename: str = "iptv_config.json") -> Dict[str, int]:
        """
        获取工作线程配置
        
        Args:
            filename: 配置文件名
            
        Returns:
            工作线程配置字典
        """
        validation_config = self.get_validation_config(filename)
        return {
            'default_workers': validation_config.get('default_workers', 30),
            'max_workers_multiplier': validation_config.get('max_workers_multiplier', 4)
        }


# 全局配置管理器实例
_global_config_manager = None


def get_config_manager(base_dir: Optional[str] = None) -> ConfigManager:
    """
    获取全局配置管理器实例
    
    Args:
        base_dir: 基础目录路径
        
    Returns:
        配置管理器实例
    """
    global _global_config_manager
    if _global_config_manager is None or base_dir:
        _global_config_manager = ConfigManager(base_dir)
    return _global_config_manager


def load_app_config(filename: str = "iptv_config.json") -> Dict[str, Any]:
    """
    快速加载应用配置（向后兼容函数）
    
    Args:
        filename: 配置文件名
        
    Returns:
        应用配置字典
    """
    return get_config_manager().load_config(filename)


def get_validation_config(filename: str = "iptv_config.json") -> Dict[str, Any]:
    """
    快速获取验证配置（向后兼容函数）
    
    Args:
        filename: 配置文件名
        
    Returns:
        验证配置字典
    """
    return get_config_manager().get_validation_config(filename)