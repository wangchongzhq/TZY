@echo off
chcp 65001 >nul
title 直播源验证工具启动器

echo ================================================
echo     直播源验证工具启动器
echo ================================================
echo.

cd /d "%~dp0"
echo 当前目录: %CD%
echo.

if exist "dist\直播源验证工具.exe" (
    echo ✓ 找到EXE文件: %CD%\dist\直播源验证工具.exe
    echo.
    echo 正在启动验证工具...
    echo.
    start "" "dist\直播源验证工具.exe"
    echo ✓ 工具已启动！
    echo.
    echo 如果工具没有出现，请检查:
    echo 1. 是否有杀毒软件拦截
    echo 2. 是否允许运行未知程序
    echo 3. 查看错误信息
) else (
    echo ✗ 未找到EXE文件，尝试使用Python版本
    echo.
    if exist "integrated_validator.py" (
        echo ✓ 找到验证工具: %CD%\integrated_validator.py
        echo.
        echo 正在启动验证工具...
        echo.
        python integrated_validator.py
        echo.
        echo ✓ 验证工具已退出
    ) else (
        echo ✗ 错误: 未找到任何可用的验证工具
        echo 预期文件: 
        echo 1. dist\直播源验证工具.exe (EXE版本)
        echo 2. integrated_validator.py (Python版本)
        echo.
        echo 解决方案:
        echo 1. 运行 build_exe.py 构建EXE文件
        echo 2. 确保integrated_validator.py文件存在
    )
)

echo.
echo 按任意键退出...
pause >nul