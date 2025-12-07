#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为config.json中的现有频道添加HD格式别名
"""

import json
import os

def update_hd_aliases():
    """
    为config.json中的所有频道添加HD格式别名
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
    
    # 读取配置文件
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    name_mappings = config.get('channels', {}).get('name_mappings', {})
    updated_count = 0
    
    for channel, aliases in name_mappings.items():
        # 跳过4K/8K频道，因为它们不需要HD别名
        if '4K' in channel or '8K' in channel:
            continue
            
        # 确保aliases是列表
        if not isinstance(aliases, list):
            aliases = [aliases]
            name_mappings[channel] = aliases
        
        # 创建别名集合以避免重复
        alias_set = set(aliases)
        original_count = len(alias_set)
        
        # 生成各种HD别名格式
        hd_formats = [
            f"{channel}HD",       # 无空格，如CCTV1HD
            f"{channel} HD",      # 有空格，如CCTV1 HD
            f"{channel}-HD",      # 带连字符，如CCTV1-HD
            f"{channel}高清"      # 高清中文，如CCTV1高清
        ]
        
        # 为频道添加HD别名
        for hd_format in hd_formats:
            alias_set.add(hd_format)
        
        # 处理带连字符的频道名，如CCTV-1
        if '-' in channel and not channel.endswith('-HD'):
            base_channel = channel.split('-')[0]  # 获取基础频道名
            suffix = channel.split('-')[-1] if len(channel.split('-')) > 1 else ''
            
            # 生成更多格式
            additional_formats = []
            if suffix:
                additional_formats.append(f"{base_channel}{suffix}HD")
                additional_formats.append(f"{base_channel}{suffix} HD")
                additional_formats.append(f"{base_channel}-{suffix}HD")
                additional_formats.append(f"{base_channel}-{suffix} HD")
            
            for fmt in additional_formats:
                alias_set.add(fmt)
        
        # 如果有变化，更新别名列表
        if len(alias_set) > original_count:
            name_mappings[channel] = list(alias_set)
            updated_count += 1
            added_aliases = [alias for alias in alias_set if alias not in aliases]
            print(f"已为频道 {channel} 添加HD别名: {', '.join(added_aliases)}")
    
    # 调试：查看所有频道
    print("\n调试信息：所有频道总数: {}".format(len(name_mappings)))
    print("\n前20个频道:")
    counter = 0
    for channel, aliases in name_mappings.items():
        counter += 1
        print(f"{channel}: {aliases}")
        if counter >= 20:
            break
    
    # 保存更新后的配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"\n更新完成！共为 {updated_count} 个频道添加了HD格式别名")

if __name__ == "__main__":
    update_hd_aliases()
