@echo off
chcp 65001 >nul
title 一键构建直播源验证工具EXE

echo ================================================
echo     直播源验证工具EXE一键构建脚本
echo ================================================
echo.

:: 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    echo 请先安装Python 3.7或更高版本
    pause
    exit /b 1
)

echo ✓ Python环境检查通过

:: 进入validator目录
cd /d "%~dp0"

:: 检查必要文件
if not exist "integrated_validator.py" (
    echo 错误: 未找到 integrated_validator.py
    echo 请确保在validator目录下运行此脚本
    pause
    exit /b 1
)

if not exist "build_exe.py" (
    echo 错误: 未找到 build_exe.py
    echo 请确保文件完整
    pause
    exit /b 1
)

echo ✓ 文件检查通过

:: 运行构建脚本
echo.
echo 正在运行构建脚本...
echo.

python build_exe.py

:: 检查构建结果
if exist "dist\直播源验证工具.exe" (
    echo.
    echo ================================================
    echo ✓ 构建成功！
    echo EXE文件位置: dist\直播源验证工具.exe
    echo 启动脚本: 启动验证工具.bat
    echo ================================================
    echo.
    echo 是否现在启动验证工具？(Y/N)
    set /p choice=请输入: 
    if /i "%choice%"=="Y" (
        start "" "dist\直播源验证工具.exe"
        echo 工具已启动
    )
) else (
    echo.
    echo ✗ 构建失败，请检查错误信息
)

echo.
pause