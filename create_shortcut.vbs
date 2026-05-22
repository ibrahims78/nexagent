Set WshShell = CreateObject("WScript.Shell")
Set oShortcut = WshShell.CreateShortcut("C:\Users\admin\Desktop\NexAgent-GUI.lnk")
oShortcut.TargetPath = "C:\Python313\python.exe"
oShortcut.Arguments = "C:\nexagent\pc-commander\main.py"
oShortcut.WorkingDirectory = "C:\nexagent\pc-commander"
oShortcut.WindowStyle = 1
oShortcut.IconLocation = "C:\Python313\python.exe,0"
oShortcut.Description = "NexAgent GUI"
oShortcut.Save
WScript.Echo "Shortcut created"
