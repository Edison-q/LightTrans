' 打开LightTrans.vbs — 万能打开按钮（双击它永远能打开 LightTrans）
' 逻辑：服务在线 -> 直接开页面；不在线 -> 静默拉起 -> 等就绪 -> 开页面
Option Explicit
Dim fso, sh, baseDir
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = baseDir

' ---- 用 netstat 快扫 8765-8774 的监听端口（一次调用 <0.5s）----
Function ListeningPorts()
    Dim ex, out, lines, line, arr, item, p, result, i, j
    Set ex = sh.Exec("cmd /c netstat -ano | findstr /R "":876[5-9][^0-9] :877[0-4][^0-9]"" | findstr ""LISTENING""")
    out = ex.StdOut.ReadAll()
    result = ","
    lines = Split(out, vbCrLf)
    For i = 0 To UBound(lines)
        line = Trim(lines(i))
        If Len(line) > 0 Then
            arr = Split(line, " ")
            For j = 0 To UBound(arr)
                item = arr(j)
                If Len(item) > 0 And InStr(item, ":") > 0 Then
                    p = Right(item, Len(item) - InStrRev(item, ":"))
                    If IsNumeric(p) Then
                        If CInt(p) >= 8765 And CInt(p) <= 8774 Then
                            If InStr(result, "," & p & ",") = 0 Then result = result & p & ","
                        End If
                    End If
                End If
            Next
        End If
    Next
    ListeningPorts = result
End Function

' ---- HTTP 确认端口上确实是 LightTrans（/health 返回 lighttrans）----
Function IsLightTrans(port)
    Dim http
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.setTimeouts 600, 600, 600, 600
    On Error Resume Next
    http.open "GET", "http://127.0.0.1:" & port & "/health", False
    http.send
    If Err.Number = 0 Then
        If http.status = 200 Then
            If InStr(1, http.responseText, "lighttrans", 1) > 0 Then
                IsLightTrans = True
                Exit Function
            End If
        End If
    End If
    Err.Clear
    IsLightTrans = False
End Function

' ---- 找第一个可用的 LightTrans 服务端口，没有则返回 0 ----
Function FindServicePort()
    Dim ports, arr, i, p
    ports = ListeningPorts()
    If Len(ports) > 2 Then
        arr = Split(Mid(ports, 2, Len(ports) - 2), ",")
        For i = 0 To UBound(arr)
            If Len(arr(i)) > 0 Then
                p = CInt(arr(i))
                If IsLightTrans(p) Then
                    FindServicePort = p
                    Exit Function
                End If
            End If
        Next
    End If
    FindServicePort = 0
End Function

' ---- 找 Edge（用于 App 独立窗口模式）----
Function FindEdge()
    Dim p
    p = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    If fso.FileExists(p) Then FindEdge = p : Exit Function
    p = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    If fso.FileExists(p) Then FindEdge = p : Exit Function
    p = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Microsoft\Edge\Application\msedge.exe"
    If fso.FileExists(p) Then FindEdge = p : Exit Function
    FindEdge = ""
End Function

' ---- 用 Edge App 模式打开页面（独立窗口，和「作为应用安装」体验一致）----
Sub OpenPage(port)
    Dim edge, target
    edge = FindEdge()
    target = "http://localhost:" & port
    If Len(edge) > 0 Then
        sh.Run """" & edge & """ --app=" & target, 1, False
    Else
        sh.Run target, 1, False
    End If
End Sub

' ---- 主流程 ----
Dim port, i
port = FindServicePort()
If port > 0 Then
    OpenPage port          ' 服务在线：直接开门
    WScript.Quit 0
End If

' 服务不在线：静默拉起（防重入由 silent-start.bat 内部保证）
sh.Run """" & baseDir & "\silent-start.bat""", 0, False

' 等待就绪：每秒快扫一次，最多 30 秒
For i = 1 To 30
    WScript.Sleep 1000
    port = FindServicePort()
    If port > 0 Then
        OpenPage port
        WScript.Quit 0
    End If
Next

' 确实起不来：给用户指路
MsgBox "LightTrans 启动超时。" & vbCrLf & vbCrLf & _
       "请查看日志：" & baseDir & "\server.log" & vbCrLf & _
       "如果日志没有新内容，双击「启动LightTrans.bat」可以看到具体报错。", _
       vbExclamation, "LightTrans"
