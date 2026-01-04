@echo off
:: Enable UTF-8 encoding to avoid Chinese character issues ( >nul 2>&1 hides output)
chcp 65001 >nul 2>&1

echo Starting TRAE validation service...
cd /d "%~dp0"
start "" python validator\web_app.py
timeout /t 2 /nobreak >nul
echo Opening browser to http://127.0.0.1:5001...
start "" "http://127.0.0.1:5001"
echo Service startup complete! Press any key to close window...
pause >nul