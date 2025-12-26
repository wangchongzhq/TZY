Set oShell = CreateObject("WScript.Shell")
oShell.Run "powershell -ExecutionPolicy Bypass -File ""%~dp0git_sync.ps1""", 1, True
