# -*- coding: utf-8 -*-
"""
更新config.json文件，为所有频道别名添加繁体中文版本
"""
import json
import os
import sys

# 添加项目根目录到模块搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import read_file, write_file, file_exists
from core.chinese_conversion import add_traditional_aliases

# 配置文件路径
CONFIG_FILE_PATH = 'config/config.json'


def update_config_traditional_aliases():
    """
    更新config.json文件，为频道别名添加繁体中文版本
    """
    # 检查配置文件是否存在
    if not file_exists(CONFIG_FILE_PATH):
        print(f"错误: 配置文件 {CONFIG_FILE_PATH} 不存在")
        return False
    
    try:
        # 读取配置文件
        content = read_file(CONFIG_FILE_PATH)
        if not content:
            print(f"错误: 无法读取配置文件 {CONFIG_FILE_PATH}")
            return False
        config = json.loads(content)
        
        print("✓ 成功读取配置文件")
        
        # 检查channels.name_mappings是否存在
        if 'channels' not in config or 'name_mappings' not in config['channels']:
            print("错误: 配置文件中缺少channels.name_mappings部分")
            return False
        
        # 获取原始频道别名
        original_aliases = config['channels']['name_mappings']
        print(f"✓ 找到 {len(original_aliases)} 个频道的别名配置")
        
        # 添加繁体别名
        updated_aliases = add_traditional_aliases(original_aliases)
        print(f"✓ 成功为所有频道别名添加繁体中文版本")
        
        # 更新配置
        config['channels']['name_mappings'] = updated_aliases
        
        # 保存更新后的配置文件
        updated_content = json.dumps(config, ensure_ascii=False, indent=2)
        if not write_file(CONFIG_FILE_PATH, updated_content):
            print(f"错误: 无法保存配置文件 {CONFIG_FILE_PATH}")
            return False
        
        print(f"✓ 成功保存更新后的配置文件到 {CONFIG_FILE_PATH}")
        print(f"✓ 总共有 {len(updated_aliases)} 个频道别名配置已更新")
        
        return True
        
    except Exception as e:
        print(f"错误: 更新配置文件时发生异常: {e}")
        return False


if __name__ == "__main__":
    print("开始更新config.json文件中的频道别名，添加繁体中文版本...")
    print("=" * 60)
    
    success = update_config_traditional_aliases()
    
    print("=" * 60)
    if success:
        print("✅ 所有频道别名已成功添加繁体中文版本！")
    else:
        print("❌ 更新失败，请检查错误信息")
