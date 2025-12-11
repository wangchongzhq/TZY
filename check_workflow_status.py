#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import os
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 忽略SSL证书验证警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_workflow_status():
    # 配置参数
    repo_owner = "wangchongzhq"
    repo_name = "TZY"
    workflow_id = "mainzy.yml"
    
    # 构建API URL
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_id}/runs"
    
    # 设置请求头
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 尝试获取GitHub Token
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        # 发送请求
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"API响应状态码: {response.status_code}")
        print(f"API响应头: {json.dumps(dict(response.headers), indent=2)}")
        response.raise_for_status()
        
        # 解析响应
        runs = response.json()
        print(f"工作流运行总数: {len(runs.get('workflow_runs', []))}")
        
        if not runs.get("workflow_runs"):
            print("没有找到工作流运行记录")
            return None
        
        # 获取最新的工作流运行
        latest_run = runs["workflow_runs"][0]
        print(f"工作流ID: {latest_run.get('id')}")
        print(f"状态: {latest_run.get('status')}")
        print(f"结论: {latest_run.get('conclusion')}")
        print(f"创建时间: {latest_run.get('created_at')}")
        print(f"更新时间: {latest_run.get('updated_at')}")
        print(f"日志URL: {latest_run.get('html_url')}")
        return latest_run
    except Exception as e:
        print(f"获取工作流状态失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("检查GitHub Actions工作流状态")
    print("==================================================")
    
    # 最多尝试5次
    for i in range(1, 6):
        print(f"\n尝试 {i}/5:")
        
        # 获取工作流状态
        workflow_run = get_workflow_status()
        
        if workflow_run:
            # 打印详细的工作流信息
            print(f"触发事件: {workflow_run.get('event')}")
            print(f"提交SHA: {workflow_run.get('head_sha')}")
            print(f"分支: {workflow_run.get('head_branch')}")
            print(f"触发者: {workflow_run.get('actor', {}).get('login')}")
            
            # 检查工作流是否已完成
            if workflow_run.get('status') == "completed":
                print(f"\n工作流已完成，结论: {workflow_run.get('conclusion')}")
                return workflow_run.get('conclusion') == "success"
        else:
            print("未找到工作流运行信息")
        
        # 等待5秒后再次检查
        if i < 5:
            print("工作流正在运行或未开始，等待5秒后再次检查...")
            time.sleep(5)
    
    print("\n超过最大尝试次数，工作流仍在运行中")
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)