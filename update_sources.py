#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
播放源自动更新脚本

功能：
1. 读取sources.json中的播放源列表
2. 生成unified_sources.py文件
3. 更新所有相关脚本中的播放源

使用方法：
python update_sources.py
"""

import json
import os
import re

# 导入日志模块
import logging

# 配置日志记录
# 简化日志配置，只输出到控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # 确保日志使用utf-8编码
)
logger = logging.getLogger(__name__)

# 定义文件路径（使用绝对路径）
import os
SOURCES_JSON = os.path.abspath('sources.json')
UNIFIED_SOURCES_PY = os.path.abspath('unified_sources.py')

# 需要更新的脚本列表
SCRIPTS_TO_UPDATE = [
    'IP-TV.py'
]


def read_sources_from_json():
    """从JSON文件读取播放源列表"""
    with open(SOURCES_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 过滤出启用的播放源
    enabled_sources = [source for source in data['sources'] if source['enabled']]
    urls = [source['url'] for source in enabled_sources]
    sources_with_names = [(source['name'], source['url']) for source in enabled_sources]
    
    return urls, sources_with_names


def generate_unified_sources(urls, sources_with_names):
    """生成unified_sources.py文件"""
    # 确保urls和sources_with_names是列表
    urls = urls if isinstance(urls, list) else []
    sources_with_names = sources_with_names if isinstance(sources_with_names, list) else []
    
    # 格式化URL列表
    urls_formatted = [f'    "{url.replace("\"", "\\\"")}"' for url in urls]
    urls_str = ',\n'.join(urls_formatted)
    
    # 格式化带名称的播放源列表
    sources_with_names_formatted = [f'    ("{name.replace("\"", "\\\"")}", "{url.replace("\"", "\\\"")}")' for name, url in sources_with_names]
    sources_with_names_str = ',\n'.join(sources_with_names_formatted)
    
    # 使用f-string构建文件内容
    content = f'''# -*- coding: utf-8 -*-
# 统一播放源列表
# 此文件由update_sources.py自动生成，请勿手动修改

# 播放源URL列表
UNIFIED_SOURCES = [
{urls_str}
]

# 带名称的播放源列表（用于collect_ipzy.py）
SOURCES_WITH_NAMES = [
{sources_with_names_str}
]
'''
    
    # 写入文件
    try:
        # 确保目录存在
        dir_path = os.path.dirname(UNIFIED_SOURCES_PY)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"[OK] 创建目录: {dir_path}")
        
        with open(UNIFIED_SOURCES_PY, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        
        # 验证文件是否生成成功
        if os.path.exists(UNIFIED_SOURCES_PY):
            file_size = os.path.getsize(UNIFIED_SOURCES_PY)
            logger.info(f"[OK] 已生成 {UNIFIED_SOURCES_PY}，文件大小: {file_size} 字节")
            # 读取文件内容的前几行进行验证
            with open(UNIFIED_SOURCES_PY, 'r', encoding='utf-8') as f:
                first_lines = f.readlines()[:5]
            logger.info(f"文件内容前5行: {''.join(first_lines)}")
            # 检查文件是否为空
            if file_size == 0:
                logger.warning(f"[WARNING] {UNIFIED_SOURCES_PY} 文件为空")
        else:
            logger.error(f"[ERROR] 生成 {UNIFIED_SOURCES_PY} 失败，文件不存在")
            # 尝试使用相对路径再生成一次
            relative_path = "unified_sources.py"
            with open(relative_path, 'w', encoding='utf-8-sig') as f:
                f.write(content)
            if os.path.exists(relative_path):
                logger.info(f"[OK] 使用相对路径生成 {relative_path} 成功")
            else:
                logger.error(f"[ERROR] 使用相对路径生成 {relative_path} 也失败了")
    except Exception as e:
        logger.error(f"[ERROR] 写入 {UNIFIED_SOURCES_PY} 文件失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        # 尝试使用相对路径再生成一次
        relative_path = "unified_sources.py"
        try:
            with open(relative_path, 'w', encoding='utf-8-sig') as f:
                f.write(content)
            if os.path.exists(relative_path):
                logger.info(f"[OK] 使用相对路径生成 {relative_path} 成功")
            else:
                logger.error(f"[ERROR] 使用相对路径生成 {relative_path} 也失败了")
        except Exception as e2:
            logger.error(f"[ERROR] 使用相对路径生成 {relative_path} 也失败了: {e2}")


def update_script(script_path):
    """更新单个脚本中的播放源"""
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查文件中是否已经导入了unified_sources
    if 'from unified_sources import' not in content:
        # 根据不同脚本类型进行处理
        # 替换GITHUB_SOURCES或其他数据源列表
            if 'GITHUB_SOURCES' in content:
                # 匹配GITHUB_SOURCES = get_config(...) 的情况，使用多行匹配
                pattern = r'GITHUB_SOURCES\s*=\s*get_config\(.*?\)'  # 匹配GITHUB_SOURCES = get_config(...) 
                replacement = '''# 从统一播放源文件导入
from unified_sources import UNIFIED_SOURCES
GITHUB_SOURCES = UNIFIED_SOURCES'''
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            elif 'default_sources' in content and 'user_sources' in content:
                # 处理IP-TV.py类型的脚本
                # 分别匹配default_sources和user_sources，不要求它们紧挨着
                default_sources_pattern = r'default_sources\s*=\s*\[.*?\]'
                user_sources_pattern = r'user_sources\s*=\s*\[.*?\]'
                
                # 先替换default_sources
                content = re.sub(default_sources_pattern, '''# 从统一播放源文件导入
from unified_sources import UNIFIED_SOURCES
default_sources = UNIFIED_SOURCES''', content, flags=re.DOTALL)
                
                # 然后替换user_sources
                content = re.sub(user_sources_pattern, '''user_sources = []''', content, flags=re.DOTALL)
            elif 'urls' in content:
                # 处理其他直接使用urls变量的脚本
                pattern = r'urls\s*=\s*\[.*?\]'
                replacement = '''# 从统一播放源文件导入
from unified_sources import UNIFIED_SOURCES
urls = UNIFIED_SOURCES'''
                
                # 使用多行匹配进行替换
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            else:
                logger.warning(f"[WARNING] 未知的数据源格式，跳过 {script_path}")
                return
    
    # 写入更新后的内容
    with open(script_path, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    
    logger.info(f"[OK] 已更新 {script_path}")


def main():
    """主函数"""
    logger.info("=== 播放源自动更新脚本 ===")
    
    # 检查当前工作目录
    current_dir = os.getcwd()
    logger.info(f"当前工作目录: {current_dir}")
    
    # 检查sources.json是否存在
    if not os.path.exists(SOURCES_JSON):
        logger.error(f"[ERROR] 找不到 {SOURCES_JSON} 文件")
        # 即使sources.json不存在，也生成一个空的unified_sources.py文件
        logger.info("[INFO] 生成空的统一播放源文件...")
        generate_unified_sources([], [])
        return
    
    # 读取播放源
    logger.info("[INFO] 读取播放源列表...")
    urls, sources_with_names = read_sources_from_json()
    logger.info(f"[INFO] 共读取到 {len(urls)} 个启用的播放源")
    
    # 生成unified_sources.py
    logger.info("[INFO] 生成统一播放源文件...")
    generate_unified_sources(urls, sources_with_names)
    
    # 再次验证文件是否存在
    if not os.path.exists(UNIFIED_SOURCES_PY):
        logger.error(f"❌ 生成 {UNIFIED_SOURCES_PY} 失败，文件不存在")
        # 尝试再次生成
        logger.info("[INFO] 尝试再次生成统一播放源文件...")
        generate_unified_sources(urls, sources_with_names)
    
    # 更新所有脚本
    logger.info("[INFO] 更新所有脚本...")
    for script in SCRIPTS_TO_UPDATE:
        if os.path.exists(script):
            update_script(script)
        else:
            logger.error(f"[ERROR] 找不到 {script} 文件")
    
    logger.info("\n[DONE] 所有更新已完成！")
    logger.info(f"[INFO] 更新了 {len([s for s in SCRIPTS_TO_UPDATE if os.path.exists(s)])} 个脚本")


if __name__ == "__main__":
    main()