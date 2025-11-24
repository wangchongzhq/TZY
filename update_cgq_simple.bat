@echo off
echo =====================================================
echo           直播源更新工具
echo =====================================================
echo.

REM 设置输出文件
set "OUTPUT=CGQ.TXT"
set "TEMP=temp_update.txt"

REM 创建文件内容
echo # 超高清直播源列表 > "%TEMP%"
echo # 更新时间: %date% %time% >> "%TEMP%"
echo # 简单批处理工具 >> "%TEMP%"
echo. >> "%TEMP%"

REM 央视频道
echo 央视,#genre# >> "%TEMP%"
echo CCTV-1综合,https://raw.githubusercontent.com/Supprise0901/tvlist/main/live.txt >> "%TEMP%"
echo CCTV-2财经,https://raw.githubusercontent.com/ffmking/TVlist/main/live.txt >> "%TEMP%"
echo CCTV-3综艺,https://raw.githubusercontent.com/qingtingjjjjjjj/tvlist1/main/live.txt >> "%TEMP%"
echo CCTV-4中文国际,https://raw.githubusercontent.com/zhonghu32/live/main/888.txt >> "%TEMP%"
echo CCTV-5体育,https://raw.githubusercontent.com/cuijian01/dianshi/main/888.txt >> "%TEMP%"
echo CCTV-6电影,https://raw.githubusercontent.com/xyy0508/iptv/main/888.txt >> "%TEMP%"
echo CCTV-7国防军事,https://raw.githubusercontent.com/zhonghu32/live/main/live.txt >> "%TEMP%"
echo CCTV-8电视剧,https://raw.githubusercontent.com/cuijian01/dianshi/main/live.txt >> "%TEMP%"
echo. >> "%TEMP%"

REM 4K频道
echo 4K央视频道,#genre# >> "%TEMP%"
echo CCTV-4K超高清,https://raw.githubusercontent.com/Supprise0901/tvlist/main/live.txt >> "%TEMP%"
echo. >> "%TEMP%"

REM 新增直播源
echo 新增直播源,#genre# >> "%TEMP%"
echo 新源1,https://raw.githubusercontent.com/Supprise0901/tvlist/main/live.txt >> "%TEMP%"
echo 新源2,https://raw.githubusercontent.com/ffmking/TVlist/main/live.txt >> "%TEMP%"
echo 新源3,https://raw.githubusercontent.com/qingtingjjjjjjj/tvlist1/main/live.txt >> "%TEMP%"
echo 新源4,https://raw.githubusercontent.com/zhonghu32/live/main/888.txt >> "%TEMP%"
echo 新源5,https://raw.githubusercontent.com/cuijian01/dianshi/main/888.txt >> "%TEMP%"
echo 新源6,https://raw.githubusercontent.com/xyy0508/iptv/main/888.txt >> "%TEMP%"
echo 新源7,https://raw.githubusercontent.com/zhonghu32/live/main/live.txt >> "%TEMP%"
echo 新源8,https://raw.githubusercontent.com/cuijian01/dianshi/main/live.txt >> "%TEMP%"
echo. >> "%TEMP%"

REM 替换文件
if exist "%OUTPUT%" del "%OUTPUT%"
ren "%TEMP%" "%OUTPUT%"

echo =====================================================
echo         更新完成！
echo         文件: %OUTPUT%
echo =====================================================
pause
