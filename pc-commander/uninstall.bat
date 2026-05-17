@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title NexAgent — Uninstaller

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║              NexAgent — Uninstaller                  ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.
echo  This script will:
echo    - Stop the NexAgent bot process
echo    - Remove Windows auto-start entry
echo    - Stop SSH tunnel and remove scheduled task
echo    - Remove installation files (your settings are preserved)
echo.
set /p CONFIRM=  Are you sure? [y/N]: 
if /i not "%CONFIRM%"=="y" (
    echo  Cancelled.
    pause
    exit /b 0
)

:: ─────────────────────────────────────────────────────
:: [1] Stop running bot process
:: ─────────────────────────────────────────────────────
echo.
echo  [1/4] Stopping NexAgent bot...
taskkill /f /im "NexAgent.exe" >nul 2>&1
taskkill /f /im "python.exe"   >nul 2>&1
echo  [1/4] Processes stopped... OK

:: ─────────────────────────────────────────────────────
:: [2] Remove Windows startup entry
:: ─────────────────────────────────────────────────────
echo.
echo  [2/4] Removing auto-start entry...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "NexAgent" /f >nul 2>&1
echo  [2/4] Auto-start entry removed... OK

:: ─────────────────────────────────────────────────────
:: [3] Uninstall SSH Layer 2 (SshRemote V2)
:: ─────────────────────────────────────────────────────
echo.
echo  [3/4] Uninstalling SSH layer (SshRemote V2)...
set "CORE=%~dp0core"
if exist "%CORE%\uninstall_v2.bat" (
    call "%CORE%\uninstall_v2.bat"
    echo  [3/4] SSH layer removed... OK
) else (
    :: Try to remove scheduled task directly
    schtasks /delete /tn "SshRemoteTunnel_V2" /f >nul 2>&1
    taskkill /f /im "bore.exe" >nul 2>&1
    echo  [3/4] SSH scheduled task removed... OK
)

:: ─────────────────────────────────────────────────────
:: [4] Summary
:: ─────────────────────────────────────────────────────
echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║              Uninstall complete!                      ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.
echo  Note: Your settings are preserved at:
echo    %%APPDATA%%\PCCommander\config.json
echo.
echo  To delete them permanently, remove this folder:
echo    %%APPDATA%%\PCCommander\
echo.
pause
endlocal
