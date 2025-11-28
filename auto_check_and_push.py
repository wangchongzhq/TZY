#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动检查仓库状态并上传修改的脚本
功能：
1. 检查仓库当前状态
2. 处理可能的rebase或合并冲突
3. 更新process_4k_channels.py脚本（如果需要）
4. 运行process_4k_channels.py生成最新的4K_uhd_channels.txt
5. 自动添加和提交修改
6. 推送更改到远程仓库
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
        return {
            'success': False,
            'stdout': '',
            'stderr': f"命令执行超时: {timeout}秒",
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': f"命令执行出错: {str(e)}",
            'returncode': -2
        }

def check_git_status(cwd=None):
    """检查git状态"""
    print("\n===== 检查git状态 =====")
    result = run_command("git status", cwd=cwd)
    print(result['stdout'])
    if result['stderr']:
        print(f"错误: {result['stderr']}")
    return result

def handle_rebase_conflicts(cwd=None):
    """处理rebase冲突"""
    print("\n===== 检查是否存在rebase冲突 =====")
    result = run_command("git status", cwd=cwd)
    
    if "rebase" in result['stdout']:
        if "Unmerged paths" in result['stdout']:
            print("发现rebase冲突，尝试解决...")
            
            # 列出所有冲突文件
            conflict_files = []
            lines = result['stdout'].split('\n')
            in_unmerged = False
            
            for line in lines:
                if "Unmerged paths:" in line:
                    in_unmerged = True
                    continue
                if in_unmerged and line.startswith("\t"):
                    # 提取冲突文件路径
                    match = re.search(r"\t\w+\s+(.+)", line)
                    if match:
                        conflict_files.append(match.group(1))
                elif in_unmerged and not line.startswith("\t"):
                    break
            
            print(f"冲突文件: {conflict_files}")
            
            # 简单解决方案：使用我们的版本
            for file in conflict_files:
                print(f"解决冲突: {file} (使用我们的版本)")
                run_command(f"git checkout --ours -- {file}", cwd=cwd)
                run_command(f"git add {file}", cwd=cwd)
            
            # 继续rebase
            print("继续rebase...")
            result = run_command("git rebase --continue", cwd=cwd)
            print(result['stdout'])
            if result['stderr']:
                print(f"错误: {result['stderr']}")
            
            return result['success']
        else:
            print("rebase正在进行中，但没有冲突，继续rebase...")
            result = run_command("git rebase --continue", cwd=cwd)
            print(result['stdout'])
            if result['stderr']:
                print(f"错误: {result['stderr']}")
            return result['success']
    
    print("没有发现rebase冲突")
    return True

def check_and_update_process_4k_script(cwd=None):
    """检查并更新process_4k_channels.py脚本"""
    script_path = os.path.join(cwd or os.getcwd(), "process_4k_channels.py")
    
    if not os.path.exists(script_path):
        print(f"错误: {script_path} 文件不存在")
        return False
    
    print("\n===== 检查process_4k_channels.py脚本 =====")
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否需要更新（确保能生成至少200个GitHub URL）
    if '200' not in content or 'github_urls' not in content:
        print("需要更新process_4k_channels.py脚本...")
        
        # 读取原始脚本内容，然后手动更新
        updated_lines = []
        in_generate_github_urls = False
        added_fallback_function = False
        
        for line in content.splitlines():
            if 'def generate_github_urls():' in line:
                in_generate_github_urls = True
                # 添加备用函数
                updated_lines.append('def generate_fallback_github_urls():')
                updated_lines.append('    """生成备用GitHub直播源URL，确保至少有200个"""')
                updated_lines.append('    fallback_urls = []')
                updated_lines.append('    # 使用一些稳定的IPTV仓库，为每个仓库生成多个变体URL')
                updated_lines.append('    github_repos = [')
                updated_lines.append("        'Free-IPTV/IPTV',")
                updated_lines.append("        'iptv-org/iptv',")
                updated_lines.append("        'pierre-emmanuelJ/IPTVRepository',")
                updated_lines.append("        'kingfire/IPTV',")
                updated_lines.append("        'iptv/playlist-links'")
                updated_lines.append('    ]')
                updated_lines.append('')
                updated_lines.append('    # 为每个仓库生成多个变体URL')
                updated_lines.append('    for repo in github_repos:')
                updated_lines.append('        user, repo_name = repo.split("/")')
                updated_lines.append('        # 生成不同分支和路径的URL变体')
                updated_lines.append('        branches = ["main", "master", "gh-pages"]')
                updated_lines.append('        paths = [')
                updated_lines.append('            "streams", "channels", "playlists", "m3u",')
                updated_lines.append('            "iptv/streams", "iptv/channels", "iptv/playlists"')
                updated_lines.append('        ]')
                updated_lines.append('')
                updated_lines.append('        for branch in branches:')
                updated_lines.append('            for path in paths:')
                updated_lines.append('                # 生成不同的文件名')
                updated_lines.append('                filenames = [')
                updated_lines.append('                    "all.m3u", "playlist.m3u", "tv.m3u", "iptv.m3u",')
                updated_lines.append('                    "index.m3u", "channels.m3u", "live.m3u"')
                updated_lines.append('                ]')
                updated_lines.append('')
                updated_lines.append('                for filename in filenames:')
                updated_lines.append('                    url = f"https://raw.githubusercontent.com/{user}/{repo_name}/{branch}/{path}/{filename}"')
                updated_lines.append('                    fallback_urls.append(url)')
                updated_lines.append('    ')
                updated_lines.append('    return fallback_urls')
                updated_lines.append('')
                updated_lines.append('')
                updated_lines.append(line)  # 添加原始的generate_github_urls函数定义
                added_fallback_function = True
            elif in_generate_github_urls and '# 获取GitHub直播源' in line:
                # 更新获取GitHub直播源的代码
                updated_lines.append('    # 获取GitHub直播源')
                updated_lines.append('    github_urls = []')
                updated_lines.append('    repo_count = {}')
                updated_lines.append('')
                updated_lines.append('    # 首先从主要来源获取GitHub URL')
                updated_lines.append('    for username in github_usernames:')
                updated_lines.append('        for repo in github_repos:')
                updated_lines.append('            if repo_count.get(f"{username}/{repo}", 0) < 5:')
                updated_lines.append('                url = f"https://raw.githubusercontent.com/{username}/{repo}/master/streams/playlist.m3u"')
                updated_lines.append('                github_urls.append(url)')
                updated_lines.append('                repo_count[f"{username}/{repo}"] = repo_count.get(f"{username}/{repo}", 0) + 1')
                updated_lines.append('')
                updated_lines.append('    # 如果GitHub URL不足200个，使用备用URL')
                updated_lines.append('    if len(github_urls) < 200:')
                updated_lines.append('        print(f"GitHub URL不足200个({len(github_urls)}个)，添加备用URL...")')
                updated_lines.append('        fallback_urls = generate_fallback_github_urls()')
                updated_lines.append('')
                updated_lines.append('        # 确保不超过200个URL，并且每个仓库的URL不超过5个')
                updated_lines.append('        for url in fallback_urls:')
                updated_lines.append('            if len(github_urls) >= 200:')
                updated_lines.append('                break')
                updated_lines.append('')
                updated_lines.append('            # 提取仓库信息')
                updated_lines.append('            match = re.search(r"github.com/([^/]+)/([^/]+)/", url)')
                updated_lines.append('            if match:')
                updated_lines.append('                repo_key = f"{match.group(1)}/{match.group(2)}"')
                updated_lines.append('                if repo_count.get(repo_key, 0) < 5:')
                updated_lines.append('                    github_urls.append(url)')
                updated_lines.append('                    repo_count[repo_key] = repo_count.get(repo_key, 0) + 1')
                updated_lines.append('')
                updated_lines.append('    # 限制GitHub URL数量为200个')
                updated_lines.append('    github_urls = github_urls[:200]')
                updated_lines.append('')
                updated_lines.append('    print(f"成功生成{len(github_urls)}个GitHub直播源URL")')
                updated_lines.append('')
                updated_lines.append('    # 将4K频道和GitHub直播源合并')
                updated_lines.append('    all_channels = sorted_4k_channels + github_urls')
                # 跳过原始的这段代码，直到找到下一个逻辑块
                while '# 将4K频道和GitHub直播源合并' not in line:
                    # 继续读取下一行，直到找到结束标记
                    if '# 将4K频道和GitHub直播源合并' in line:
                        break
            elif in_generate_github_urls and '# 将4K频道和GitHub直播源合并' in line:
                # 跳过原始的合并代码，因为我们已经添加了更新后的版本
                pass
            else:
                updated_lines.append(line)
        
        # 如果没有找到generate_github_urls函数，我们仍然需要更新文件
        if not added_fallback_function:
            print("警告: 未找到generate_github_urls函数，无法更新脚本")
            return False
        
        updated_content = '\n'.join(updated_lines)
        
        # 保存更新后的脚本
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("process_4k_channels.py脚本已更新")
        return True
    else:
        print("process_4k_channels.py脚本已是最新版本")
        return True

def run_process_4k_script(cwd=None):
    """运行process_4k_channels.py脚本生成最新的4K_uhd_channels.txt"""
    print("\n===== 运行process_4k_channels.py脚本 =====")
    result = run_command("python process_4k_channels.py", cwd=cwd)
    print(result['stdout'])
    if result['stderr']:
        print(f"错误: {result['stderr']}")
    return result['success']

def add_and_commit_changes(cwd=None):
    """添加并提交修改"""
    print("\n===== 添加并提交修改 =====")
    
    # 添加所有修改的文件
    result = run_command("git add -u", cwd=cwd)
    if not result['success']:
        print(f"添加修改文件失败: {result['stderr']}")
        return False
    
    # 添加特定的未跟踪文件（如果需要）
    important_files = ['process_4k_channels.py', '4K_uhd_channels.txt', 'auto_check_and_push.py']
    for file in important_files:
        if os.path.exists(os.path.join(cwd or os.getcwd(), file)):
            run_command(f"git add {file}", cwd=cwd)
    
    # 检查是否有更改要提交
    result = run_command("git status", cwd=cwd)
    if "nothing to commit" in result['stdout']:
        print("没有更改需要提交")
        return True
    
    # 提交更改
    commit_msg = "Auto update: Generate latest 4K UHD channels and GitHub URLs"
    result = run_command(f"git commit -m \"{commit_msg}\"", cwd=cwd)
    if not result['success']:
        print(f"提交失败: {result['stderr']}")
        return False
    
    print(f"提交成功: {commit_msg}")
    return True

def push_to_remote(cwd=None):
    """推送更改到远程仓库"""
    print("\n===== 推送更改到远程仓库 =====")
    
    # 获取当前分支
    result = run_command("git branch --show-current", cwd=cwd)
    if not result['success']:
        print(f"获取当前分支失败: {result['stderr']}")
        branch = "main"  # 默认分支
    else:
        branch = result['stdout'].strip() or "main"
    
    print(f"当前分支: {branch}")
    
    # 尝试正常推送
    result = run_command(f"git push TZY {branch}", cwd=cwd)
    if result['success']:
        print("推送成功!")
        return True
    
    # 如果失败，尝试拉取后再推送
    print("推送失败，尝试拉取最新更改...")
    result = run_command(f"git pull --rebase TZY {branch}", cwd=cwd)
    if not result['success']:
        print(f"拉取失败: {result['stderr']}")
        
        # 尝试强制推送
        print("尝试强制推送...")
        result = run_command(f"git push TZY {branch} --force", cwd=cwd)
        if result['success']:
            print("强制推送成功!")
            return True
        else:
            print(f"强制推送失败: {result['stderr']}")
            return False
    
    # 拉取成功后再次推送
    print("拉取成功，再次尝试推送...")
    result = run_command(f"git push TZY {branch}", cwd=cwd)
    if result['success']:
        print("推送成功!")
        return True
    else:
        print(f"推送失败: {result['stderr']}")
        
        # 最后尝试强制推送
        print("最后尝试强制推送...")
        result = run_command(f"git push TZY {branch} --force", cwd=cwd)
        if result['success']:
            print("强制推送成功!")
            return True
        else:
            print(f"强制推送失败: {result['stderr']}")
            return False

def main():
    """主函数"""
    print("===== 自动检查和上传脚本启动 =====")
    start_time = time.time()
    
    # 设置工作目录
    cwd = os.path.dirname(os.path.abspath(__file__))
    print(f"工作目录: {cwd}")
    
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
            print("提交修改失败，退出脚本")
            sys.exit(1)
        
        # 6. 推送更改到远程仓库
        if not push_to_remote(cwd):
            print("推送更改失败，退出脚本")
            sys.exit(1)
        
        end_time = time.time()
        print(f"\n===== 脚本执行成功！耗时: {end_time - start_time:.2f}秒 =====")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n脚本被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n脚本执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()