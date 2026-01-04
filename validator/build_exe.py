#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源验证工具EXE打包脚本
自动构建单文件EXE应用程序
"""

import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path

def check_pyinstaller():
    """检查PyInstaller是否安装"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller已安装: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("✗ PyInstaller未安装")
        return False

def install_pyinstaller():
    """安装PyInstaller"""
    print("正在安装PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ PyInstaller安装失败: {e}")
        return False

def check_dependencies():
    """检查必需的依赖项"""
    dependencies = [
        'tkinter',
        'requests',
        'threading',
        'json',
        'tempfile',
        'logging',
        'datetime'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print(f"缺少依赖项: {missing}")
        return False
    else:
        print("✓ 所有必需依赖项已满足")
        return True

def create_spec_file():
    """创建PyInstaller spec文件"""
    # 获取当前目录的绝对路径
    current_dir = os.path.abspath('.')
    parent_dir = os.path.abspath('..')
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['integrated_validator.py'],
    pathex=['{current_dir}'],
    binaries=[],
    datas=[
        # 包含上级目录中的重要文件
        ('{parent_dir}/quick_url_checker.py', '.'),
        ('{parent_dir}/config_manager.py', '.'),
        ('{parent_dir}/url_validator.py', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        'quick_url_checker',
        'config_manager', 
        'url_validator',
        'threading',
        'concurrent.futures',
        'json',
        'tempfile',
        'logging',
        'datetime',
        'collections.defaultdict',
        'socket',
        'dns.resolver',
        're',
        'os',
        'sys',
        'time'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='直播源验证工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version_file=None,
)
'''
    
    with open('validator_exe.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✓ 已创建spec文件: validator_exe.spec")

def build_exe():
    """构建EXE文件"""
    print("开始构建EXE文件...")
    
    try:
        # 使用spec文件构建
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--windowed", 
            "--name", "直播源验证工具",
            "--distpath", "dist",
            "--workpath", "build",
            "--specpath", ".",
            "integrated_validator.py"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✓ EXE构建成功")
            print("输出位置: dist/直播源验证工具.exe")
            return True
        else:
            print(f"✗ EXE构建失败")
            print(f"错误输出: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ 构建过程出错: {e}")
        return False

def create_launcher_script():
    """创建启动脚本"""
    script_content = f'''@echo off
chcp 65001 >nul
title 直播源验证工具启动器

echo ================================================
echo     直播源验证工具启动器
echo ================================================
echo.

cd /d "%~dp0"
echo 当前目录: %CD%
echo.

if exist "dist\\直播源验证工具.exe" (
    echo ✓ 找到EXE文件: %CD%\\dist\\直播源验证工具.exe
    echo.
    echo 正在启动验证工具...
    echo.
    start "" "dist\\直播源验证工具.exe"
    echo ✓ 工具已启动！
    echo.
    echo 如果工具没有出现，请检查:
    echo 1. 是否有杀毒软件拦截
    echo 2. 是否允许运行未知程序
    echo 3. 查看错误信息
) else (
    echo ✗ 错误: 未找到EXE文件
    echo 预期位置: %CD%\\dist\\直播源验证工具.exe
    echo.
    echo 解决方案:
    echo 1. 确保已运行 build_exe.py 构建EXE文件
    echo 2. 检查dist目录是否存在
    echo 3. 查看构建日志中的错误信息
    echo.
)

echo 按任意键退出...
pause >nul
'''
    
    with open('启动验证工具.bat', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✓ 已创建启动脚本: 启动验证工具.bat")

def create_readme():
    """创建说明文件"""
    readme_content = '''# 直播源验证工具 - EXE版本

## 使用说明

### 快速启动
1. 双击 `启动验证工具.bat` 启动应用程序
2. 或直接运行 `dist/直播源验证工具.exe`

### 功能特点
- **文件支持**: 支持M3U、M3U8、TXT格式的直播源文件
- **验证设置**: 可调节超时时间、并发数等参数
- **快速检测**: 集成轻量级URL检测，提升大列表处理效率
- **进度显示**: 实时显示验证进度和统计信息
- **结果保存**: 支持TXT和JSON格式的结果导出
- **日志记录**: 详细的运行日志记录

### 验证设置
- **超时时间**: 单个URL检测的超时限制（1-30秒）
- **并发数**: 同时进行的验证任务数量（1-100）
- **启用VLC检测**: 使用VLC库进行深度流检测
- **启用快速检测**: 使用预过滤和批量处理的快速验证

### 操作流程
1. **选择文件**: 点击"浏览"按钮选择直播源文件
2. **配置设置**: 根据需要调整验证参数
3. **开始验证**: 点击"开始验证"按钮启动验证过程
4. **监控进度**: 观察进度条和统计信息
5. **查看结果**: 在结果标签页中查看有效/无效频道
6. **保存结果**: 使用"保存结果"功能导出验证结果

### 结果说明
- **有效频道**: 能够正常访问的直播源
- **无效频道**: 无法访问或存在问题的直播源，包含失败原因
- **运行日志**: 详细的操作记录和错误信息

### 注意事项
- 验证过程中请勿关闭应用程序
- 大文件验证可能需要较长时间，请耐心等待
- 建议在网络稳定的环境下使用
- 结果文件保存在与EXE相同的目录下

### 技术支持
如有问题，请检查运行日志中的错误信息。

版本: v2.0
构建时间: {build_time}
'''
    
    with open('README_EXE.txt', 'w', encoding='utf-8') as f:
        from datetime import datetime
        f.write(readme_content.format(build_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    print("✓ 已创建说明文件: README_EXE.txt")

def main():
    """主函数"""
    print("=" * 50)
    print("直播源验证工具 EXE 打包工具")
    print("=" * 50)
    
    # 检查当前目录
    if not os.path.exists('integrated_validator.py'):
        print("错误: 未找到 integrated_validator.py")
        print("请在validator目录下运行此脚本")
        return False
    
    # 检查并安装PyInstaller
    if not check_pyinstaller():
        if not install_pyinstaller():
            return False
    
    # 检查依赖项
    if not check_dependencies():
        print("请先安装所需的依赖项")
        return False
    
    # 清理旧文件
    print("\n清理旧文件...")
    for dir_name in ['dist', 'build', '__pycache__']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ 已删除 {dir_name}")
    
    # 删除旧的spec文件
    spec_files = ['validator_exe.spec', '直播源验证工具.spec']
    for spec_file in spec_files:
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print(f"✓ 已删除 {spec_file}")
    
    # 创建spec文件
    print("\n创建构建配置...")
    create_spec_file()
    
    # 构建EXE
    print("\n开始构建...")
    if build_exe():
        # 创建辅助文件
        print("\n创建辅助文件...")
        create_launcher_script()
        create_readme()
        
        print("\n" + "=" * 50)
        print("✓ 构建完成!")
        print("EXE文件位置: dist/直播源验证工具.exe")
        print("启动脚本: 启动验证工具.bat")
        print("说明文件: README_EXE.txt")
        print("=" * 50)
        return True
    else:
        print("\n构建失败，请检查错误信息")
        return False

if __name__ == "__main__":
    success = main()
    input("\n按回车键退出...")
    sys.exit(0 if success else 1)