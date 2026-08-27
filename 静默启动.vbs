' LightTrans silent startup entry (hidden window, portable)
' Tip: to auto-start at Windows login, create a SHORTCUT to this file
' and place the shortcut in the Startup folder (Win+R -> shell:startup).
Set fso = CreateObject("Scripting.FileSystemObject")
baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set ws = CreateObject("WScript.Shell")
ws.CurrentDirectory = baseDir
ws.Run """" & baseDir & "\silent-start.bat""", 0, False
