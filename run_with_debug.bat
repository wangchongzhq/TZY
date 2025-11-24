@echo off

rem 运行Python脚本并捕获所有输出
echo 正在执行直播源更新脚本...
python -u get_cgq_sources.py > output.log 2>&1

rem 显示输出文件内容
echo 脚本执行完成，输出内容如下：
type output.log

echo.
echo 按任意键继续...
pause > nul
