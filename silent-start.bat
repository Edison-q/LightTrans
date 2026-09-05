@echo off
rem LightTrans silent launcher (called by startup / KaiLightTrans.vbs, no window)
rem Re-entry guard: if an instance is already listening on 8765-8774, exit.
cd /d "%~dp0"
netstat -ano | findstr /R ":876[5-9][^0-9] :877[0-4][^0-9]" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 exit /b
set LT_SILENT=1
".venv\Scripts\python.exe" server.py >> server.log 2>&1
