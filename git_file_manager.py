#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys

# 设置标准输出为UTF-8编码
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# 检查文件的Git状态
def check_file_git_status(file_path):
    try:
        print(f"\n检查文件: {file_path}")
        # 检查文件是否存在
        import os
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在")
            return False
        
        # 使用当前脚本所在目录作为工作目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 检查文件是否在Git跟踪中
        result = subprocess.run(['git', 'ls-files', '--error-unmatch', file_path], 
                              capture_output=True, 
                              text=True, 
                              cwd=current_dir)
        
        if result.returncode == 0:
            print(f"✅ 文件在Git跟踪中")
            # 获取文件的状态
            status_result = subprocess.run(['git', 'status', '--short', file_path], 
                                         capture_output=True, 
                                         text=True, 
                                         cwd=current_dir)
            print(f"状态: {status_result.stdout.strip()}")
            return True
        else:
            print(f"❌ 文件不在Git跟踪中")
            return False
    except Exception as e:
        print(f"检查文件状态时出错: {e}")
        return False

# 添加文件到Git
def add_file_to_git(file_path):
    try:
        print(f"\n将文件添加到Git: {file_path}")
        # 使用当前脚本所在目录作为工作目录
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(['git', 'add', file_path], 
                              capture_output=True, 
                              text=True, 
                              cwd=current_dir)
        
        if result.returncode == 0:
            print(f"✅ 成功将文件添加到Git")
            # 检查添加后的状态
            status_result = subprocess.run(['git', 'status', '--short', file_path], 
                                         capture_output=True, 
                                         text=True, 
                                         cwd=current_dir)
            print(f"添加后的状态: {status_result.stdout.strip()}")
            return True
        else:
            print(f"❌ 添加文件失败")
            if result.stderr:
                print(f"错误信息: {result.stderr}")
            return False
    except Exception as e:
        print(f"添加文件到Git时出错: {e}")
        return False

# 提交文件
def commit_files():
    try:
        print(f"\n提交更改")
        commit_message = "添加git_check.py和github_actions_git_push_fix.md文件"
        # 使用当前脚本所在目录作为工作目录
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(['git', 'commit', '-m', commit_message], 
                              capture_output=True, 
                              text=True, 
                              cwd=current_dir)
        
        if result.returncode == 0:
            print(f"✅ 成功提交更改")
            print(f"提交信息: {commit_message}")
            return True
        else:
            print(f"❌ 提交失败")
            if result.stderr:
                print(f"错误信息: {result.stderr}")
            return False
    except Exception as e:
        print(f"提交更改时出错: {e}")
        return False

# 主程序
def main():
    print("=== Git文件状态检查与添加工具 ===")
    
    # 获取当前脚本所在目录
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 要检查的文件列表
    files_to_check = [
        os.path.join(script_dir, "github_actions_git_push_fix.md"),
        os.path.join(script_dir, "git_check.py")
    ]
    
    # 检查每个文件的状态
    files_to_add = []
    for file in files_to_check:
        if not check_file_git_status(file):
            files_to_add.append(file)
    
    # 如果有文件需要添加，执行添加操作
    if files_to_add:
        print(f"\n发现 {len(files_to_add)} 个文件需要添加到Git")
        
        # 添加所有文件
        all_added = True
        for file in files_to_add:
            if not add_file_to_git(file):
                all_added = False
        
        # 如果所有文件都成功添加，提交更改
        if all_added:
            print("\n所有文件都成功添加到Git，准备提交...")
            commit_files()
        else:
            print("\n部分文件添加失败，跳过提交")
    else:
        print("\n所有文件都已经在Git跟踪中，无需添加")
    
    print("\n=== 操作完成 ===")

if __name__ == "__main__":
    main()
