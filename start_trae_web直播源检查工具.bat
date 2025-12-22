@echo off
chcp 65001 >nul 2>&1  :: 解决中文乱码
echo 正在启动TRAE验证服务...
:: 启动Python Web服务（后台运行，避免窗口阻塞）
start "" python "C:\Users\Administrator\Documents\GitHub\TZY\validator\web_app.py"
:: 延迟2秒（等待服务加载完成），再打开浏览器访问地址
timeout /t 2 /nobreak >nul
echo 正在打开浏览器访问 http://localhost:5001...
start "" "http://localhost:5001"
echo 服务启动完成！按任意键关闭窗口（服务仍会后台运行）...
pause >nul