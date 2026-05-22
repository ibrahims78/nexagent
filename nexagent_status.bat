@echo off
title NexAgent Status
echo ==========================================
echo           NexAgent Bot Status
echo ==========================================
tasklist /FI "IMAGENAME eq python.exe" /FO CSV 2>nul | findstr /I "python.exe" >nul
if %errorlevel%==0 (
    echo [*] Status: RUNNING
) else (
    echo [*] Status: STOPPED
)
echo.
echo --- Last log lines ---
if exist "C:\nexagent\bot_log.txt" (
    type "C:\nexagent\bot_log.txt"
) else (
    echo No log file found.
)
echo ==========================================
pause
