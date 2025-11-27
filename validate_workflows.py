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
    print(f"\n=== 验证工作流文件: {file_path} ===")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"📄 文件内容前1000字符:")
            print(content[:1000])
            print("...")
            workflow = yaml.safe_load(content)
            print(f"✅ YAML解析成功")
    except Exception as e:
        print(f"❌ 解析文件失败: {e}")
        return False
    
    # 检查权限配置
    print(f"\n🔍 检查权限配置...")
    permissions = workflow.get('permissions', {})
    print(f"当前权限: {permissions}")
    if permissions.get('contents') != 'write':
        print(f"❌ 缺少必要的写入权限: contents: write")
    else:
        print(f"✅ 权限配置正确")
    
    # 获取作业名称
    jobs = workflow.get('jobs', {})
    if not jobs:
        print(f"❌ 没有找到作业配置")
        return False
    
    job_name = next(iter(jobs))
    print(f"\n🔍 检查作业 '{job_name}' 的步骤...")
    
    # 获取步骤
    steps = jobs.get(job_name, {}).get('steps', [])
    print(f"找到 {len(steps)} 个步骤")
    
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
    print(f"\n🔍 提取所有Git命令...")
    for i, step in enumerate(steps):
        print(f"  步骤 {i+1}: {step.get('name', '无名称')}")
        if 'run' in step:
            run_content = step['run']
            print(f"    命令内容: {run_content[:200]}...")
            git_commands.append(run_content)
    
    # 验证Git命令
    all_commands = '\n'.join(git_commands)
    print(f"\n🔍 验证Git命令格式...")
    print(f"所有Git命令:")
    print(all_commands)
    
    results = []
    
    for cmd_name, pattern in git_patterns.items():
        print(f"\n  检查 {cmd_name} 命令:")
        print(f"    期望模式: {pattern}")
        if re.search(pattern, all_commands):
            print(f"    ✅ 找到匹配")
            results.append(True)
        else:
            print(f"    ❌ 没有找到匹配")
            results.append(False)
    
    # 检查推送策略
    print(f"\n🔍 检查推送策略...")
    push_strategy = re.findall(r'git push[^\n]+', all_commands)
    print(f"    找到 {len(push_strategy)} 个推送命令:")
    for i, push_cmd in enumerate(push_strategy):
        print(f"      {i+1}. {push_cmd}")
    
    if len(push_strategy) >= 2:
        print(f"    ✅ 找到多级推送策略")
        results.append(True)
    else:
        print(f"    ⚠️  推送策略可能不够健壮")
        results.append(False)
    
    # 检查GitHub Actions邮箱格式
    print(f"\n🔍 检查GitHub Actions邮箱格式...")
    if re.search(r'github-actions\[bot\]@users\.noreply\.github\.com', all_commands):
        print(f"    ✅ 使用了正确的GitHub Actions邮箱格式")
        results.append(True)
    else:
        print(f"    ⚠️  可能缺少GitHub Actions邮箱格式")
        results.append(False)
    
    print(f"\n📊 验证结果: {sum(results)}/{len(results)} 通过")
    return all(results)


def main():
    """主函数，验证所有工作流文件"""
    print("🎯 开始验证GitHub Actions工作流配置")
    print("=" * 50)
    
    # 获取工作流目录
    workflows_dir = Path('.github', 'workflows')
    if not workflows_dir.exists():
        print(f"❌ 工作流目录不存在: {workflows_dir}")
        return
    
    # 验证所有YAML文件
    workflow_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))
    total = len(workflow_files)
    passed = 0
    
    for workflow_file in workflow_files:
        if validate_workflow(workflow_file):
            print("✅ 工作流验证通过")
            passed += 1
        else:
            print("❌ 工作流验证失败")
    
    print("\n" + "=" * 50)
    print(f"📊 验证结果: {passed}/{total} 工作流通过验证")
    
    if passed == total:
        print("🎉 所有工作流配置验证通过！")
        return 0
    else:
        print("⚠️  部分工作流配置需要修复")
        return 1


if __name__ == "__main__":
    exit(main())
