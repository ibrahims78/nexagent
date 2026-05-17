@echo off
chcp 65001 >nul 2>&1

echo.
echo ╔══════════════════════════════════════════╗
echo ║  SshRemote V2 (NexAgent) - Current Port  ║
echo ╚══════════════════════════════════════════╝
echo.

set "CONFIG=%~dp0sshremote_config.ini"
if not exist "%CONFIG%" set "CONFIG=C:\SshRemote_V2\sshremote_config.ini"

for /f "tokens=3 delims== " %%A in ('findstr /i "install_path" "%CONFIG%" 2^>nul') do set "INSTALL_PATH=%%A"
if "%INSTALL_PATH%"=="" set "INSTALL_PATH=C:\SshRemote_V2"

set "PORT_FILE=%INSTALL_PATH%\bore_port.txt"

if not exist "%PORT_FILE%" (
    echo   [INFO] No active tunnel found.
    echo          Start the tunnel first using start_tunnel_v2.bat
    echo.
    pause & exit /b 0
)

for /f %%p in ('type "%PORT_FILE%"') do (
    echo   Device   : %COMPUTERNAME%
    echo   User     : %USERNAME%
    echo   Server   : bore.pub
    echo   Port     : %%p
    echo.
    echo   ─────────────────────────────────────────────
    echo   Connection command:
    echo     ssh %USERNAME%@bore.pub -p %%p
    echo.
    echo   With key file:
    echo     ssh -i sshremote_key %USERNAME%@bore.pub -p %%p
    echo   ─────────────────────────────────────────────
)
echo.
pause
