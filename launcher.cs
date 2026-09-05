// LightTrans launcher: starts 打开LightTrans.vbs in the same folder, then exits.
// Compiled with the built-in .NET compiler:
//   C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe ^
//     /win32icon:icon.ico /out:LightTrans.exe launcher.cs
// An .exe is required because Windows 11 refuses to pin script (.vbs/.bat)
// shortcuts to the taskbar.
using System;
using System.Diagnostics;
using System.IO;

class Program
{
    static void Main()
    {
        string dir = Path.GetDirectoryName(typeof(Program).Assembly.Location);
        // "\u6253\u5f00LightTrans.vbs" = 打开LightTrans.vbs (ASCII-safe source)
        string vbs = Path.Combine(dir, "\u6253\u5f00LightTrans.vbs");
        var psi = new ProcessStartInfo("wscript.exe", "\"" + vbs + "\"")
        {
            UseShellExecute = true,
            WindowStyle = ProcessWindowStyle.Hidden
        };
        Process.Start(psi);
    }
}
