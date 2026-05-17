@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo.
echo ╔══════════════════════════════════════════╗
echo ║  SshRemote V2 (NexAgent) - Stop Tunnel   ║
echo ╚══════════════════════════════════════════╝
echo.

net session >nul 2>&1
if %errorlevel% neq 0 ( echo [ERROR] Must be run as Administrator. & pause & exit /b 1 )

set "CONFIG=%~dp0sshremote_config.ini"
if not exist "%CONFIG%" set "CONFIG=C:\SshRemote_V2\sshremote_config.ini"

for /f "tokens=3 delims== " %%A in ('findstr /i "task_name" "%CONFIG%" 2^>nul') do set "TASK_NAME=%%A"
if "%TASK_NAME%"=="" set "TASK_NAME=SshRemoteTunnel_V2"

schtasks /end /tn "%TASK_NAME%" >nul 2>&1
echo [1/4] Scheduled task stopped... OK

taskkill /f /im bore.exe >nul 2>&1
if !errorlevel! equ 0 ( echo [2/4] bore.exe killed... OK ) else ( echo [2/4] bore.exe was not running. )

for /f "tokens=2" %%a in ('wmic process where "name='powershell.exe' and commandline like '%%sshremote%%'" get processid /format:list 2^>nul ^| findstr ProcessId') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [3/4] Tunnel PowerShell process stopped... OK

net stop sshd >nul 2>&1
if !errorlevel! equ 0 ( echo [4/4] sshd stopped... OK ) else ( echo [4/4] sshd was already stopped. )

echo.
echo ╔══════════════════════════════════════════╗
echo ║   Tunnel STOPPED.                        ║
echo ║   No remote access is possible now.      ║
echo ╚══════════════════════════════════════════╝
echo.
pause
endlocal
