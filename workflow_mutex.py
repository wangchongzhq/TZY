#!/usr/bin/env python3
"""
工作流互斥锁脚本 - 防止多个工作流同时执行

此脚本通过GitHub Actions API检查指定工作流的运行状态，并实现互斥锁机制，确保在任意时刻
只有一个工作流实例在运行，从而避免Git推送冲突和'fetch first'错误。

使用方法:
  python workflow_mutex.py --owner <owner> --repo <repo> --workflow <workflow_name> --token <github_token> [--timeout <seconds>] [--wait]
"""

import os
import sys
import time
import argparse
import requests
import logging
import uuid
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('workflow_mutex.log')
    ]
)
logger = logging.getLogger('workflow_mutex')

class WorkflowMutex:
    """
    工作流互斥锁管理器，使用GitHub Actions API管理工作流运行
    """
    
    def __init__(self, owner, repo, workflow_name, token, timeout=300):
        self.owner = owner
        self.repo = repo
        self.workflow_name = workflow_name
        self.token = token
        self.timeout = timeout
        self.api_base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Workflow-Mutex'
        }
        self.run_id = os.environ.get('GITHUB_RUN_ID', f'manual-{uuid.uuid4()}')
        
    def get_workflow_id(self):
        """
        获取工作流ID
        """
        try:
            url = f"{self.api_base_url}/actions/workflows"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            workflows = response.json().get('workflows', [])
            for workflow in workflows:
                if workflow['name'] == self.workflow_name:
                    logger.info(f"找到工作流 '{self.workflow_name}'，ID: {workflow['id']}")
                    return workflow['id']
            
            logger.error(f"未找到工作流: {self.workflow_name}")
            return None
        except Exception as e:
            logger.error(f"获取工作流ID失败: {str(e)}")
            return None
    
    def get_running_workflows(self, workflow_id):
        """
        获取正在运行的工作流实例
        """
        try:
            url = f"{self.api_base_url}/actions/workflows/{workflow_id}/runs?status=in_progress"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            runs = response.json().get('workflow_runs', [])
            # 过滤掉当前运行实例和已超时的运行
            current_time = datetime.now().timestamp()
            running_runs = []
            
            for run in runs:
                # 跳过当前运行实例
                if str(run['id']) == str(self.run_id):
                    continue
                
                # 检查是否超时（超过指定秒数仍在运行）
                created_at = datetime.strptime(run['created_at'], '%Y-%m-%dT%H:%M:%SZ').timestamp()
                if current_time - created_at > self.timeout:
                    logger.warning(f"检测到超时运行: {run['id']} (创建于 {run['created_at']})")
                    continue
                
                running_runs.append(run)
            
            return running_runs
        except Exception as e:
            logger.error(f"获取运行中工作流失败: {str(e)}")
            return []
    
    def get_other_workflow_runs(self):
        """
        获取所有可能冲突的其他工作流运行
        这里假设可能有其他工作流也在操作相同的文件
        """
        try:
            # 获取所有工作流名称（用于冲突检测）
            workflow_names_to_check = ['TVZY Daily Update', 'TVZY Daily Update API']
            
            conflicting_runs = []
            
            for wf_name in workflow_names_to_check:
                if wf_name == self.workflow_name:
                    continue
                    
                wf_id = self._get_workflow_id_by_name(wf_name)
                if wf_id:
                    url = f"{self.api_base_url}/actions/workflows/{wf_id}/runs?status=in_progress"
                    response = requests.get(url, headers=self.headers)
                    response.raise_for_status()
                    
                    runs = response.json().get('workflow_runs', [])
                    conflicting_runs.extend(runs)
            
            return conflicting_runs
        except Exception as e:
            logger.error(f"检查冲突工作流失败: {str(e)}")
            return []
    
    def _get_workflow_id_by_name(self, workflow_name):
        """
        辅助方法：通过名称获取工作流ID
        """
        try:
            url = f"{self.api_base_url}/actions/workflows"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            workflows = response.json().get('workflows', [])
            for workflow in workflows:
                if workflow['name'] == workflow_name:
                    return workflow['id']
            
            return None
        except Exception:
            return None
    
    def acquire_lock(self, wait=False, max_wait_time=300):
        """
        获取互斥锁
        
        Args:
            wait: 是否等待其他工作流完成
            max_wait_time: 最大等待时间（秒）
            
        Returns:
            bool: 是否成功获取锁
        """
        start_time = time.time()
        
        while True:
            # 获取工作流ID
            workflow_id = self.get_workflow_id()
            if not workflow_id:
                logger.error("无法获取工作流ID，无法继续互斥检查")
                return False
            
            # 检查同工作流的其他运行实例
            running_instances = self.get_running_workflows(workflow_id)
            
            # 检查其他可能冲突的工作流
            conflicting_runs = self.get_other_workflow_runs()
            
            # 合并所有冲突的运行
            all_conflicts = running_instances + conflicting_runs
            
            if not all_conflicts:
                # 没有冲突，成功获取锁
                logger.info(f"✅ 成功获取工作流互斥锁: {self.workflow_name}")
                self._write_lock_info()
                return True
            
            # 有冲突
            conflict_count = len(all_conflicts)
            logger.warning(f"⚠️  检测到 {conflict_count} 个冲突的工作流运行")
            
            for run in all_conflicts:
                run_name = run.get('name', 'Unknown Workflow')
                run_id = run.get('id', 'Unknown ID')
                run_status = run.get('status', 'Unknown Status')
                run_created = run.get('created_at', 'Unknown Time')
                logger.warning(f"  - 工作流: {run_name} (ID: {run_id}, 状态: {run_status}, 创建于: {run_created})")
            
            # 检查是否等待
            if not wait:
                logger.error("❌ 检测到冲突工作流，未配置等待，互斥锁获取失败")
                return False
            
            # 检查是否超过最大等待时间
            if time.time() - start_time > max_wait_time:
                logger.error(f"❌ 等待互斥锁超时 ({max_wait_time}秒)")
                return False
            
            # 等待一段时间后重试
            wait_time = 5  # 每5秒检查一次
            logger.info(f"🔄 等待 {wait_time} 秒后重试互斥锁检查...")
            time.sleep(wait_time)
    
    def _write_lock_info(self):
        """
        写入锁信息到文件，用于调试和跟踪
        """
        try:
            lock_info = {
                'workflow_name': self.workflow_name,
                'run_id': self.run_id,
                'acquired_at': datetime.now().isoformat(),
                'owner': self.owner,
                'repo': self.repo
            }
            
            with open('workflow_lock_info.json', 'w', encoding='utf-8') as f:
                import json
                json.dump(lock_info, f, indent=2, ensure_ascii=False)
                
            logger.info("互斥锁信息已保存到 workflow_lock_info.json")
        except Exception as e:
            logger.warning(f"保存锁信息失败: {str(e)}")
    
    def check_and_wait(self, interval=5, max_attempts=10):
        """
        检查并等待其他工作流完成，返回是否成功
        """
        logger.info(f"开始检查并等待可能的冲突工作流...")
        
        for attempt in range(max_attempts):
            if self.acquire_lock(wait=False):
                return True
                
            logger.info(f"尝试 {attempt + 1}/{max_attempts}: 冲突工作流仍在运行，等待 {interval} 秒...")
            time.sleep(interval)
        
        logger.error(f"已达到最大尝试次数 ({max_attempts})，冲突工作流仍在运行")
        return False
    
    def use_fallback_strategy(self):
        """
        使用备选策略：通过GitHub API直接更新文件，避免Git冲突
        """
        logger.info("启用备选策略：使用GitHub API进行文件更新")
        
        # 创建标记文件，表示使用了备选策略
        try:
            with open('used_api_fallback.txt', 'w') as f:
                f.write(f"API fallback used at: {datetime.now().isoformat()}\n")
                f.write(f"Workflow: {self.workflow_name}\n")
                f.write(f"Run ID: {self.run_id}\n")
            
            logger.info("已创建API备选策略标记文件")
            return True
        except Exception as e:
            logger.error(f"创建API备选策略标记失败: {str(e)}")
            return False

def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='GitHub Actions工作流互斥锁')
    parser.add_argument('--owner', required=True, help='GitHub仓库所有者')
    parser.add_argument('--repo', required=True, help='GitHub仓库名称')
    parser.add_argument('--workflow', required=True, help='工作流名称')
    parser.add_argument('--token', required=True, help='GitHub访问令牌')
    parser.add_argument('--timeout', type=int, default=300, help='工作流运行超时时间（秒）')
    parser.add_argument('--wait', action='store_true', help='是否等待其他工作流完成')
    parser.add_argument('--max-wait', type=int, default=300, help='最大等待时间（秒）')
    parser.add_argument('--fallback', action='store_true', help='在无法获取锁时使用备选策略')
    
    return parser.parse_args()

def main():
    """
    主函数
    """
    try:
        args = parse_args()
        
        # 创建互斥锁管理器
        mutex = WorkflowMutex(
            owner=args.owner,
            repo=args.repo,
            workflow_name=args.workflow,
            token=args.token,
            timeout=args.timeout
        )
        
        logger.info(f"开始工作流互斥检查: {args.workflow}")
        
        # 尝试获取锁
        if mutex.acquire_lock(wait=args.wait, max_wait_time=args.max_wait):
            logger.info("互斥锁获取成功，工作流可以继续执行")
            # 输出成功信息，供CI环境使用
            print("::set-output name=mutex_acquired::true")
            print("MUTEX_ACQUIRED=true")
            return 0
        else:
            # 锁获取失败
            logger.error("无法获取互斥锁")
            
            # 检查是否使用备选策略
            if args.fallback:
                if mutex.use_fallback_strategy():
                    logger.warning("已启用备选API更新策略")
                    print("::set-output name=mutex_fallback_used::true")
                    print("MUTEX_FALLBACK_USED=true")
                    return 0
                else:
                    logger.error("备选策略也失败")
            
            # 输出失败信息
            print("::set-output name=mutex_acquired::false")
            print("MUTEX_ACQUIRED=false")
            return 1
            
    except Exception as e:
        logger.error(f"工作流互斥检查发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
