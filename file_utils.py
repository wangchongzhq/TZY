#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file_utils.py

文件操作工具类
提供统一编码的文件读写操作和其他文件相关工具
"""

import os
import sys
import json
import tempfile
from typing import List, Dict, Optional, Tuple, Union

# 默认编码列表，按优先级排序
DEFAULT_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'latin1', 'iso-8859-1']

def read_file_with_encoding(file_path: str, encodings: Optional[List[str]] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    尝试使用多种编码读取文件
    
    Args:
        file_path: 文件路径
        encodings: 编码列表，如果为None则使用默认编码列表
        
    Returns:
        Tuple[Optional[str], Optional[str]]: (文件内容, 使用的编码)，如果读取失败则返回(None, None)
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None, None
    
    if not os.path.isfile(file_path):
        print(f"不是普通文件: {file_path}")
        return None, None
    
    encodings = encodings or DEFAULT_ENCODINGS
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content, encoding
        except UnicodeDecodeError:
            continue
        except (IOError, OSError) as e:
            print(f"读取文件失败: 文件操作错误 - {e}")
            continue
        except (ValueError, TypeError) as e:
            print(f"读取文件失败: 数据格式错误 - {e}")
            continue
        except Exception as e:
            print(f"读取文件失败: 未知错误 - {e}")
            continue
    
    return None, None

def write_file_with_encoding(file_path: str, content: str, encoding: str = 'utf-8', 
                           ensure_dir: bool = False) -> bool:
    """
    使用指定编码写入文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 编码格式，默认utf-8
        ensure_dir: 是否确保目录存在
        
    Returns:
        bool: 是否写入成功
    """
    if ensure_dir:
        output_dir = os.path.dirname(file_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                print(f"无法创建输出目录 '{output_dir}': {e}")
                return False
    
    try:
        # 如果需要使用UTF-8 BOM（Windows兼容）
        if encoding == 'utf-8-sig':
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                f.write(content)
        else:
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
        return True
    except (IOError, OSError) as e:
        print(f"写入文件失败: 文件操作错误 - {e}")
        return False
    except (ValueError, TypeError) as e:
        print(f"写入文件失败: 数据格式错误 - {e}")
        return False
    except Exception as e:
        print(f"写入文件失败: 未知错误 - {e}")
        return False

def safe_filename(filename: str) -> str:
    """
    生成安全的文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 安全的文件名
    """
    # 移除或替换不安全字符
    unsafe_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\n', '\r', '\t']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # 限制长度
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename

def ensure_directory_exists(directory: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
        
    Returns:
        bool: 是否成功创建或目录已存在
    """
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except OSError as e:
            print(f"无法创建目录 '{directory}': {e}")
            return False
    elif not os.path.isdir(directory):
        print(f"路径不是目录: {directory}")
        return False
    else:
        return True

def validate_file_path(file_path: str) -> bool:
    """
    验证文件路径的安全性
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 路径是否安全
    """
    if not file_path:
        return False
    
    # 检查路径长度
    if len(file_path) > 255:
        raise ValueError(f"文件路径过长: {file_path}")
    
    # 检查是否包含危险字符
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        if char in file_path:
            raise ValueError(f"文件路径包含危险字符 '{char}': {file_path}")
    
    # 检查是否尝试访问上级目录
    if '..' in file_path:
        raise ValueError(f"文件路径包含上级目录访问: {file_path}")
    
    return True

def read_json_with_encoding(file_path: str, encodings: Optional[List[str]] = None) -> Optional[Dict]:
    """
    使用指定编码读取JSON文件
    
    Args:
        file_path: 文件路径
        encodings: 编码列表，如果为None则使用默认编码列表
        
    Returns:
        Dict or None: JSON数据或None（如果读取失败）
    """
    content, encoding = read_file_with_encoding(file_path, encodings)
    if content is None:
        return None
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return None
    except Exception as e:
        print(f"读取JSON文件失败: {e}")
        return None

def write_json_with_encoding(file_path: str, data: Dict, ensure_dir: bool = False, 
                           encoding: str = 'utf-8', indent: int = 2) -> bool:
    """
    使用指定编码写入JSON文件
    
    Args:
        file_path: 文件路径
        data: 要写入的JSON数据
        ensure_dir: 是否确保目录存在
        encoding: 编码格式，默认utf-8
        indent: JSON缩进，默认2
        
    Returns:
        bool: 是否写入成功
    """
    if ensure_dir:
        output_dir = os.path.dirname(file_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                print(f"无法创建输出目录 '{output_dir}': {e}")
                return False
    
    try:
        content = json.dumps(data, ensure_ascii=False, indent=indent)
        return write_file_with_encoding(file_path, content, encoding)
    except Exception as e:
        print(f"写入JSON文件失败: {e}")
        return False

def create_temp_file(content: str, suffix: str = '.txt', prefix: str = 'iptv_', 
                   encoding: str = 'utf-8', delete: bool = False) -> Optional[str]:
    """
    创建临时文件
    
    Args:
        content: 文件内容
        suffix: 文件后缀
        prefix: 文件前缀
        encoding: 编码格式
        delete: 是否删除文件（仅返回文件名，保留文件）
        
    Returns:
        str or None: 临时文件路径或None（如果创建失败）
    """
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, prefix=prefix, 
                                       delete=delete, encoding=encoding) as f:
            f.write(content)
            return f.name
    except Exception as e:
        print(f"创建临时文件失败: {e}")
        return None

def get_safe_temp_dir() -> Optional[str]:
    """
    获取安全的临时目录
    
    Returns:
        str or None: 临时目录路径或None（如果创建失败）
    """
    try:
        temp_dir = tempfile.gettempdir()
        safe_dir = os.path.join(temp_dir, 'iptv_temp')
        if not os.path.exists(safe_dir):
            os.makedirs(safe_dir)
        return safe_dir
    except Exception as e:
        print(f"获取临时目录失败: {e}")
        return None