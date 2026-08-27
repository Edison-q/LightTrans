@echo off
netsh advfirewall firewall add rule name="LightTrans" dir=in action=allow protocol=TCP localport=8765
netsh advfirewall firewall show rule name="LightTrans"
echo.
echo Done. You can close this window now.
pause
