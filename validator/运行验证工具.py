#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源验证工具 - 独立启动器
直接运行此文件即可启动验证工具，无需安装额外依赖
"""

import os
import sys
import subprocess
import locale
import codecs

# 设置控制台编码为UTF-8
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    ctypes.windll.kernel32.SetConsoleCP(65001)

# 设置标准输出编码
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def main():
    """主函数"""
    print("=" * 60)
    print("    直播源验证工具启动器")
    print("=" * 60)
    print()
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查Python版本和编码设置
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"系统编码: {sys.getdefaultencoding()}")
    print(f"文件编码: {locale.getpreferredencoding()}")
    print()
    
    # 检查集成验证器文件
    validator_file = os.path.join(current_dir, "integrated_validator.py")
    if not os.path.exists(validator_file):
        print("✗ 错误: 未找到 integrated_validator.py")
        print(f"预期位置: {validator_file}")
        input("按回车键退出...")
        return
    
    print("✓ 找到验证器文件")
    print()
    
    # 检查依赖
    print("正在检查依赖...")
    missing_deps = []
    
    try:
        import tkinter
        print("✓ tkinter - GUI框架")
    except ImportError:
        missing_deps.append("tkinter")
        print("✗ tkinter - GUI框架")
    
    try:
        import requests
        print("✓ requests - HTTP请求库")
    except ImportError:
        missing_deps.append("requests")
        print("✗ requests - HTTP请求库")
    
    try:
        import ffmpeg
        print("✓ ffmpeg-python - 媒体信息提取")
    except ImportError:
        print("ℹ ffmpeg-python - 媒体信息提取 (可选)")
    
    try:
        import subprocess
        print("✓ subprocess - 系统调用")
    except ImportError:
        missing_deps.append("subprocess")
        print("✗ subprocess - 系统调用")
    
    if missing_deps:
        print()
        print("⚠  缺少以下依赖:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print()
        print("尝试安装缺少的依赖...")
        
        # 尝试安装依赖
        for dep in missing_deps:
            try:
                print(f"正在安装 {dep}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                print(f"✓ {dep} 安装成功")
            except subprocess.CalledProcessError:
                print(f"✗ {dep} 安装失败")
    
    print()
    print("正在启动验证工具...")
    print("-" * 40)
    
    try:
        # 启动验证器
        try:
            subprocess.run([sys.executable, validator_file], check=False)
        except Exception as e:
            print(f"启动失败: {e}")
        print("-" * 40)
        print("✓ 验证工具已退出")
    except Exception as e:
        print(f"✗ 启动失败: {e}")
    
    print()
    print("按回车键退出...")
    input()

if __name__ == "__main__":
    main()