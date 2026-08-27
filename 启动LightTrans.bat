@echo off
cd /d "%~dp0"
netstat -ano | findstr ":8765 " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
  echo [LightTrans] Server is already running, opening page...
  start http://localhost:8765
  ping -n 2 127.0.0.1 >nul
  exit /b
)
echo [LightTrans] Starting server... (first run may take ~1 min to install deps)
echo.
uv run server.py
echo.
echo [LightTrans] Stopped. Press any key to close...
pause >nul
