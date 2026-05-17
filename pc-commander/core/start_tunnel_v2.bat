@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo.
echo ╔══════════════════════════════════════════╗
echo ║  SshRemote V2 (NexAgent) - Start Tunnel  ║
echo ╚══════════════════════════════════════════╝
echo.

net session >nul 2>&1
if %errorlevel% neq 0 ( echo [ERROR] Must be run as Administrator. & pause & exit /b 1 )

set "CONFIG=%~dp0sshremote_config.ini"
if not exist "%CONFIG%" set "CONFIG=C:\SshRemote_V2\sshremote_config.ini"

for /f "tokens=3 delims== " %%A in ('findstr /i "install_path" "%CONFIG%" 2^>nul') do set "INSTALL_PATH=%%A"
for /f "tokens=3 delims== " %%A in ('findstr /i "task_name"    "%CONFIG%" 2^>nul') do set "TASK_NAME=%%A"
if "%INSTALL_PATH%"=="" set "INSTALL_PATH=C:\SshRemote_V2"
if "%TASK_NAME%"==""    set "TASK_NAME=SshRemoteTunnel_V2"

net start sshd >nul 2>&1
echo [1/2] sshd service started... OK

schtasks /run /tn "%TASK_NAME%" >nul 2>&1
if !errorlevel! equ 0 (
    echo [2/2] Tunnel task started... OK
) else (
    echo [ERROR] Failed to start task "%TASK_NAME%". Is setup complete?
    pause & exit /b 1
)

echo.
echo ╔══════════════════════════════════════════╗
echo ║   Tunnel STARTED!                        ║
echo ║   Check Telegram for the port number.    ║
echo ╚══════════════════════════════════════════╝
echo.
pause
endlocal
