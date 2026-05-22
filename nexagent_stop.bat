@echo off
title NexAgent Stop
echo [NexAgent] Stopping bot...
taskkill /F /IM python.exe /T >nul 2>&1
if %errorlevel%==0 (
    echo [NexAgent] Bot stopped successfully.
) else (
    echo [NexAgent] Bot was not running.
)
del "C:\nexagent\bot_log.txt" >nul 2>&1
timeout /t 2 /nobreak >nul
