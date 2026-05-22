Set oWS = WScript.CreateObject("WScript.Shell")  
sLinkFile = "C:\Users\admin\Desktop\NexAgent-Start.lnk"  
Set oLink = oWS.CreateShortcut(sLinkFile)  
oLink.TargetPath = "C:\nexagent\nexagent_start.bat"  
oLink.WorkingDirectory = "C:\nexagent"  
oLink.IconLocation = "C:\Windows\System32\SHELL32.dll,77"  
oLink.Save  
Set oLink2 = oWS.CreateShortcut("C:\Users\admin\Desktop\NexAgent-Stop.lnk")  
oLink2.TargetPath = "C:\nexagent\nexagent_stop.bat"  
oLink2.WorkingDirectory = "C:\nexagent"  
oLink2.IconLocation = "C:\Windows\System32\SHELL32.dll,131"  
oLink2.Save  
Set oLink3 = oWS.CreateShortcut("C:\Users\admin\Desktop\NexAgent-Status.lnk")  
oLink3.TargetPath = "C:\nexagent\nexagent_status.bat"  
oLink3.WorkingDirectory = "C:\nexagent"  
oLink3.IconLocation = "C:\Windows\System32\SHELL32.dll,23"  
oLink3.Save  
