import requests
import json
import os

# 配置参数
workflow_run_id = 20126571513
repo_owner = "wangchongzhq"
repo_name = "TZY"

def main():
    # 获取GitHub Token
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("未找到GITHUB_TOKEN环境变量")
        return
    
    # 设置请求头
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # 获取工作流作业列表
    jobs_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{workflow_run_id}/jobs'
    try:
        response = requests.get(jobs_url, headers=headers, verify=False)
        response.raise_for_status()
        jobs = response.json()
        
        print("工作流作业列表:")
        for job in jobs.get('jobs', []):
            print(f"  作业ID: {job.get('id')}, 名称: {job.get('name')}, 状态: {job.get('status')}, 结论: {job.get('conclusion')}")
            
            # 如果作业已完成，获取日志
            if job.get('status') == 'completed':
                logs_url = job.get('logs_url')
                if logs_url:
                    try:
                        logs_response = requests.get(logs_url, headers=headers, verify=False)
                        logs_response.raise_for_status()
                        logs_content = logs_response.text
                        print(f"    日志内容(前1000字符): {logs_content[:1000]}...")
                    except Exception as e:
                        print(f"    获取日志失败: {e}")
    except Exception as e:
        print(f"获取工作流作业失败: {e}")

if __name__ == "__main__":
    main()