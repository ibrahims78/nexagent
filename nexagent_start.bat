@echo off
title NexAgent Bot
cd /d "C:\nexagent\pc-commander"
tasklist /FI "IMAGENAME eq python.exe" /FO CSV 2>nul | findstr /I "python.exe" >nul
if %errorlevel%==0 (
    echo [NexAgent] Bot is already running!
    timeout /t 2 /nobreak >nul
    exit /b 0
)

:: Set your credentials here before running
:: set TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
:: set TELEGRAM_ALLOWED_USERS=YOUR_USER_ID_HERE
:: set GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
set AI_PROVIDER=gemini

echo [NexAgent] Starting bot...
start "NexAgent" /MIN cmd /c "cd /d C:\nexagent\pc-commander && python run_headless.py > C:\nexagent\bot_log.txt 2>&1"
echo [NexAgent] Bot started! Check Telegram.
timeout /t 3 /nobreak >nul
