#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试频道别名映射是否在ipzyauto.txt中生效
"""

import json
import os
from typing import Dict, List, Set

# 导入频道名称标准化函数
from core.channel_utils import normalize_channel_name

# 导入配置管理器
from core.config import get_config

# 从配置获取本地源开关设置
local_sources_enabled = get_config('local_sources.enabled', True)
local_sources_files = get_config('local_sources.files', [])

# 加载配置文件
def load_config():
    """加载配置文件"""
    config_path = os.path.join('config', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 加载ipzyauto.txt中的频道
def load_ipzy_channels():
    """加载ipzyauto.txt中的频道"""
    # 检查本地源开关
    if not local_sources_enabled:
        print("本地源功能已关闭，跳过加载本地文件")
        return []
    
    # 检查文件是否在允许的本地源列表中
    channels_path = 'ipzyauto.txt'
    if channels_path not in local_sources_files:
        print(f"文件 '{channels_path}' 不在允许的本地源列表中，跳过加载")
        return []
    
    channels = []
    current_category = None
    
    try:
        with open(channels_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# '):
                    # 分类行
                    current_category = line[2:]
                elif line and not line.startswith('#') and not '#genre#' in line:
                    # 频道行
                    if ',' in line:
                        name, url = line.split(',', 1)
                        channels.append({
                            'name': name.strip(),
                            'url': url.strip(),
                            'category': current_category
                        })
    except FileNotFoundError:
        print(f"错误：找不到文件 '{channels_path}'")
        return []
    
    return channels

# 检查频道是否使用了通用频道名
def check_channel_aliases():
    """检查频道是否使用了通用频道名"""
    # 加载配置
    config = load_config()
    name_mappings = config.get('channels', {}).get('name_mappings', {})
    
    # 加载ipzyauto.txt中的频道
    ipzy_channels = load_ipzy_channels()
    
    # 提取所有通用频道名
    standard_names = set(name_mappings.keys())
    
    # 提取所有别名
    all_aliases = set()
    for aliases in name_mappings.values():
        all_aliases.update(aliases)
    
    # 分析ipzyauto.txt中的频道名称
    print(f"配置中的通用频道名数量: {len(standard_names)}")
    print(f"配置中的别名数量: {len(all_aliases)}")
    print(f"ipzyauto.txt中的频道数量: {len(ipzy_channels)}")
    
    # 检查哪些频道名称匹配通用频道名
    matched_standard = set()
    matched_alias = set()
    unmatched = set()
    
    for channel in ipzy_channels:
        name = channel['name']
        
        # 先对频道名称进行标准化处理
        standardized_name = normalize_channel_name(name)
        
        if standardized_name in standard_names:
            matched_standard.add(name)
        elif standardized_name in all_aliases:
            matched_alias.add(name)
        else:
            unmatched.add(name)
    
    print(f"\n匹配通用频道名的数量: {len(matched_standard)}")
    print(f"匹配别名的数量: {len(matched_alias)}")
    print(f"未匹配的频道名称数量: {len(unmatched)}")
    
    # 显示未匹配的频道名称（前20个）
    print("\n未匹配的频道名称（前20个）:")
    for i, name in enumerate(sorted(unmatched)[:20]):
        print(f"  {i+1}. {name}")
    
    if len(unmatched) > 20:
        print(f"  ... 还有 {len(unmatched) - 20} 个未匹配的频道名称")
    
    # 显示匹配别名的频道名称（前20个）
    print("\n匹配别名的频道名称（前20个）:")
    for i, name in enumerate(sorted(matched_alias)[:20]):
        # 查找对应的通用频道名
        for standard_name, aliases in name_mappings.items():
            if name in aliases:
                print(f"  {i+1}. {name} -> {standard_name}")
                break
    
    if len(matched_alias) > 20:
        print(f"  ... 还有 {len(matched_alias) - 20} 个匹配别名的频道名称")
    
    # 统计每个分类的匹配情况
    print("\n各分类的匹配情况:")
    category_stats = {}
    
    for channel in ipzy_channels:
        name = channel['name']
        category = channel['category']
        
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'standard': 0, 'alias': 0, 'unmatched': 0}
        
        category_stats[category]['total'] += 1
        
        if name in standard_names:
            category_stats[category]['standard'] += 1
        elif name in all_aliases:
            category_stats[category]['alias'] += 1
        else:
            category_stats[category]['unmatched'] += 1
    
    for category, stats in sorted(category_stats.items()):
        print(f"  {category}: 总{stats['total']}, 通用{stats['standard']}, 别名{stats['alias']}, 未匹配{stats['unmatched']}")

if __name__ == "__main__":
    check_channel_aliases()
