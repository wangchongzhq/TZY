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
import sys

# 导入核心模块
from core.logging_config import setup_logging, get_logger

# 设置日志
setup_logging()
logger = get_logger(__name__)

# 定义文件路径
SOURCES_JSON = 'sources.json'
UNIFIED_SOURCES_PY = 'unified_sources.py'

# 需要更新的脚本列表
SCRIPTS_TO_UPDATE = [
    'IPTV.py',
    'ipzyauto.py',
    'scripts/convert_m3u_to_txt.py'
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
    content = '''# -*- coding: utf-8 -*-
# 统一播放源列表
# 此文件由update_sources.py自动生成，请勿手动修改

# 播放源URL列表
UNIFIED_SOURCES = [
{urls}
]

# 带名称的播放源列表（用于ipzyauto.py）
SOURCES_WITH_NAMES = [
{sources_with_names}
]
'''
    
    # 格式化URL列表
    urls_formatted = ['    "' + url.replace('"', '\\"') + '"' for url in urls]
    urls_str = ',\n'.join(urls_formatted)
    
    # 格式化带名称的播放源列表
    sources_with_names_formatted = ['    ("' + name.replace('"', '\\"') + '", "' + url.replace('"', '\\"') + '")' for name, url in sources_with_names]
    sources_with_names_str = ',\n'.join(sources_with_names_formatted)
    
    # 替换占位符
    content = content.format(urls=urls_str, sources_with_names=sources_with_names_str)
    
    # 写入文件
    with open(UNIFIED_SOURCES_PY, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"✅ 已生成 {UNIFIED_SOURCES_PY}")


def update_script(script_path):
    """更新单个脚本中的播放源"""
    try:
        # 使用utf-8-sig编码读取文件，自动处理BOM字符
        with open(script_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"❌ 读取文件 {script_path} 失败: {e}")
        return
    
    # 检查文件中是否已经导入了unified_sources
    if 'from unified_sources import' not in content:
        updated = False
        
        # 根据不同脚本类型进行处理
        if 'GITHUB_SOURCES' in content:
            # 匹配GITHUB_SOURCES = get_config(...) 的情况，使用多行匹配
            pattern = r'GITHUB_SOURCES\s*=\s*get_config\(.*?\)'
            replacement = '''# 从统一播放源文件导入
from unified_sources import UNIFIED_SOURCES
GITHUB_SOURCES = UNIFIED_SOURCES'''
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            if new_content != content:
                content = new_content
                updated = True
                logger.debug(f"使用GITHUB_SOURCES模式更新 {script_path}")
        
        if 'default_sources' in content and 'user_sources' in content:
            # 处理IPTV.py类型的脚本
            # 分别匹配default_sources和user_sources，不要求它们紧挨着
            default_sources_pattern = r'default_sources\s*=\s*\[.*?\]'
            user_sources_pattern = r'user_sources\s*=\s*\[.*?\]'
            
            # 先替换default_sources
            new_content = re.sub(default_sources_pattern, '''# 从统一播放源文件导入
from unified_sources import UNIFIED_SOURCES
default_sources = UNIFIED_SOURCES''', content, flags=re.DOTALL)
            if new_content != content:
                content = new_content
                updated = True
                logger.debug(f"更新 {script_path} 中的default_sources")
            
            # 然后替换user_sources
            new_content = re.sub(user_sources_pattern, '''user_sources = []''', content, flags=re.DOTALL)
            if new_content != content:
                content = new_content
                updated = True
                logger.debug(f"更新 {script_path} 中的user_sources")
        
        elif 'urls' in content:
            # 处理其他直接使用urls变量的脚本
            pattern = r'urls\s*=\s*\[.*?\]'
            replacement = '''# 从统一播放源文件导入
from unified_sources import UNIFIED_SOURCES
urls = UNIFIED_SOURCES'''
            
            # 使用多行匹配进行替换
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            if new_content != content:
                content = new_content
                updated = True
                logger.debug(f"使用urls模式更新 {script_path}")
        
        if not updated:
            logger.warning(f"⚠️  未知的数据源格式，跳过 {script_path}")
            return
    
    try:
        # 写入更新后的内容
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"✅ 已更新 {script_path}")
    except Exception as e:
        logger.error(f"❌ 写入文件 {script_path} 失败: {e}")
        return


def main():
    """主函数"""
    logger.info("=== 播放源自动更新脚本 ===")
    
    # 检查sources.json是否存在
    if not os.path.exists(SOURCES_JSON):
        logger.error(f"❌ 找不到 {SOURCES_JSON} 文件")
        return
    
    # 读取播放源
    logger.info("📖 读取播放源列表...")
    urls, sources_with_names = read_sources_from_json()
    logger.info(f"📊 共读取到 {len(urls)} 个启用的播放源")
    
    # 生成unified_sources.py
    logger.info("🔧 生成统一播放源文件...")
    generate_unified_sources(urls, sources_with_names)
    
    # 更新所有脚本
    logger.info("🔄 更新所有脚本...")
    for script in SCRIPTS_TO_UPDATE:
        if os.path.exists(script):
            update_script(script)
        else:
            logger.error(f"❌ 找不到 {script} 文件")
    
    logger.info("\n🎉 所有更新已完成！")
    logger.info(f"📝 更新了 {len([s for s in SCRIPTS_TO_UPDATE if os.path.exists(s)])} 个脚本")


if __name__ == "__main__":
    main()