#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的工作流配置验证脚本

此脚本用于验证GitHub Actions工作流文件的基本结构和关键配置，
确保它们包含必要的权限、步骤和Git命令。
"""

import os
import yaml
from pathlib import Path


def validate_workflow(file_path):
    """验证单个工作流文件的基本结构"""
    print(f"\n=== 验证工作流文件: {file_path} ===")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            workflow = yaml.safe_load(content)
            print(f"✅ YAML解析成功")
    except Exception as e:
        print(f"❌ 解析文件失败: {e}")
        return False
    
    # 检查权限配置
    permissions = workflow.get('permissions', {})
    if permissions.get('contents') == 'write':
        print(f"✅ 权限配置正确: {permissions}")
    else:
        print(f"⚠️  权限配置可能不完整: {permissions}")
    
    # 检查作业配置
    jobs = workflow.get('jobs', {})
    if not jobs:
        print(f"❌ 没有找到作业配置")
        return False
    
    job_name = next(iter(jobs))
    print(f"✅ 找到作业: {job_name}")
    
    # 获取步骤
    steps = jobs.get(job_name, {}).get('steps', [])
    print(f"✅ 找到 {len(steps)} 个步骤")
    
    # 检查关键步骤
    has_checkout = False
    has_run = False
    has_git_commands = False
    
    for i, step in enumerate(steps):
        if 'name' in step:
            print(f"  步骤 {i+1}: {step['name']}")
        
        if 'uses' in step and 'checkout' in step['uses']:
            has_checkout = True
            print(f"    ✅ 找到代码检出步骤: {step['uses']}")
        
        if 'run' in step:
            has_run = True
            run_content = step['run']
            # 检查关键Git命令
            if any(cmd in run_content for cmd in ['git fetch', 'git checkout', 'git reset', 'git push']):
                has_git_commands = True
                print(f"    ✅ 找到包含Git命令的步骤")
                print(f"       包含的命令: {[cmd for cmd in ['git fetch', 'git checkout', 'git reset', 'git push'] if cmd in run_content]}")
    
    # 验证关键配置
    if not has_checkout:
        print(f"⚠️  缺少代码检出步骤")
    
    if not has_run:
        print(f"⚠️  缺少运行命令的步骤")
    
    if not has_git_commands:
        print(f"⚠️  缺少包含Git命令的步骤")
    
    # 检查工作流内容中的关键配置
    content = open(file_path, 'r', encoding='utf-8').read()
    if '${{ github.ref_name }}' in content:
        print(f"✅ 找到正确的GitHub Actions变量语法: ${{ github.ref_name }}")
    elif '${GITHUB_REF_NAME}' in content:
        print(f"⚠️  找到错误的变量语法: ${GITHUB_REF_NAME}")
    else:
        print(f"⚠️  没有找到分支引用变量")
    
    if 'git push' in content:
        print(f"✅ 找到Git推送命令")
    else:
        print(f"⚠️  没有找到Git推送命令")
    
    print(f"\n🎉 基本验证完成")
    return True


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
            print("✅ 工作流基本结构验证通过")
            passed += 1
        else:
            print("❌ 工作流验证失败")
    
    print("\n" + "=" * 50)
    print(f"📊 验证结果: {passed}/{total} 工作流通过基本验证")
    
    if passed == total:
        print("🎉 所有工作流配置的基本结构验证通过！")
        return 0
    else:
        print("⚠️  部分工作流配置需要检查")
        return 1


if __name__ == "__main__":
    exit(main())
