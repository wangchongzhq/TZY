@echo off
chcp 65001 >nul 2>&1
echo Dual M3U Converter Starting...
echo Usage:
echo   python convert_m3u_to_txt.py filename.m3u     (M3U to TXT)
echo   python convert_m3u_to_txt.py filename.txt     (TXT to M3U)
echo   python convert_m3u_to_txt.py input.txt output.m3u (Specify output filename)
echo.
echo Starting command line tool...
start "" python "C:\Users\Administrator\Documents\GitHub\TZY\convert_m3u_to_txt.py" --help
echo Done!
pause
