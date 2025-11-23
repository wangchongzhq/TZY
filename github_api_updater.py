#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub API文件更新器
用于通过GitHub API直接更新文件，避免git push操作带来的冲突问题
"""

import os
import sys
import base64
import time
import json
import random
import logging
import requests
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("github_api_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GitHubAPIUpdater:
    def __init__(self, token, repo_owner, repo_name, branch="main", api_version="2022-11-28"):
        """初始化GitHub API更新器"""
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.api_version = api_version
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.api_version,
            "User-Agent": "GitHub-Actions-Tvzy-Update-Script"
        }
        
        # 验证必要参数
        if not self.token:
            raise ValueError("GitHub token cannot be empty")
        if not self.repo_owner or not self.repo_name:
            raise ValueError("Repository owner and name cannot be empty")
    
    def get_file_sha(self, file_path, max_retries=3):
        """
        获取文件的当前SHA
        如果文件不存在，返回None
        """
        endpoint = f"/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}?ref={self.branch}"
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Attempt {attempt}/{max_retries}: Getting SHA for file {file_path}")
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=15,
                    allow_redirects=True
                )
                
                # 记录HTTP状态码
                logger.info(f"HTTP Status Code: {response.status_code}")
                
                # 文件存在
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "sha" in data:
                            sha = data["sha"]
                            logger.info(f"Successfully got SHA for {file_path}: {sha[:7]}...")
                            return sha
                        else:
                            logger.warning(f"SHA not found in response for {file_path}")
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON response for {file_path}")
                        logger.debug(f"Response content: {response.text[:200]}...")
                
                # 文件不存在
                elif response.status_code == 404:
                    logger.info(f"File {file_path} does not exist, will create new file")
                    return None
                
                # 处理其他错误
                else:
                    logger.error(f"Failed to get SHA for {file_path}, HTTP {response.status_code}")
                    logger.debug(f"Response content: {response.text[:200]}...")
                    
                    # 处理特定错误
                    if response.status_code == 401:
                        logger.error("Authentication failed, check your GitHub token")
                        return None
                    elif response.status_code == 403:
                        logger.error("API rate limit or insufficient permissions (403)")
                        if "X-RateLimit-Reset" in response.headers:
                            reset_time = response.headers["X-RateLimit-Reset"]
                            logger.info(f"Rate limit resets at: {reset_time}")
                
            except requests.RequestException as e:
                logger.error(f"Request exception while getting SHA for {file_path}: {str(e)}")
            
            # 重试逻辑
            if attempt < max_retries:
                wait_time = attempt * 3  # 线性退避
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            
        logger.warning(f"All attempts to get SHA for {file_path} failed")
        return None
    
    def encode_file(self, file_path):
        """将文件编码为base64"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"File {file_path} does not exist")
                return None
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            logger.info(f"File {file_path} size: {file_size} bytes")
            
            # 检查文件是否为空
            if file_size == 0:
                logger.error(f"File {file_path} is empty")
                return None
            
            # 编码文件
            with open(file_path, 'rb') as f:
                content = f.read()
            encoded = base64.b64encode(content).decode('utf-8')
            logger.info(f"Successfully encoded {file_path} to base64, length: {len(encoded)} characters")
            return encoded
            
        except Exception as e:
            logger.error(f"Failed to encode file {file_path}: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def upload_file(self, file_path, commit_message=None, max_retries=5, base_delay=2):
        """
        上传文件到GitHub仓库
        使用增强的指数退避策略和智能冲突检测进行重试
        
        Args:
            file_path (str): 要上传的文件路径
            commit_message (str): 提交信息
            max_retries (int): 最大重试次数
            base_delay (int): 基础延迟时间（秒）
            
        Returns:
            bool: 是否上传成功
        """
        endpoint = f"/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
        url = f"{self.base_url}{endpoint}"
        
        # 编码文件
        encoded_content = self.encode_file(file_path)
        if not encoded_content:
            logger.critical(f"Failed to encode file {file_path}, aborting upload")
            return False
        
        # 生成提交消息
        if not commit_message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"自动更新: {file_path} ({timestamp})"
        
        logger.info(f"🔄 Preparing to upload {file_path} with commit message: {commit_message}")
        logger.info(f"⚡ Using enhanced conflict detection and smart retry strategy")
        
        last_conflict_time = None
        conflict_count = 0
        
        for attempt in range(1, max_retries + 1):
            try:
                # 获取最新SHA（在每次尝试前重新获取以避免冲突）
                current_sha = self.get_file_sha(file_path, max_retries=3)
                if current_sha:
                    logger.info(f"🔍 Retrieved latest SHA: {current_sha[:7]}...")
                else:
                    logger.info(f"📄 Will create new file: {file_path}")
                
                # 构建请求数据
                data = {
                    "message": commit_message,
                    "content": encoded_content,
                    "branch": self.branch
                }
                
                # 如果文件已存在，添加SHA（乐观并发控制）
                if current_sha:
                    data["sha"] = current_sha
                    logger.info(f"📝 Updating existing file with SHA-based optimistic concurrency control")
                
                # 发送请求
                logger.info(f"🚀 Attempt {attempt}/{max_retries}: Sending PUT request to update file")
                response = requests.put(
                    url,
                    headers=self.headers,
                    json=data,
                    timeout=60,
                    allow_redirects=True
                )
                
                # 记录HTTP状态码
                logger.info(f"📊 HTTP Status Code: {response.status_code}")
                
                # 成功处理
                if response.status_code in [200, 201]:
                    try:
                        result = response.json()
                        if "commit" in result:
                            commit_url = result["commit"].get("html_url", "")
                            if commit_url:
                                logger.info(f"🎉 Successfully updated file! Commit URL: {commit_url}")
                                logger.info(f"✅ Optimistic concurrency control succeeded with SHA: {current_sha[:7]}...")
                            else:
                                logger.info("🎉 Successfully updated file!")
                            return True
                        else:
                            logger.warning("⚠️ No commit information in response, but HTTP status is success")
                            return True
                    except json.JSONDecodeError:
                        logger.error("❌ Failed to parse JSON response, but HTTP status is success")
                        return True
                
                # 错误处理
                else:
                    logger.error(f"❌ Failed to update file, HTTP {response.status_code}")
                    
                    # 尝试解析错误信息
                    try:
                        error_data = response.json()
                        error_message = error_data.get("message", "")
                        logger.error(f"💬 Error message: {error_message}")
                        
                        # 增强的冲突检测
                        is_conflict = self._is_conflict_error(response, error_message)
                        
                        if is_conflict:
                            conflict_count += 1
                            current_time = time.time()
                            
                            # 记录冲突信息
                            logger.warning(f"⚠️ Version conflict detected! This is attempt #{conflict_count} to resolve")
                            logger.warning("🔄 Will immediately retry with fresh SHA to resolve conflict")
                            
                            # 如果短时间内冲突频繁，增加一个小延迟避免立即重试风暴
                            if last_conflict_time and (current_time - last_conflict_time) < 2:
                                small_delay = random.uniform(0.5, 1.5)
                                logger.info(f"⏱️  Adding small delay ({small_delay:.2f}s) to avoid retry storm")
                                time.sleep(small_delay)
                            
                            last_conflict_time = current_time
                            # 不等待，立即重试以获取最新SHA
                            continue
                            
                    except json.JSONDecodeError:
                        logger.debug(f"📋 Response content: {response.text[:200]}...")
                    
                    # 处理特定错误
                    if response.status_code == 401:
                        logger.error("🚫 Authentication failed, check your GitHub token")
                        logger.error("💡 Tip: Ensure the token has 'contents' write permission")
                        return False
                    elif response.status_code == 403:
                        logger.error("🚫 API rate limit or insufficient permissions (403)")
                        if "X-RateLimit-Reset" in response.headers:
                            reset_time = int(response.headers["X-RateLimit-Reset"])
                            wait_time = max(1, reset_time - int(time.time()))
                            logger.info(f"⏱️  Rate limit resets in {wait_time} seconds")
                            if attempt < max_retries and wait_time < 30:  # 只在等待时间合理时才等待
                                logger.info(f"⏳ Waiting {wait_time} seconds for rate limit reset")
                                time.sleep(wait_time)
                    elif response.status_code >= 500:
                        logger.error(f"🌐 GitHub server error ({response.status_code})")
                        logger.info("💡 This is likely temporary, will retry with exponential backoff")
                    elif response.status_code == 404:
                        if current_sha:  # 如果之前能获取到SHA但现在404，说明仓库或分支可能被删除
                            logger.error("❌ Repository or branch not found")
                            return False
                        else:
                            logger.warning("⚠️ File not found, will create new file")
                    else:
                        logger.error(f"❓ Unexpected error code: {response.status_code}")
            
            except requests.RequestException as e:
                logger.error(f"🌐 Request exception while uploading {file_path}: {str(e)}")
                # 网络相关错误应该进行重试
                if "Connection refused" in str(e) or "Connection reset" in str(e):
                    logger.info("💡 Network connection error detected, will retry with backoff")
            except Exception as e:
                logger.error(f"❓ Unexpected error while uploading {file_path}: {str(e)}")
                import traceback
                logger.debug(traceback.format_exc())
            
            # 指数退避策略 - 增强版
            if attempt < max_retries:
                # 计算基础退避时间
                delay = base_delay * (2 ** (attempt - 1))
                
                # 根据错误类型调整退避时间
                if conflict_count > 0:
                    # 冲突场景，使用较短但稳定的退避
                    delay = min(delay, 10)  # 限制最大延迟
                    logger.info(f"🔄 Conflict scenario detected, using optimized backoff")
                elif "403" in str(locals().get('response', '')):
                    # 速率限制场景，使用较长退避
                    delay = delay * 1.5
                    logger.info(f"⏱️  Rate limit scenario detected, using extended backoff")
                elif "500" in str(locals().get('response', '')):
                    # 服务器错误场景，使用较长退避
                    delay = delay * 1.2
                    logger.info(f"🌐 Server error scenario detected, using increased backoff")
                
                # 添加智能随机抖动（5%-25%）
                jitter_percent = random.uniform(0.05, 0.25)
                jitter = delay * jitter_percent
                if random.choice([True, False]):
                    delay += jitter
                else:
                    delay = max(1, delay - jitter)
                
                # 限制最大延迟为60秒
                delay = min(delay, 60)
                
                logger.info(f"⏱️  Waiting {delay:.2f} seconds before retry (attempt {attempt+1}/{max_retries})...")
                time.sleep(delay)
        
        logger.error(f"❌ All {max_retries} attempts to upload {file_path} failed")
        logger.error(f"💡 Troubleshooting suggestions:")
        logger.error(f"   1. Check GitHub API permissions and token validity")
        logger.error(f"   2. Verify repository exists and branch is correct")
        logger.error(f"   3. Check if file is being modified by another process concurrently")
        logger.error(f"   4. Increase max_retries or base_delay for more robust retry behavior")
        return False
    
    def _is_conflict_error(self, response, error_message):
        """
        增强的冲突错误检测
        
        Args:
            response: HTTP响应对象
            error_message: 错误消息文本
            
        Returns:
            bool: 是否为冲突错误
        """
        # 检查HTTP状态码
        if response.status_code == 409:
            return True
            
        # 检查错误消息中的关键词
        error_lower = error_message.lower()
        conflict_keywords = [
            'sha', 'conflict', 'modified', 'update', 
            'version', 'stale', 'different', 'changed'
        ]
        
        for keyword in conflict_keywords:
            if keyword in error_lower:
                return True
                
        return False

# 命令行接口
def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Update files on GitHub using GitHub API with advanced conflict detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        高级功能说明:
        - 使用基于SHA的乐观并发控制机制避免更新冲突
        - 智能指数退避重试策略，针对不同错误类型优化延迟时间
        - 增强的冲突检测算法，能准确识别各种冲突场景
        - 详细的日志记录和故障排除建议
        - 完全避免Git Push操作，解决持续集成中的冲突问题
        """)
    
    parser.add_argument('--token', required=True, help='GitHub personal access token')
    parser.add_argument('--owner', required=True, help='Repository owner')
    parser.add_argument('--repo', required=True, help='Repository name')
    parser.add_argument('--file', required=True, help='Path to file to upload')
    parser.add_argument('--branch', default='main', help='Target branch (default: main)')
    parser.add_argument('--message', help='Commit message (optional)')
    parser.add_argument('--dry-run', action='store_true', help='Simulate upload without actual API calls')
    parser.add_argument('--max-retries', type=int, default=5, help='Maximum number of retry attempts (default: 5)')
    parser.add_argument('--base-delay', type=float, default=2, help='Base delay in seconds for exponential backoff (default: 2)')
    
    args = parser.parse_args()
    
    # 打印启动信息
    logger.info("🚀 GitHub API文件更新器启动")
    logger.info("🔄 基于SHA的乐观并发控制和智能重试策略")
    logger.info("✅ 完全避免Git Push冲突的解决方案")
    
    # 模拟模式
    if args.dry_run:
        logger.info("🧪 Dry run mode enabled - no actual API calls will be made")
        logger.info(f"📄 Would upload file: {args.file}")
        logger.info(f"📦 Target repository: {args.owner}/{args.repo}@{args.branch}")
        logger.info(f"📝 Commit message: {args.message or 'Auto-generated'}")
        logger.info(f"🔧 Retry configuration: {args.max_retries} retries, {args.base_delay}s base delay")
        
        # 检查文件是否存在
        if not os.path.exists(args.file):
            logger.error(f"❌ File {args.file} does not exist")
            return 1
        
        # 检查文件大小
        file_size = os.path.getsize(args.file)
        logger.info(f"📊 File size: {file_size} bytes")
        
        # 测试文件编码
        try:
            with open(args.file, 'rb') as f:
                content = f.read(1024)  # 只读取前1KB进行测试
            logger.info(f"🔍 Successfully read file content sample")
        except Exception as e:
            logger.error(f"❌ Failed to read file content: {str(e)}")
            return 1
        
        logger.info("✅ Dry run completed successfully")
        return 0
    
    # 实际执行
    try:
        # 打印详细配置信息
        logger.info(f"📋 Configuration:")
        logger.info(f"  - Repository: {args.owner}/{args.repo}@{args.branch}")
        logger.info(f"  - File: {args.file}")
        logger.info(f"  - Commit message: {args.message or 'Auto-generated'}")
        logger.info(f"  - Retry strategy: {args.max_retries} retries, {args.base_delay}s base delay")
        
        # 创建更新器实例
            updater = GitHubAPIUpdater(
                token=args.token,
                repo_owner=args.owner,
                repo_name=args.repo,
                branch=args.branch,
                mutual_exclusion=not args.no_mutex,
                workflow_name=args.workflow_name or os.environ.get('GITHUB_WORKFLOW')
            )
        
        # 执行文件更新
        logger.info(f"🔄 Starting file upload process...")
        start_time = time.time()
        
        success = updater.upload_file(
            file_path=args.file,
            commit_message=args.message,
            max_retries=args.max_retries,
            base_delay=args.base_delay
        )
        
        # 计算执行时间
        execution_time = time.time() - start_time
        logger.info(f"⏱️  Execution time: {execution_time:.2f} seconds")
        
        # 返回结果
        if success:
            logger.info("🎉 GitHub API文件更新成功完成！")
            logger.info("✅ 基于SHA的乐观并发控制机制成功避免了冲突")
            logger.info("🎯 任务完成，退出状态码: 0")
            return 0
        else:
            logger.error("❌ GitHub API文件更新失败！")
            logger.error("💡 故障排除建议:")
            logger.error("  1. 检查GitHub API权限和token有效性")
            logger.error("  2. 验证仓库存在且分支正确")
            logger.error("  3. 检查是否有其他进程正在修改同一文件")
            logger.error("  4. 检查网络连接和GitHub API状态")
            logger.error("  5. 尝试增加--max-retries或--base-delay参数值")
            logger.error("🎯 任务失败，退出状态码: 1")
            return 1
            
    except ValueError as e:
        logger.error(f"❌ 参数验证错误: {str(e)}")
        return 2
    except Exception as e:
        logger.error(f"❌ 主程序执行异常: {str(e)}")
        import traceback
        logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
