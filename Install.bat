@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 install.py %*
) else (
  python install.py %*
)
set "linxsci_result=%errorlevel%"
if %linxsci_result% neq 0 echo 安装或配置未完成，请查看上方提示。需要 Python 3.9 或更新版本。
pause
exit /b %linxsci_result%
