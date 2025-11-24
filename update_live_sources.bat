@echo off
chcp 65001 > nul
echo.--------------------------------------------------------------------
echo.                直播源更新工具 (无需Python环境)
echo.--------------------------------------------------------------------
echo.
set "output_file=CGQ.TXT"
set "temp_file=temp_cgq_update.txt"

REM 检查输出文件是否存在
if not exist "%output_file%" (
    echo 警告: %output_file% 文件不存在，将创建新文件
)

REM 创建临时文件
echo # 超高清直播源列表 > "%temp_file%"
echo # 更新时间: %date% %time% >> "%temp_file%"
echo # 更新方式: 批处理工具 >> "%temp_file%"
echo. >> "%temp_file%"

REM 添加分类和频道
echo 央视,#genre# >> "%temp_file%"
echo CCTV-1综合,https://raw.githubusercontent.com/Supprise0901/tvlist/main/live.txt >> "%temp_file%"
echo CCTV-2财经,https://raw.githubusercontent.com/ffmking/TVlist/main/live.txt >> "%temp_file%"
echo CCTV-3综艺,https://raw.githubusercontent.com/qingtingjjjjjjj/tvlist1/main/live.txt >> "%temp_file%"
echo CCTV-4中文国际,https://raw.githubusercontent.com/zhonghu32/live/main/888.txt >> "%temp_file%"
echo CCTV-5体育,https://raw.githubusercontent.com/cuijian01/dianshi/main/888.txt >> "%temp_file%"
echo CCTV-6电影,https://raw.githubusercontent.com/xyy0508/iptv/main/888.txt >> "%temp_file%"
echo CCTV-7国防军事,https://raw.githubusercontent.com/zhonghu32/live/main/live.txt >> "%temp_file%"
echo CCTV-8电视剧,https://raw.githubusercontent.com/cuijian01/dianshi/main/live.txt >> "%temp_file%"
echo. >> "%temp_file%"

echo 4K央视频道,#genre# >> "%temp_file%"
echo CCTV-4K超高清,https://raw.githubusercontent.com/Supprise0901/tvlist/main/live.txt >> "%temp_file%"
echo. >> "%temp_file%"

echo 新增直播源,#genre# >> "%temp_file%"
echo 新源1,https://raw.githubusercontent.com/Supprise0901/tvlist/main/live.txt >> "%temp_file%"
echo 新源2,https://raw.githubusercontent.com/ffmking/TVlist/main/live.txt >> "%temp_file%"
echo 新源3,https://raw.githubusercontent.com/qingtingjjjjjjj/tvlist1/main/live.txt >> "%temp_file%"
echo 新源4,https://raw.githubusercontent.com/zhonghu32/live/main/888.txt >> "%temp_file%"
echo 新源5,https://raw.githubusercontent.com/cuijian01/dianshi/main/888.txt >> "%temp_file%"
echo 新源6,https://raw.githubusercontent.com/xyy0508/iptv/main/888.txt >> "%temp_file%"
echo 新源7,https://raw.githubusercontent.com/zhonghu32/live/main/live.txt >> "%temp_file%"
echo 新源8,https://raw.githubusercontent.com/cuijian01/dianshi/main/live.txt >> "%temp_file%"
echo. >> "%temp_file%"

REM 替换原文件
if exist "%output_file%" (
    del "%output_file%"
)
ren "%temp_file%" "%output_file%"

echo.--------------------------------------------------------------------
echo. ✓ 直播源文件更新完成！
echo. ✓ 文件位置: %output_file%
echo. ✓ 更新时间: %date% %time%
echo.--------------------------------------------------------------------
echo.
pause
