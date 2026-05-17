@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║  SshRemote V2 (NexAgent) - Uninstall Script      ║
echo ║  This will remove ALL remote access.             ║
echo ╚══════════════════════════════════════════════════╝
echo.

net session >nul 2>&1
if %errorlevel% neq 0 ( echo [ERROR] Must be run as Administrator. & pause & exit /b 1 )

echo   WARNING: This will:
echo   - Remove the SshRemote public key from this machine
echo   - Delete the scheduled task
echo   - Stop bore.exe and sshd
echo   - Delete all SshRemote files from install path
echo.
set /p CONFIRM=   Type YES to confirm uninstall: 
if /i not "%CONFIRM%"=="YES" ( echo   Uninstall cancelled. & pause & exit /b 0 )
echo.

set "CONFIG=%~dp0sshremote_config.ini"
if not exist "%CONFIG%" set "CONFIG=C:\SshRemote_V2\sshremote_config.ini"

for /f "tokens=3 delims== " %%A in ('findstr /i "install_path" "%CONFIG%" 2^>nul') do set "INSTALL_PATH=%%A"
for /f "tokens=3 delims== " %%A in ('findstr /i "task_name"    "%CONFIG%" 2^>nul') do set "TASK_NAME=%%A"
if "%INSTALL_PATH%"=="" set "INSTALL_PATH=C:\SshRemote_V2"
if "%TASK_NAME%"==""    set "TASK_NAME=SshRemoteTunnel_V2"

schtasks /end    /tn "%TASK_NAME%" >nul 2>&1
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
echo [1/6] Scheduled task removed... OK

taskkill /f /im bore.exe >nul 2>&1
echo [2/6] bore.exe stopped... OK

for /f "tokens=2" %%a in ('wmic process where "name='powershell.exe' and commandline like '%%sshremote%%'" get processid /format:list 2^>nul ^| findstr ProcessId') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [3/6] PowerShell tunnel process stopped... OK

set "AUTH_KEYS=C:\Users\%USERNAME%\.ssh\authorized_keys"
set "ADMIN_KEYS=C:\ProgramData\ssh\administrators_authorized_keys"

if exist "%AUTH_KEYS%" (
    powershell -Command "(Get-Content '%AUTH_KEYS%') | Where-Object { $_ -notmatch 'sshremote-access' } | Set-Content '%AUTH_KEYS%' -Encoding UTF8" 2>nul
    echo [4/6] SshRemote key removed from authorized_keys... OK
) else ( echo [4/6] authorized_keys not found, skipping. )

if exist "%ADMIN_KEYS%" (
    powershell -Command "(Get-Content '%ADMIN_KEYS%') | Where-Object { $_ -notmatch 'sshremote-access' } | Set-Content '%ADMIN_KEYS%' -Encoding UTF8" 2>nul
)

net stop sshd >nul 2>&1
echo [5/6] sshd stopped... OK

if exist "%INSTALL_PATH%" (
    rmdir /s /q "%INSTALL_PATH%" >nul 2>&1
    if exist "%INSTALL_PATH%" (
        echo [6/6] WARNING: Could not delete %INSTALL_PATH% — please delete manually.
    ) else ( echo [6/6] Install directory deleted... OK )
) else ( echo [6/6] Install directory not found, skipping. )

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║   Uninstall Complete.                            ║
echo ║   SshRemote has been fully removed.              ║
echo ╚══════════════════════════════════════════════════╝
echo.
pause
endlocal
