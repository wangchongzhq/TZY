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

# 定义文件路径
SOURCES_JSON = 'sources.json'
UNIFIED_SOURCES_PY = 'unified_sources.py'

# 设置脚本执行时的编码
import sys
if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')
else:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 需要更新的脚本列表
SCRIPTS_TO_UPDATE = [
    'tvzy.py',
    'tvzy_simplified.py',
    'ipzyauto.py',
    'ipzyauto_simplified.py',
    'IP-TV.py',
    'IP-TV_simplified.py',
    'collect_ipzy.py'
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

# 带名称的播放源列表（用于collect_ipzy.py）
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
    
    print(f"✅ 已生成 {UNIFIED_SOURCES_PY}")


def update_script(script_path):
    """更新单个脚本中的播放源"""
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查文件中是否已经导入了unified_sources
    if 'from unified_sources import' not in content:
        # 根据不同脚本类型进行处理
        if script_path == 'collect_ipzy.py':
            # 替换SOURCES列表
            sources_pattern = r'SOURCES\s*=\s*\[.*?\]'  # 匹配SOURCES = [ ... ]
            replacement = '''# 从统一播放源文件导入
from unified_sources import SOURCES_WITH_NAMES
SOURCES = SOURCES_WITH_NAMES'''
        else:
            # 替换GITHUB_SOURCES或其他数据源列表
            if 'GITHUB_SOURCES' in content:
                pattern = r'GITHUB_SOURCES\s*=\s*\[.*?\]'  # 匹配GITHUB_SOURCES = [ ... ]
                replacement = '''# 从统一播放源文件导入
from unified_sources import UNIFIED_SOURCES
GITHUB_SOURCES = UNIFIED_SOURCES'''
            elif 'default_sources' in content and 'user_sources' in content:
                # 处理ipzyauto.py类型的脚本
                pattern = r'default_sources\s*=\s*\[.*?\]\s*user_sources\s*=\s*\[.*?\]'
                replacement = '''# 从统一播放源文件导入
from unified_sources import UNIFIED_SOURCES
urls = UNIFIED_SOURCES'''
            elif 'urls' in content:
                # 处理其他直接使用urls变量的脚本
                pattern = r'urls\s*=\s*\[.*?\]'
                replacement = '''# 从统一播放源文件导入
from unified_sources import UNIFIED_SOURCES
urls = UNIFIED_SOURCES'''
            else:
                print(f"⚠️  未知的数据源格式，跳过 {script_path}")
                return
        
        # 使用多行匹配进行替换
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # 写入更新后的内容
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已更新 {script_path}")


def main():
    """主函数"""
    print("=== 播放源自动更新脚本 ===")
    
    # 检查sources.json是否存在
    if not os.path.exists(SOURCES_JSON):
        print(f"❌ 找不到 {SOURCES_JSON} 文件")
        return
    
    # 读取播放源
    print("📖 读取播放源列表...")
    urls, sources_with_names = read_sources_from_json()
    print(f"📊 共读取到 {len(urls)} 个启用的播放源")
    
    # 生成unified_sources.py
    print("🔧 生成统一播放源文件...")
    generate_unified_sources(urls, sources_with_names)
    
    # 更新所有脚本
    print("🔄 更新所有脚本...")
    for script in SCRIPTS_TO_UPDATE:
        if os.path.exists(script):
            update_script(script)
        else:
            print(f"❌ 找不到 {script} 文件")
    
    print("\n🎉 所有更新已完成！")
    print(f"📝 更新了 {len([s for s in SCRIPTS_TO_UPDATE if os.path.exists(s)])} 个脚本")


if __name__ == "__main__":
    main()