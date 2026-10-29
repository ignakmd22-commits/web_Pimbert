@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py servidor.py
) else (
  python servidor.py
)
echo.
pause
