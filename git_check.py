#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os

# 设置标准输出为UTF-8编码
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# 执行git命令并捕获完整输出
def run_git_command(command):
    try:
        print(f"\n执行命令: git {command}")
        # 使用当前脚本所在目录作为工作目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(['git'] + command.split(), 
                              capture_output=True, 
                              text=True, 
                              cwd=current_dir)
        print(f"返回码: {result.returncode}")
        print("\n标准输出:")
        print(result.stdout)
        if result.stderr:
            print("\n错误输出:")
            print(result.stderr)
        return result
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return None

# 执行一系列git命令来全面检查仓库状态
print("=== Git仓库全面检查 ===")

# 1. 检查当前状态
run_git_command("status")

# 2. 检查远程仓库配置
run_git_command("remote -v")

# 3. 检查分支状态
run_git_command("branch -vv")

# 4. 检查最近的提交记录
run_git_command("log -n 5 --oneline")

# 5. 检查工作树和索引状态
run_git_command("diff --name-status")
run_git_command("diff --staged --name-status")

# 6. 检查本地与远程的差异
run_git_command("fetch")
run_git_command("log --oneline HEAD..origin/main")

print("\n=== 检查完成 ===")
