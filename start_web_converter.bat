@echo off
chcp 65001 >nul
echo ============================================
echo M3U Converter Launcher (Normal Mode)
echo ============================================
echo.
echo Port: 5000
echo Address: http://127.0.0.1:5000/
echo.
echo Starting Flask application...
echo Press Ctrl+C to stop service
echo.

cd /d "%~dp0"
start "" python web_converter.py
timeout /t 3 /nobreak >nul
echo Opening browser to http://127.0.0.1:5000...
start "" "http://127.0.0.1:5000"
echo Converter startup complete! Press any key to close this window...
pause >nul
