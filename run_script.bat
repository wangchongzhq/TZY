@echo off
cls
echo 开始运行直播源获取脚本...
echo.

rem 获取当前目录
set "CURRENT_DIR=%~dp0"

rem 运行Python脚本
python "%CURRENT_DIR%get_cgq_sources.py"

rem 检查退出码
if %errorlevel% equ 0 (
    echo.
    echo 脚本运行成功！
) else (
    echo.
    echo 脚本运行失败，退出码: %errorlevel%
)

echo.
echo 按任意键退出...
pause > nul