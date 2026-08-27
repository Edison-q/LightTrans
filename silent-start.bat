@echo off
rem LightTrans silent launcher (called by startup, no window)
cd /d "%~dp0"
set LT_SILENT=1
".venv\Scripts\python.exe" server.py >> server.log 2>&1
