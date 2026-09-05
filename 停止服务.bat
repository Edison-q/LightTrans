@echo off
rem Stop ALL LightTrans instances: scan ports 8765-8774, kill python listeners.
rem Note: in for /f command strings, ^^ escapes to a literal ^ for findstr regex.
set killed=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R ":876[5-9][^^0-9] :877[0-4][^^0-9]" ^| findstr "LISTENING"') do (
  tasklist /FI "PID eq %%a" | findstr /I "python.exe" >nul 2>&1
  if not errorlevel 1 (
    taskkill /F /PID %%a >nul 2>&1
    set /a killed+=1
  )
)
echo [LightTrans] Stopped %killed% instance(s).
echo [LightTrans] Restart: double-click KaiLightTrans.vbs (or reboot for auto-start).
pause >nul
