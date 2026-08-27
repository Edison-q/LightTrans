@echo off
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
echo [LightTrans] Server stopped.
echo Restart: reboot the PC (auto-start) or double-click the start bat.
pause >nul
