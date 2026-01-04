@echo off
chcp 936 >nul
title IPTV Validator Launcher

echo ================================================
echo     IPTV Validator Launcher
echo ================================================
echo.

cd /d "%~dp0"
echo Current directory: %CD%
echo.

REM Check for EXE version first
if exist "dist\直播源验证工具.exe" (
    echo [OK] Found EXE file: %CD%\dist\直播源验证工具.exe
    echo.
    echo Starting validator...
    echo.
    start "" "dist\直播源验证工具.exe"
    echo [OK] Validator started!
    echo.
    echo If the tool doesn't appear, please check:
    echo 1. Anti-virus software blocking
    echo 2. Unknown program execution permission
    echo 3. Error messages
    goto :end
) else (
    echo [WARN] EXE file not found, trying Python version
    echo.
    REM Check if Python version exists
    if exist "integrated_validator.py" (
        echo [OK] Found validator: %CD%\integrated_validator.py
        echo.
        echo Starting validator...
        echo.
        
        REM Check if we have a GUI environment
        echo Checking GUI environment...
        
        REM Try to run the validator
        python integrated_validator.py
        
        REM Check exit code
        if errorlevel 1 (
            echo.
            echo [ERROR] Validator failed to start
            echo Possible reasons:
            echo 1. No GUI environment (running in console mode)
            echo 2. Missing dependencies
            echo 3. Permission issues
            echo.
            echo Solutions:
            echo 1. Run on a desktop environment
            echo 2. Check Python dependencies: pip install -r requirements.txt
            echo 3. Try running from Windows Explorer
            echo.
        ) else (
            echo.
            echo [OK] Validator exited normally
        )
    ) else (
        echo [ERROR] No validator found
        echo Expected files:
        echo 1. dist\直播源验证工具.exe (EXE version)
        echo 2. integrated_validator.py (Python version)
        echo.
        echo Solutions:
        echo 1. Run build_exe.py to build EXE file
        echo 2. Ensure integrated_validator.py exists
    )
)

:end
echo.
echo Press any key to exit...
pause >nul