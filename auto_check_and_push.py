#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动检查仓库状态并上传修改的脚本
"""

import os
import subprocess
import sys
import time
import re

def run_command(cmd, cwd=None, shell=True, timeout=300):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            shell=shell, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            timeout=timeout
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'stdout': '', 'stderr': f"超时: {timeout}秒", 'returncode': -1}
    except Exception as e:
        return {'success': False, 'stdout': '', 'stderr': f"错误: {str(e)}", 'returncode': -2}

def check_git_status(cwd=None):
    """检查git状态"""
    result = run_command("git status", cwd=cwd)
    return result

def handle_rebase_conflicts(cwd=None):
    """处理rebase冲突"""
    result = run_command("git status", cwd=cwd)
    
    if "rebase" in result['stdout']:
        if "Unmerged paths" in result['stdout']:
            # 列出所有冲突文件
            conflict_files = []
            lines = result['stdout'].split('\n')
            in_unmerged = False
            
            for line in lines:
                if "Unmerged paths:" in line:
                    in_unmerged = True
                    continue
                if in_unmerged and line.startswith("\t"):
                    match = re.search(r"\t\w+\s+(.+)", line)
                    if match:
                        conflict_files.append(match.group(1))
                elif in_unmerged and not line.startswith("\t"):
                    break
            
            # 使用我们的版本解决冲突
            for file in conflict_files:
                run_command(f"git checkout --ours -- {file}", cwd=cwd)
                run_command(f"git add {file}", cwd=cwd)
            
            # 继续rebase
            result = run_command("git rebase --continue", cwd=cwd)
            return result['success']
        else:
            # 没有冲突，继续rebase
            result = run_command("git rebase --continue", cwd=cwd)
            return result['success']
    
    return True

def check_and_update_process_4k_script(cwd=None):
    """检查并更新process_4k_channels.py脚本"""
    script_path = os.path.join(cwd or os.getcwd(), "process_4k_channels.py")
    
    if not os.path.exists(script_path):
        return False
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否需要更新（确保能生成至少200个GitHub URL）
    if '200' not in content or 'github_urls' not in content:
        # 这里简化处理，实际项目中可能需要更复杂的更新逻辑
        return False
    
    return True

def run_process_4k_script(cwd=None):
    """运行process_4k_channels.py脚本生成最新的4K_uhd_channels.txt"""
    result = run_command("python process_4k_channels.py", cwd=cwd)
    return result['success']

def add_and_commit_changes(cwd=None):
    """添加并提交修改"""
    # 添加所有修改的文件
    run_command("git add -u", cwd=cwd)
    
    # 添加特定的未跟踪文件（如果需要）
    important_files = ['process_4k_channels.py', '4K_uhd_channels.txt', 'auto_check_and_push.py']
    for file in important_files:
        if os.path.exists(os.path.join(cwd or os.getcwd(), file)):
            run_command(f"git add {file}", cwd=cwd)
    
    # 检查是否有更改要提交
    result = run_command("git status", cwd=cwd)
    if "nothing to commit" in result['stdout']:
        return True
    
    # 提交更改
    commit_msg = "Auto update: Generate latest 4K UHD channels and GitHub URLs"
    result = run_command(f"git commit -m \"{commit_msg}\"", cwd=cwd)
    return result['success']

def push_to_remote(cwd=None):
    """推送更改到远程仓库"""
    # 获取当前分支
    result = run_command("git branch --show-current", cwd=cwd)
    branch = result['stdout'].strip() or "main"
    
    # 尝试正常推送
    result = run_command(f"git push TZY {branch}", cwd=cwd)
    if result['success']:
        return True
    
    # 如果失败，尝试拉取后再推送
    result = run_command(f"git pull --rebase TZY {branch}", cwd=cwd)
    if not result['success']:
        # 尝试强制推送
        result = run_command(f"git push TZY {branch} --force", cwd=cwd)
        return result['success']
    
    # 拉取成功后再次推送
    result = run_command(f"git push TZY {branch}", cwd=cwd)
    if result['success']:
        return True
    
    # 最后尝试强制推送
    result = run_command(f"git push TZY {branch} --force", cwd=cwd)
    return result['success']

def main():
    """主函数"""
    start_time = time.time()
    
    # 设置工作目录
    cwd = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # 1. 检查git状态
        git_status = check_git_status(cwd)
        
        # 2. 处理可能的rebase冲突
        if "rebase" in git_status['stdout']:
            handle_rebase_conflicts(cwd)
        
        # 3. 更新process_4k_channels.py脚本（如果需要）
        check_and_update_process_4k_script(cwd)
        
        # 4. 运行process_4k_channels.py生成最新的4K_uhd_channels.txt
        run_process_4k_script(cwd)
        
        # 5. 添加并提交修改
        if not add_and_commit_changes(cwd):
            sys.exit(1)
        
        # 6. 推送更改到远程仓库
        if not push_to_remote(cwd):
            sys.exit(1)
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()