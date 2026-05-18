@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║     SshRemote V2 — Part of NexAgent             ║
echo ║     Setup Script — Secure SSH Remote Access     ║
echo ╚══════════════════════════════════════════════════╝
echo.

:: ─────────────────────────────────────────
:: [0] Check for Administrator privileges
:: ─────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script must be run as Administrator.
    echo         Right-click setup_v2.bat and choose "Run as administrator"
    echo.
    pause
    exit /b 1
)
echo [0/7] Running as Administrator... OK

:: ─────────────────────────────────────────
:: [STEP 0.1] Read config file
:: ─────────────────────────────────────────
set "CONFIG=%~dp0sshremote_config.ini"
if not exist "%CONFIG%" (
    if exist "%~dp0sshremote_config.ini.template" (
        copy /y "%~dp0sshremote_config.ini.template" "%CONFIG%" >nul
        echo [0/7] Created sshremote_config.ini from template.
        echo [0/7] IMPORTANT: Edit sshremote_config.ini and fill in your bot_token and chat_id before continuing.
        pause
        exit /b 1
    )
    echo [ERROR] sshremote_config.ini not found next to this script.
    pause
    exit /b 1
)

for /f "tokens=3 delims== " %%A in ('findstr /i "install_path" "%CONFIG%"') do set "INSTALL_PATH=%%A"
for /f "tokens=3 delims== " %%A in ('findstr /i "task_name"    "%CONFIG%"') do set "TASK_NAME=%%A"
if "%INSTALL_PATH%"=="" set "INSTALL_PATH=C:\SshRemote_V2"
if "%TASK_NAME%"==""    set "TASK_NAME=SshRemoteTunnel_V2"

echo [0/7] Config loaded: install_path=%INSTALL_PATH%  task=%TASK_NAME%
echo.

:: ─────────────────────────────────────────
:: [1] Copy files to install path
:: ─────────────────────────────────────────
echo [1/7] Installing files to %INSTALL_PATH% ...
if not exist "%INSTALL_PATH%" (
    mkdir "%INSTALL_PATH%"
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create directory: %INSTALL_PATH%
        pause
        exit /b 1
    )
)

xcopy /y /q "%~dp0bore.exe"                  "%INSTALL_PATH%\" >nul 2>&1
xcopy /y /q "%~dp0sshremote_key.pub"         "%INSTALL_PATH%\" >nul 2>&1
xcopy /y /q "%~dp0sshremote_tunnel_v2.ps1"   "%INSTALL_PATH%\" >nul 2>&1
xcopy /y /q "%~dp0sshremote_config.ini"      "%INSTALL_PATH%\" >nul 2>&1
xcopy /y /q "%~dp0start_tunnel_v2.bat"       "%INSTALL_PATH%\" >nul 2>&1
xcopy /y /q "%~dp0stop_tunnel_v2.bat"        "%INSTALL_PATH%\" >nul 2>&1
xcopy /y /q "%~dp0show_port_v2.bat"          "%INSTALL_PATH%\" >nul 2>&1
xcopy /y /q "%~dp0uninstall_v2.bat"          "%INSTALL_PATH%\" >nul 2>&1

if not exist "%INSTALL_PATH%\bore.exe" (
    echo [ERROR] Failed to copy bore.exe to install path.
    pause
    exit /b 1
)
echo [1/7] Files installed... OK

:: ─────────────────────────────────────────
:: [2] Install OpenSSH Server
:: ─────────────────────────────────────────
echo [2/7] Installing OpenSSH Server...
powershell -Command "Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0" 2>&1 | findstr /i "error fail" >nul
echo [2/7] OpenSSH Server installed... OK
net start sshd >nul 2>&1
sc config sshd start=auto >nul 2>&1
echo [2/7] sshd service configured for auto-start... OK

:: ─────────────────────────────────────────
:: [3] Configure sshd safely
:: ─────────────────────────────────────────
echo [3/7] Configuring sshd_config safely...
set "SSHD_CONFIG=C:\ProgramData\ssh\sshd_config"

if not exist "%SSHD_CONFIG%" (
    echo # SshRemote V2 - sshd_config > "%SSHD_CONFIG%"
)

powershell -Command ^
  "$cfg = '%SSHD_CONFIG%';" ^
  "$content = Get-Content $cfg -ErrorAction SilentlyContinue;" ^
  "$content = $content | Where-Object { $_ -notmatch '^(StrictModes|PasswordAuthentication|PubkeyAuthentication|Subsystem sftp)' };" ^
  "$content += 'StrictModes no';" ^
  "$content += 'PasswordAuthentication no';" ^
  "$content += 'PubkeyAuthentication yes';" ^
  "$content += 'Subsystem sftp sftp-server.exe';" ^
  "Set-Content $cfg $content -Encoding UTF8" 2>&1

if !errorlevel! neq 0 (
    echo [ERROR] Failed to configure sshd_config.
    pause
    exit /b 1
)
net stop sshd >nul 2>&1
net start sshd >nul 2>&1
echo [3/7] sshd configured and restarted... OK

:: ─────────────────────────────────────────
:: [4] Setup authorized_keys
:: ─────────────────────────────────────────
echo [4/7] Setting up SSH authorized keys...
set "SSH_DIR=C:\Users\%USERNAME%\.ssh"
set "AUTH_KEYS=%SSH_DIR%\authorized_keys"
set "ADMIN_KEYS=C:\ProgramData\ssh\administrators_authorized_keys"

if not exist "%SSH_DIR%" mkdir "%SSH_DIR%"

findstr /c:"sshremote-access" "%AUTH_KEYS%" >nul 2>&1
if !errorlevel! neq 0 (
    type "%INSTALL_PATH%\sshremote_key.pub" >> "%AUTH_KEYS%"
    echo [4/7] Public key added to authorized_keys... OK
) else (
    echo [4/7] Public key already present, skipping... OK
)

icacls "%AUTH_KEYS%" /inheritance:r /grant "%USERNAME%:F" /grant "SYSTEM:F" >nul 2>&1
copy /y "%AUTH_KEYS%" "%ADMIN_KEYS%" >nul 2>&1
icacls "%ADMIN_KEYS%" /inheritance:r /grant "SYSTEM:F" /grant "Administrators:F" >nul 2>&1
echo [4/7] administrators_authorized_keys configured... OK

:: ─────────────────────────────────────────
:: [5] Set bore.exe permissions
:: ─────────────────────────────────────────
echo [5/7] Setting bore.exe permissions...
icacls "%INSTALL_PATH%\bore.exe" /grant "%USERNAME%:F" /grant "SYSTEM:F" >nul 2>&1
echo [5/7] bore.exe permissions set... OK

:: ─────────────────────────────────────────
:: [6] Create Scheduled Task
:: ─────────────────────────────────────────
echo [6/7] Creating scheduled task: %TASK_NAME% ...
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File \"%INSTALL_PATH%\sshremote_tunnel_v2.ps1\"" ^
  /sc onlogon ^
  /ru "%USERNAME%" ^
  /it /rl highest /f >nul 2>&1

if !errorlevel! neq 0 (
    echo [ERROR] Failed to create scheduled task.
    pause
    exit /b 1
)
echo [6/7] Scheduled task created... OK

:: ─────────────────────────────────────────
:: [7] Start tunnel immediately
:: ─────────────────────────────────────────
echo [7/7] Starting tunnel for the first time...
schtasks /run /tn "%TASK_NAME%" >nul 2>&1
echo [7/7] Tunnel started... OK

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║   Setup Complete!                                ║
echo ║   Check Telegram — port will arrive in ~30 sec   ║
echo ║                                                  ║
echo ║   Connect:   ssh USER@bore.pub -p PORT           ║
echo ║   Stop:      run stop_tunnel_v2.bat              ║
echo ║   Remove:    run uninstall_v2.bat                ║
echo ╚══════════════════════════════════════════════════╝
echo.
pause
endlocal
