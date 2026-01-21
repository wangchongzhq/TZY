#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPTV验证工具 - 自动化代码校验脚本
在git commit时自动运行，确保代码质量和安全性
"""

import os
import sys
import re
import json
import ast
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple


class CodeValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.project_root = Path(__file__).parent
        self.validator_dir = self.project_root / "validator"
        
    def log_error(self, message: str, file_path: str = "", line: int = 0):
        """记录错误"""
        if file_path and line > 0:
            self.errors.append(f"{file_path}:{line} - {message}")
        else:
            self.errors.append(f"{message}")
            
    def log_warning(self, message: str, file_path: str = "", line: int = 0):
        """记录警告"""
        if file_path and line > 0:
            self.warnings.append(f"{file_path}:{line} - {message}")
        else:
            self.warnings.append(f"{message}")

    def check_python_syntax(self) -> bool:
        """检查Python语法错误"""
        print("检查Python语法错误...")
        
        syntax_ok = True
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    ast.parse(content)
            except SyntaxError as e:
                self.log_error(f"Python语法错误: {e.msg}", str(py_file), e.lineno)
                syntax_ok = False
            except Exception as e:
                self.log_error(f"文件读取错误: {e}", str(py_file))
                syntax_ok = False
                
        if syntax_ok:
            print("Python语法检查通过")
        return syntax_ok

    def check_encoding_declarations(self) -> bool:
        """检查文件编码声明"""
        print("检查文件编码声明...")
        
        encoding_ok = True
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read(200)  # 只检查文件头部
                    
                # 检查是否有编码声明
                if '# -*- coding:' not in content and '# coding:' not in content:
                    self.log_warning(f"建议添加文件编码声明", str(py_file))
                    
            except Exception as e:
                self.log_error(f"编码检查失败: {e}", str(py_file))
                encoding_ok = False
                
        if encoding_ok:
            print("文件编码检查通过")
        return encoding_ok

    def check_security_issues(self) -> bool:
        """检查安全问题"""
        print("检查安全相关问题...")
        
        security_patterns = {
            r'eval\s*\(': '使用eval()函数存在安全风险',
            r'exec\s*\(': '使用exec()函数存在安全风险',
            r'subprocess\.call\s*\([^)]*shell\s*=\s*True': 'shell=True存在安全风险',
            r'os\.system\s*\(': 'os.system()存在安全风险',
            r'pickle\.load\s*\(': 'pickle.load()可能存在反序列化风险',
            r'yaml\.load\s*\([^)]*(?!.*Loader=)': 'yaml.load()需要指定SafeLoader',
        }
        
        security_ok = True
        
        for py_file in self.python_files:
            # 跳过检查自身文件中的安全模式定义
            if py_file.name == 'pre_commit_check.py':
                continue
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for line_num, line in enumerate(lines, 1):
                    for pattern, message in security_patterns.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            # 允许Tkinter的特殊eval用法（执行Tcl命令）
                            if 'eval' in pattern and 'tk::' in line:
                                continue
                            # 允许Tkinter的特殊exec用法
                            if 'exec' in pattern and ('tk::' in line or 'Tcl' in line):
                                continue
                            self.log_error(f"{message}", str(py_file), line_num)
                            security_ok = False
                            
            except Exception as e:
                self.log_error(f"安全检查失败: {e}", str(py_file))
                security_ok = False
                
        if security_ok:
            print("安全检查通过")
        return security_ok

    def check_gui_requirements(self) -> bool:
        """检查GUI应用要求"""
        print("检查GUI应用要求...")
        
        gui_ok = True
        main_gui_files = [
            self.validator_dir / "integrated_validator.py",
            self.validator_dir / "智能启动器.py",
            self.validator_dir / "一键启动.py",
        ]
        
        for gui_file in main_gui_files:
            if gui_file.exists():
                try:
                    with open(gui_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 检查是否正确处理__main__模块
                    if 'if __name__ == "__main__":' not in content:
                        self.log_warning(f"GUI应用缺少main模块检查", str(gui_file))
                        
                    # 检查异常处理
                    if 'except Exception as e:' not in content and 'except:' not in content:
                        self.log_warning(f"GUI应用缺少异常处理", str(gui_file))
                        
                    # 检查资源清理
                    if 'root.destroy()' not in content and 'sys.exit()' not in content:
                        self.log_warning(f"GUI应用建议添加资源清理", str(gui_file))
                        
                except Exception as e:
                    self.log_error(f"GUI检查失败: {e}", str(gui_file))
                    gui_ok = False
                    
        if gui_ok:
            print("GUI应用要求检查通过")
        return gui_ok

    def check_file_handling(self) -> bool:
        """检查文件处理安全性"""
        print("检查文件处理安全性...")
        
        file_ok = True
        
        # 需要检查的文件操作模式
        unsafe_modes = ['w', 'a', 'wb', 'ab']
        safe_modes = ['w+', 'a+', 'x']
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for line_num, line in enumerate(lines, 1):
                    # 检查不安全的文件操作
                    for mode in unsafe_modes:
                        if f'"{mode}"' in line or f"'{mode}'" in line:
                            # 检查是否有异常处理
                            if 'try:' not in ''.join(lines[max(0, line_num-5):line_num+5]):
                                self.log_warning(f"文件操作缺少异常处理", str(py_file), line_num)
                                
                    # 检查路径操作
                    if 'os.path.join' in line and 'os.path.abspath' not in line:
                        self.log_warning(f"建议使用os.path.abspath确保路径安全", str(py_file), line_num)
                        
            except Exception as e:
                self.log_error(f"文件处理检查失败: {e}", str(py_file))
                file_ok = False
                
        if file_ok:
            print("文件处理检查通过")
        return file_ok

    def check_network_requests(self) -> bool:
        """检查网络请求配置"""
        print("检查网络请求配置...")
        
        network_ok = True
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 检查requests使用情况
                if 'requests.' in content:
                    # 检查超时设置
                    if 'timeout=' not in content:
                        self.log_warning(f"网络请求建议设置timeout参数", str(py_file))
                        
                    # 检查SSL验证
                    if 'verify=False' in content:
                        self.log_warning(f"SSL验证被禁用，存在安全风险", str(py_file))
                        
                # 检查URL验证 - 允许IPTV相关的HTTP请求
                if 'http://' in content:
                    # 对于IPTV直播源，HTTP是常见的协议，因此不警告
                    file_name = py_file.name.lower()
                    content_lower = content.lower()
                    is_iptv_related = any(keyword in file_name or keyword in content_lower for keyword in 
                                        ['iptv', 'live', 'm3u', 'stream', 'channel'])
                    
                    if not is_iptv_related and 'https://' not in content:
                        self.log_warning(f"使用HTTP而非HTTPS，可能存在安全风险", str(py_file))
                    
            except Exception as e:
                self.log_error(f"网络请求检查失败: {e}", str(py_file))
                network_ok = False
                
        if network_ok:
            print("网络请求检查通过")
        return network_ok

    def check_logging_completeness(self) -> bool:
        """检查日志记录完整性"""
        print("检查日志记录完整性...")
        
        logging_ok = True
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 检查是否使用logging但缺少重要日志
                if 'import logging' in content or 'from logging' in content:
                    # 检查是否有错误日志
                    if 'logging.error' not in content and 'logger.error' not in content:
                        self.log_warning(f"使用logging但缺少错误日志记录", str(py_file))
                        
                    # 检查是否有异常处理日志
                    if 'except Exception as e:' in content:
                        if 'logging.exception' not in content and 'logger.exception' not in content:
                            self.log_warning(f"异常处理中缺少日志记录", str(py_file))
                            
            except Exception as e:
                self.log_error(f"日志检查失败: {e}", str(py_file))
                logging_ok = False
                
        if logging_ok:
            print("日志记录检查通过")
        return logging_ok

    def check_dependencies(self) -> bool:
        """检查依赖配置"""
        print("检查项目依赖...")
        
        deps_ok = True
        
        # 检查requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    deps = f.read()
                    
                # 检查关键依赖（只检查第三方库，不检查Python标准库）
                required_deps = ['requests']
                missing_deps = []
                
                for dep in required_deps:
                    if dep not in deps.lower():
                        missing_deps.append(dep)
                        
                if missing_deps:
                    self.log_warning(f"requirements.txt缺少依赖: {', '.join(missing_deps)}")
                    
            except Exception as e:
                self.log_error(f"依赖检查失败: {e}", str(req_file))
                deps_ok = False
        else:
            self.log_warning("缺少requirements.txt文件")
            
        if deps_ok:
            print("依赖检查通过")
        return deps_ok

    def check_batch_file_encoding(self) -> bool:
        """检查批处理文件编码"""
        print("检查批处理文件编码...")
        
        batch_ok = True
        batch_files = list(self.project_root.rglob("*.bat"))
        
        for bat_file in batch_files:
            try:
                # 尝试用UTF-8编码读取
                try:
                    with open(bat_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        encoding = 'utf-8'
                except UnicodeDecodeError:
                    # 如果UTF-8失败，尝试用GBK编码
                    try:
                        with open(bat_file, 'r', encoding='gbk') as f:
                            content = f.read()
                            encoding = 'gbk'
                    except UnicodeDecodeError:
                        # 如果GBK也失败，跳过这个文件
                        continue
                
                # 检查是否正确设置编码
                if 'chcp 936' not in content and 'chcp 65001' not in content:
                    self.log_warning(f"批处理文件建议设置编码", str(bat_file))
                    
                # 检查是否有中文字符可能导致编码问题
                if re.search(r'[^\x00-\x7F]', content):
                    if encoding == 'gbk' and 'chcp 936' not in content:
                        self.log_warning(f"包含中文字符但未设置GBK编码", str(bat_file))
                    elif encoding == 'utf-8' and 'chcp 65001' not in content:
                        self.log_warning(f"包含中文字符但未设置UTF-8编码", str(bat_file))
                        
            except Exception as e:
                # 忽略批处理文件编码错误，因为这不是严重问题
                self.log_warning(f"批处理文件检查失败: {e}", str(bat_file))
                
        print("批处理文件检查通过")
        return True

    def check_git_configuration(self) -> bool:
        """检查Git配置完整性"""
        print("检查Git配置...")
        
        git_ok = True
        
        # 检查.gitignore
        gitignore_file = self.project_root / ".gitignore"
        if gitignore_file.exists():
            try:
                with open(gitignore_file, 'r', encoding='utf-8') as f:
                    gitignore_content = f.read()
                    
                # 检查必要的忽略规则
                required_ignores = ['*.pyc', '__pycache__', 'dist/', 'build/']
                missing_ignores = []
                
                for ignore in required_ignores:
                    if ignore not in gitignore_content:
                        missing_ignores.append(ignore)
                        
                if missing_ignores:
                    self.log_warning(f".gitignore缺少规则: {', '.join(missing_ignores)}")
                    
            except Exception as e:
                self.log_error(f"Git配置检查失败: {e}", str(gitignore_file))
                git_ok = False
        else:
            self.log_warning("缺少.gitignore文件")
            
        # 检查Git hooks
        hooks_dir = self.project_root / ".git" / "hooks"
        if hooks_dir.exists():
            pre_commit = hooks_dir / "pre-commit"
            if not pre_commit.exists():
                self.log_warning("建议设置pre-commit hook")
        else:
            self.log_warning("Git仓库未初始化或hooks目录不存在")
            
        if git_ok:
            print("Git配置检查通过")
        return git_ok

    def generate_report(self) -> bool:
        """生成检查报告"""
        print("\n" + "="*60)
        print("代码质量检查报告")
        print("="*60)
        
        if self.errors:
            print("\n错误 (必须修复):")
            for error in self.errors:
                print(f"  {error}")
                
        if self.warnings:
            print("\n警告 (建议修复):")
            for warning in self.warnings:
                print(f"  {warning}")
                
        print(f"\n检查统计:")
        print(f"  错误: {len(self.errors)}")
        print(f"  警告: {len(self.warnings)}")
        
        if self.errors:
            print("\n检查失败 - 发现严重问题")
            return False
        elif self.warnings:
            print("\n检查通过但有建议 - 可以提交")
            return True
        else:
            print("\n检查完全通过 - 代码质量良好")
            return True

    def run_all_checks(self) -> bool:
        """运行所有检查"""
        print("开始IPTV验证工具代码质量检查")
        print("="*60)
        
        # 只检查核心文件和目录，提高检查效率
        self.python_files = []
        core_directories = ['validator']
        core_files = ['IPTV.py', 'IPTVTXT.py', 'convert_m3u_to_txt.py', 'file_utils.py', 'pre_commit_check.py']
        
        # 添加核心文件
        for file in core_files:
            file_path = self.project_root / file
            if file_path.exists():
                self.python_files.append(file_path)
        
        # 添加核心目录下的文件
        for directory in core_directories:
            dir_path = self.project_root / directory
            if dir_path.exists():
                self.python_files.extend(list(dir_path.rglob("*.py")))
        
        # 去重
        self.python_files = list(set(self.python_files))
        
        checks = [
            self.check_python_syntax,
            self.check_encoding_declarations,
            self.check_security_issues,
            self.check_gui_requirements,
            self.check_file_handling,
            self.check_network_requests,
            self.check_logging_completeness,
            self.check_dependencies,
            self.check_batch_file_encoding,
            self.check_git_configuration,
        ]
        
        all_passed = True
        for check in checks:
            try:
                result = check()
                if not result and check.__name__ in [
                    'check_python_syntax', 
                    'check_security_issues'
                ]:
                    all_passed = False
            except Exception as e:
                self.log_error(f"检查 {check.__name__} 执行失败: {e}")
                all_passed = False
                
        return self.generate_report() and all_passed


def main():
    """主函数"""
    validator = CodeValidator()
    
    try:
        success = validator.run_all_checks()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断检查")
        sys.exit(1)
    except Exception as e:
        print(f"\n检查过程中发生异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()