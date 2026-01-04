@echo off
chcp 65001 >nul
setlocal

echo ============================================
echo Flask Web应用停止器
echo ============================================
echo.

echo [信息] 正在查找并关闭 Flask 应用进程...
echo.

REM 查找并关闭 web_converter 进程 (端口5000)
tasklist | findstr "python.exe" | findstr "web_converter" >nul 2>&1
if %errorlevel% equ 0 (
    echo [1/3] 正在关闭 M3U转换器 (web_converter) ...
    taskkill /F /IM python.exe /FI "COMMANDLINE eq *web_converter*" >nul 2>&1
    timeout /t 1 /nobreak >nul
    echo      ✓ 已关闭 M3U转换器
) else (
    echo [1/3] 未发现 M3U转换器 运行
)

REM 查找并关闭 web_app 进程 (端口5001)
tasklist | findstr "python.exe" | findstr "web_app" >nul 2>&1
if %errorlevel% equ 0 (
    echo [2/3] 正在关闭 直播源检查工具 (web_app) ...
    taskkill /F /IM python.exe /FI "COMMANDLINE eq *web_app*" >nul 2>&1
    timeout /t 1 /nobreak >nul
    echo      ✓ 已关闭 直播源检查工具
) else (
    echo [2/3] 未发现 直播源检查工具 运行
)

REM 查找并关闭其他可能的 Flask 应用
tasklist | findstr "python.exe" | findstr "flask" >nul 2>&1
if %errorlevel% equ 0 (
    echo [3/3] 正在关闭其他 Flask 应用 ...
    taskkill /F /IM python.exe /FI "COMMANDLINE eq *flask*" >nul 2>&1
    timeout /t 1 /nobreak >nul
    echo      ✓ 已关闭其他 Flask 应用
) else (
    echo [3/3] 未发现其他 Flask 应用运行
)

echo.
echo ============================================
echo [成功] 所有 Flask 应用已停止
echo ============================================
echo.
echo 已关闭的服务：
echo   - M3U转换器 (端口 5000)
echo   - 直播源检查工具 (端口 5001)
echo   - 其他 Flask 应用
echo.
endlocal
