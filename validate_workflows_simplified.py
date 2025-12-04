#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流配置验证脚本

此脚本用于验证GitHub Actions工作流文件中的Git命令配置是否正确，
包括变量使用、命令格式和同步策略等。
"""

import os
import re
import yaml
from pathlib import Path

def validate_workflow(file_path):
    """验证单个工作流文件的Git配置"""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            workflow = yaml.safe_load(content)
    except Exception as e:
        return False

    # 检查权限配置
    permissions = workflow.get('permissions', {})
    if permissions.get('contents') != 'write':
        return False

    # 获取作业名称
    jobs = workflow.get('jobs', {})
    if not jobs:
        return False

    job_name = next(iter(jobs))

    # 获取步骤
    steps = jobs.get(job_name, {}).get('steps', [])

    # 检查Git命令配置
    git_commands = []
    git_patterns = {
        'fetch': r'git fetch origin\s+\$\{\{\s*github\.ref_name\s*\}\}',
        'checkout': r'git checkout\s+\$\{\{\s*github\.ref_name\s*\}\}',
        'reset': r'git reset --hard origin/\$\{\{\s*github\.ref_name\s*\}\}',
        'config': r'git config --local',
        'push': r'git push.*origin\s+\$\{\{\s*github\.ref_name\s*\}\}|git push.*origin\s+main'
    }

    # 搜索Git命令
    for i, step in enumerate(steps):
        if 'run' in step:
            run_content = step['run']
            git_commands.append(run_content)

    # 验证Git命令
    all_commands = '\n'.join(git_commands)

    results = []

    for cmd_name, pattern in git_patterns.items():
        if re.search(pattern, all_commands):
            results.append(True)
        else:
            results.append(False)

    # 检查推送策略
    push_strategy = re.findall(r'git push[^\n]+', all_commands)
    for i, push_cmd in enumerate(push_strategy):

    if len(push_strategy) >= 2:
        results.append(True)
    else:
        results.append(False)

    # 检查GitHub Actions邮箱格式
    if re.search(r'github-actions\[bot\]@users\.noreply\.github\.com', all_commands):
        results.append(True)
    else:
        results.append(False)

    return all(results)

def main():
    """主函数，验证所有工作流文件"""

    # 获取工作流目录
    workflows_dir = Path('.github', 'workflows')
    if not workflows_dir.exists():
        return

    # 验证所有YAML文件
    workflow_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))
    total = len(workflow_files)
    passed = 0

    for workflow_file in workflow_files:
        if validate_workflow(workflow_file):
            passed += 1
        else:

    if passed == total:
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())
