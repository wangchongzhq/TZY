#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件检查脚本
用于验证项目配置文件的格式和内容是否正确
"""

import json
import os
import sys

# 配置文件路径
CONFIG_FILE = 'config/config.json'


def check_config_file():
    """检查配置文件是否存在并验证格式"""
    print(f"检查配置文件: {CONFIG_FILE}")
    
    # 检查文件是否存在
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 错误: 配置文件 {CONFIG_FILE} 不存在")
        return False
    
    try:
        # 尝试读取配置文件
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ 配置文件格式验证通过")
        print("📋 配置文件包含以下主要部分:")
        
        # 显示配置文件的主要结构
        main_sections = list(config.keys())
        print(f"   {', '.join(main_sections)}")
        
        # 如果有network配置，验证其格式
        if 'network' in config:
            network_config = config['network']
            print("\n🔍 网络配置验证:")
            print(f"   超时时间: {network_config.get('timeout', '未设置')}")
            print(f"   最大重试次数: {network_config.get('max_retries', '未设置')}")
            print(f"   最大工作线程: {network_config.get('max_workers', '未设置')}")
            
        # 如果有logging配置，验证其格式
        if 'logging' in config:
            logging_config = config['logging']
            print("\n📝 日志配置验证:")
            print(f"   日志级别: {logging_config.get('level', '未设置')}")
            print(f"   日志文件: {logging_config.get('file_path', '未设置')}")
            
        # 如果有output配置，验证其格式
        if 'output' in config:
            output_config = config['output']
            print("\n📦 输出配置验证:")
            print(f"   M3U文件: {output_config.get('m3u_file', '未设置')}")
            print(f"   TXT文件: {output_config.get('txt_file', '未设置')}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ 错误: 配置文件格式无效 - {e}")
        return False
    except Exception as e:
        print(f"❌ 错误: 检查配置文件时发生意外错误 - {e}")
        return False


def main():
    """主函数"""
    print("开始检查配置文件...")
    if check_config_file():
        print("\n🎉 所有配置检查通过！")
        sys.exit(0)
    else:
        print("\n❌ 配置检查失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
