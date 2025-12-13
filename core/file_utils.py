#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理工具模块
功能：提供安全、高效的文件操作功能
"""

import os
import shutil
import time
from typing import Optional, List, Dict, Any

# 导入日志配置
from .logging_config import get_logger, log_exception, log_performance

# 获取日志记录器
logger = get_logger(__name__)

def read_file(file_path: str, encoding: str = 'utf-8', errors: str = 'strict') -> Optional[str]:
    """
    安全读取文件内容
    
    参数:
        file_path: 文件路径
        encoding: 文件编码，默认为utf-8
        errors: 编码错误处理方式，默认为strict
        
    返回:
        文件内容，如果文件不存在或读取失败则返回None
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
            
        if not os.path.isfile(file_path):
            logger.error(f"路径不是文件: {file_path}")
            return None
            
        start_time = time.time()
        with open(file_path, 'r', encoding=encoding, errors=errors) as f:
            content = f.read()
            
        elapsed_time = time.time() - start_time
        logger.debug(f"成功读取文件 {file_path}，大小: {len(content)}字符，耗时: {elapsed_time:.2f}秒")
        log_performance(logger, "读取文件", elapsed_time, file_path=file_path, size=len(content))
        return content
        
    except UnicodeDecodeError as e:
        logger.error(f"文件编码错误 {file_path}: {e}")
        # 尝试使用其他编码
        try_encodings = ['gbk', 'gb2312', 'latin-1']
        for enc in try_encodings:
            try:
                with open(file_path, 'r', encoding=enc, errors=errors) as f:
                    content = f.read()
                logger.info(f"使用 {enc} 编码成功读取文件: {file_path}")
                return content
            except UnicodeDecodeError:
                continue
        
        logger.error(f"所有编码尝试都失败了: {file_path}")
        return None
        
    except Exception as e:
            log_exception(logger, f"读取文件失败 {file_path}", e)
            return None

def write_file(file_path: str, content: str, encoding: str = 'utf-8', overwrite: bool = True) -> bool:
    """
    安全写入文件内容
    
    参数:
        file_path: 文件路径
        content: 要写入的内容
        encoding: 文件编码，默认为utf-8
        overwrite: 是否覆盖现有文件，默认为True
        
    返回:
        写入成功返回True，失败返回False
    """
    try:
        # 检查文件是否存在
        if os.path.exists(file_path):
            if not overwrite:
                logger.warning(f"文件已存在且overwrite=False: {file_path}")
                return False
            
            # 检查是否为文件
            if not os.path.isfile(file_path):
                logger.error(f"路径不是文件: {file_path}")
                return False
        else:
            # 创建目录（如果不存在）
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    logger.info(f"创建目录: {dir_path}")
                except Exception as e:
                    logger.error(f"创建目录失败 {dir_path}: {e}")
                    return False
        
        start_time = time.time()
        with open(file_path, 'w', encoding='utf-8-sig' if encoding == 'utf-8' else encoding) as f:
            f.write(content)
            
        elapsed_time = time.time() - start_time
        logger.info(f"成功写入文件: {file_path}，大小: {len(content)}字符，耗时: {elapsed_time:.2f}秒")
        log_performance(logger, "写入文件", elapsed_time, file_path=file_path, size=len(content))
        return True
        
    except Exception as e:
        log_exception(logger, f"写入文件失败 {file_path}", e)
        return False

def append_to_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    追加内容到文件末尾
    
    参数:
        file_path: 文件路径
        content: 要追加的内容
        encoding: 文件编码，默认为utf-8
        
    返回:
        追加成功返回True，失败返回False
    """
    try:
        # 创建目录（如果不存在）
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"创建目录: {dir_path}")
            except Exception as e:
                logger.error(f"创建目录失败 {dir_path}: {e}")
                return False
        
        start_time = time.time()
        with open(file_path, 'a', encoding='utf-8-sig' if encoding == 'utf-8' else encoding) as f:
            f.write(content)
        
        elapsed_time = time.time() - start_time
        logger.debug(f"成功追加内容到文件 {file_path}，大小: {len(content)}字符，耗时: {elapsed_time:.2f}秒")
        return True
        
    except Exception as e:
        logger.error(f"追加文件失败 {file_path}: {e}")
        return False

def file_exists(file_path: str) -> bool:
    """
    检查文件是否存在
    
    参数:
        file_path: 文件路径
        
    返回:
        文件存在且为文件返回True，否则返回False
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)

def get_file_size(file_path: str, unit: str = 'bytes') -> Optional[float]:
    """
    获取文件大小
    
    参数:
        file_path: 文件路径
        unit: 单位，可选值: 'bytes', 'kb', 'mb', 'gb'
        
    返回:
        文件大小，单位转换后的数值，如果文件不存在则返回None
    """
    try:
        if not file_exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
        
        size = os.path.getsize(file_path)
        
        # 单位转换
        units = {
            'bytes': 1,
            'kb': 1024,
            'mb': 1024 * 1024,
            'gb': 1024 * 1024 * 1024
        }
        
        if unit not in units:
            logger.error(f"不支持的单位: {unit}")
            return None
            
        return size / units[unit]
        
    except Exception as e:
        logger.error(f"获取文件大小失败 {file_path}: {e}")
        return None

def list_files(directory: str, pattern: Optional[str] = None, recursive: bool = False) -> List[str]:
    """
    列出目录中的文件
    
    参数:
        directory: 目录路径
        pattern: 文件匹配模式，使用glob语法
        recursive: 是否递归子目录，默认为False
        
    返回:
        文件路径列表
    """
    try:
        if not os.path.exists(directory):
            logger.error(f"目录不存在: {directory}")
            return []
            
        if not os.path.isdir(directory):
            logger.error(f"路径不是目录: {directory}")
            return []
            
        files = []
        
        if pattern:
            import glob
            
            # 构建glob匹配模式
            if recursive:
                search_pattern = os.path.join(directory, '**', pattern)
            else:
                search_pattern = os.path.join(directory, pattern)
            
            files = glob.glob(search_pattern, recursive=recursive)
            
        else:
            # 列出所有文件
            if recursive:
                for root, _, filenames in os.walk(directory):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
            else:
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        files.append(file_path)
        
        logger.debug(f"在 {directory} 中找到 {len(files)} 个文件")
        return files
        
    except Exception as e:
        logger.error(f"列出文件失败 {directory}: {e}")
        return []

def delete_file(file_path: str, backup: bool = False) -> bool:
    """
    删除文件
    
    参数:
        file_path: 文件路径
        backup: 是否备份文件，默认为False
        
    返回:
        删除成功返回True，失败返回False
    """
    try:
        if not file_exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return True  # 文件不存在，视为删除成功
            
        # 备份文件
        if backup:
            backup_path = f"{file_path}.bak.{int(time.time())}"
            try:
                shutil.copy2(file_path, backup_path)
                logger.info(f"文件已备份到: {backup_path}")
            except Exception as e:
                logger.error(f"备份文件失败 {file_path}: {e}")
                return False
        
        # 删除文件
        os.remove(file_path)
        logger.info(f"文件已删除: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"删除文件失败 {file_path}: {e}")
        return False

def backup_file(file_path: str, backup_dir: Optional[str] = None, prefix: str = '', suffix: str = '') -> Optional[str]:
    """
    备份文件
    
    参数:
        file_path: 文件路径
        backup_dir: 备份目录，如果为None则使用原文件目录
        prefix: 备份文件前缀
        suffix: 备份文件后缀
        
    返回:
        备份文件路径，如果备份失败则返回None
    """
    try:
        if not file_exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
            
        # 确定备份目录
        if backup_dir is None:
            backup_dir = os.path.dirname(file_path)
        else:
            # 创建备份目录（如果不存在）
            os.makedirs(backup_dir, exist_ok=True)
        
        # 构建备份文件名
        base_name = os.path.basename(file_path)
        name, ext = os.path.splitext(base_name)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        backup_name = f"{prefix}{name}_{timestamp}{suffix}{ext}"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # 备份文件
        shutil.copy2(file_path, backup_path)
        logger.info(f"文件已备份: {file_path} -> {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"备份文件失败 {file_path}: {e}")
        return None

def get_file_line_count(file_path: str) -> Optional[int]:
    """
    获取文件行数
    
    参数:
        file_path: 文件路径
        
    返回:
        文件行数，如果文件不存在或读取失败则返回None
    """
    try:
        if not file_exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
            
        start_time = time.time()
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = sum(1 for _ in f)
        
        elapsed_time = time.time() - start_time
        logger.debug(f"成功获取文件行数 {file_path}: {line_count}行，耗时: {elapsed_time:.2f}秒")
        return line_count
        
    except Exception as e:
        logger.error(f"获取文件行数失败 {file_path}: {e}")
        return None

def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
    """
    获取文件详细信息
    
    参数:
        file_path: 文件路径
        
    返回:
        文件信息字典，如果文件不存在则返回None
    """
    try:
        if not file_exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
            
        stat_info = os.stat(file_path)
        
        info = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': stat_info.st_size,
            'size_mb': stat_info.st_size / (1024 * 1024),
            'created_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_ctime)),
            'modified_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_mtime)),
            'accessed_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_atime)),
            'line_count': get_file_line_count(file_path)
        }
        
        logger.debug(f"获取文件信息成功: {file_path}")
        return info
        
    except Exception as e:
        logger.error(f"获取文件信息失败 {file_path}: {e}")
        return None

def copy_file(src_path: str, dst_path: str, overwrite: bool = True) -> bool:
    """
    复制文件
    
    参数:
        src_path: 源文件路径
        dst_path: 目标文件路径
        overwrite: 是否覆盖现有文件，默认为True
        
    返回:
        复制成功返回True，失败返回False
    """
    try:
        if not file_exists(src_path):
            logger.error(f"源文件不存在: {src_path}")
            return False
            
        if os.path.exists(dst_path):
            if not overwrite:
                logger.warning(f"目标文件已存在且overwrite=False: {dst_path}")
                return False
            
            if os.path.isdir(dst_path):
                logger.error(f"目标路径是目录: {dst_path}")
                return False
        else:
            # 创建目录（如果不存在）
            dst_dir = os.path.dirname(dst_path)
            if dst_dir and not os.path.exists(dst_dir):
                os.makedirs(dst_dir, exist_ok=True)
        
        shutil.copy2(src_path, dst_path)
        logger.info(f"文件已复制: {src_path} -> {dst_path}")
        return True
        
    except Exception as e:
        logger.error(f"复制文件失败 {src_path} -> {dst_path}: {e}")
        return False

def move_file(src_path: str, dst_path: str, overwrite: bool = True) -> bool:
    """
    移动文件
    
    参数:
        src_path: 源文件路径
        dst_path: 目标文件路径
        overwrite: 是否覆盖现有文件，默认为True
        
    返回:
        移动成功返回True，失败返回False
    """
    try:
        if not file_exists(src_path):
            logger.error(f"源文件不存在: {src_path}")
            return False
            
        if os.path.exists(dst_path):
            if not overwrite:
                logger.warning(f"目标文件已存在且overwrite=False: {dst_path}")
                return False
            
            if os.path.isdir(dst_path):
                logger.error(f"目标路径是目录: {dst_path}")
                return False
        else:
            # 创建目录（如果不存在）
            dst_dir = os.path.dirname(dst_path)
            if dst_dir and not os.path.exists(dst_dir):
                os.makedirs(dst_dir, exist_ok=True)
        
        shutil.move(src_path, dst_path)
        logger.info(f"文件已移动: {src_path} -> {dst_path}")
        return True
        
    except Exception as e:
        logger.error(f"移动文件失败 {src_path} -> {dst_path}: {e}")
        return False

if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试读取文件
    print("测试读取文件:")
    content = read_file(__file__)
    if content:
        print(f"  成功读取当前文件，大小: {len(content)}字符")
    
    # 测试写入文件
    test_file = "test_write.txt"
    test_content = "测试文件写入\n第二行内容"
    print(f"\n测试写入文件 {test_file}:")
    if write_file(test_file, test_content):
        print("  文件写入成功")
        
        # 测试追加文件
        print("\n测试追加文件:")
        if append_to_file(test_file, "\n第三行追加内容"):
            print("  文件追加成功")
            
            # 测试读取追加后的内容
            appended_content = read_file(test_file)
            print(f"  追加后内容: {appended_content}")
    
    # 测试文件存在性
    print(f"\n测试文件存在性 {test_file}:")
    print(f"  文件存在: {file_exists(test_file)}")
    
    # 测试文件大小
    print(f"\n测试文件大小 {test_file}:")
    size = get_file_size(test_file, unit='kb')
    if size is not None:
        print(f"  文件大小: {size:.2f} KB")
    
    # 测试文件信息
    print(f"\n测试文件信息 {test_file}:")
    info = get_file_info(test_file)
    if info:
        print(f"  文件信息: {info}")
    
    # 测试删除文件
    print(f"\n测试删除文件 {test_file}:")
    if delete_file(test_file):
        print("  文件删除成功")
    
    # 测试列表文件
    print("\n测试列表文件:")
    files = list_files('.', pattern='*.py', recursive=False)
    print(f"  当前目录下找到 {len(files)} 个Python文件")
    for file in files[:5]:
        print(f"    {file}")