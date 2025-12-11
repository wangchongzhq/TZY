#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time

def run_command(cmd, desc):
    """运行命令并返回结果"""
    print(f"=== {desc} ===")
    print(f"执行命令: {cmd}")
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    end_time = time.time()
    print(f"退出码: {result.returncode}")
    print(f"执行时间: {end_time - start_time:.2f}秒")
    if result.stdout:
        print(f"标准输出:\n{result.stdout}")
    if result.stderr:
        print(f"标准错误:\n{result.stderr}")
    return result

def main():
    """主函数"""
    print("GitHub Actions 工作流诊断脚本")
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")
    print(f"文件列表: {os.listdir('.')}")
    
    # 测试基本git操作
    run_command("git --version", "Git版本")
    run_command("git status", "Git状态")
    run_command("git log --oneline -n 3", "最近3次提交")
    
    # 测试网络连接
    run_command("ping -c 3 github.com", "Ping GitHub")
    
    # 测试依赖安装
    run_command("pip --version", "Pip版本")
    run_command("pip list", "已安装依赖")
    
    # 测试IP-TV.py是否存在和基本运行
    if os.path.exists("IP-TV.py"):
        print("IP-TV.py存在")
        run_command("python IP-TV.py --help", "IP-TV.py帮助信息")
    else:
        print("IP-TV.py不存在")
    
    # 测试requirements.txt
    if os.path.exists("requirements.txt"):
        print("requirements.txt存在")
        with open("requirements.txt", "r") as f:
            print(f"依赖列表:\n{f.read()}")
    else:
        print("requirements.txt不存在")

if __name__ == "__main__":
    main()