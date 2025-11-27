#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys

# 检查文件是否存在
def check_files():
    files_to_check = [
        'process_4k_channels.py',
        'direct_fix.py',
        '4K_uhd_channels.txt',
        '.github/workflows/4k_uhd_update.yml'
    ]
    
    print("检查文件是否存在：")
    for file in files_to_check:
        if os.path.exists(file):
            print(f"✓ {file} 存在")
        else:
            print(f"✗ {file} 不存在")
    
    return all(os.path.exists(file) for file in files_to_check)

# 运行git命令
def run_git_command(command):
    print(f"\n运行命令: git {command}")
    try:
        result = subprocess.run(['git'] + command.split(), 
                               capture_output=True, 
                               text=True, 
                               cwd=os.getcwd())
        print(f"退出码: {result.returncode}")
        if result.stdout:
            print("输出:")
            print(result.stdout)
        if result.stderr:
            print("错误:")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"运行git命令时出错: {e}")
        return False

# 主函数
def main():
    # 检查文件
    if not check_files():
        print("\n错误：某些文件不存在！")
        sys.exit(1)
    
    # 运行git命令
    print("\n=== 开始推送更改 ===")
    
    # 添加文件
    if not run_git_command('add process_4k_channels.py direct_fix.py 4K_uhd_channels.txt .github/workflows/4k_uhd_update.yml'):
        print("添加文件失败！")
        sys.exit(1)
    
    # 提交更改
    if not run_git_command('commit -m "添加4K超高清直播源自动更新功能，包括脚本文件和工作流文件"'):
        print("提交更改失败！")
        sys.exit(1)
    
    # 拉取最新更改
    if not run_git_command('pull origin main'):
        print("拉取最新更改失败！")
        sys.exit(1)
    
    # 推送更改
    if not run_git_command('push origin main'):
        print("推送更改失败！")
        sys.exit(1)
    
    print("\n=== 推送成功！ ===")

if __name__ == "__main__":
    main()
