@echo off
cls
echo 开始运行Python测试脚本...
echo.

rem 运行Python脚本并将输出重定向到文件
python simple_echo.py > output.txt 2>&1

rem 检查退出码
if %errorlevel% equ 0 (
    echo Python脚本执行完成，退出码: 0
) else (
    echo Python脚本执行失败，退出码: %errorlevel%
)

echo.
echo 检查输出文件内容:
type output.txt

echo.
echo 按任意键退出...
pause > nul