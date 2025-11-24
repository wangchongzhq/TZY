@echo off
cls

echo ====================================================
echo            简化版直播源更新工具
 echo             适用于环境受限情况
 echo ====================================================
echo.
echo 此工具将生成CGQ.TXT文件，无需Python额外依赖

:: 检查Python是否可用
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到Python环境！
    echo.
    echo 请安装Python 3.x或使用以下方法之一：
    echo 1. 下载Python安装包：https://www.python.org/downloads/
    echo 2. 使用Microsoft Store安装Python
    echo 3. 使用此文件夹中的update_cgq_simple.bat直接添加频道
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

:: 运行简化脚本
echo 正在运行更新脚本...
echo.
python simple_static_update.py

:: 检查脚本执行结果
if %errorlevel% equ 0 (
    echo.
    echo [成功] 更新完成！
    echo CGQ.TXT文件已生成
    echo.
    echo 按任意键查看文件内容...
    pause >nul
    type CGQ.TXT | more
    echo.
    echo 文件保存在：%cd%\CGQ.TXT
) else (
    echo.
    echo [错误] 更新失败！
    echo 请检查以上错误信息
)

echo.
echo 按任意键退出...
pause >nul
