@echo off
chcp 65001 >nul
echo ============================
echo 量学交易记录 - 推送到 GitHub
echo ============================
echo.

cd /d D:\选股软件\hermes选股\website

echo 1. 生成今日记录...
python generate_site.py

echo.
echo 2. 提交到 GitHub...
git add -A
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set DT=%%I
set TODAY=%DT:~0,4%-%DT:~4,2%-%DT:~6,2%
git commit -m "每日更新 %TODAY%"
git push

echo.
echo 完成！https://zw113210672.github.io
pause
