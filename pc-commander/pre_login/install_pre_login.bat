@echo off
chcp 65001 >nul
title PC Commander - Pre-Login Agent Setup
color 0B

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║     Pre-Login Agent Setup                    ║
echo  ║     Boot Notification Script                 ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Check admin
net session >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Must run as Administrator. Right-click and choose "Run as administrator"
    pause
    exit /b 1
)

echo  [1/4] Installing requirements...
pip install python-telegram-bot==20.7 pywin32 --quiet
echo  [OK] Requirements installed

echo.
echo  [2/4] Building executable...
pyinstaller --noconfirm --onefile --noconsole ^
    --name "PCCommander_PreLogin" ^
    --hidden-import "win32api" ^
    --hidden-import "win32con" ^
    --hidden-import "telegram" ^
    pre_login_agent.py

if errorlevel 1 (
    echo  [WARN] EXE build failed - will run as Python script
    set AGENT_PATH=python "%~dp0pre_login_agent.py"
) else (
    set AGENT_PATH="%~dp0dist\PCCommander_PreLogin.exe"
    echo  [OK] EXE built successfully
)

echo.
echo  [3/4] Creating Windows scheduled task...

:: Create scheduled task that runs at system startup (before login)
schtasks /create /tn "PCCommander_PreLogin" ^
    /tr "%AGENT_PATH%" ^
    /sc onstart ^
    /ru "SYSTEM" ^
    /rl HIGHEST ^
    /f ^
    /delay 0000:30

if errorlevel 1 (
    echo  [ERROR] Failed to create scheduled task
    pause
    exit /b 1
)

echo  [OK] Scheduled task created

echo.
echo  [4/4] Verifying setup...
schtasks /query /tn "PCCommander_PreLogin" /fo LIST | findstr "Status"

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║         Setup complete!                      ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  What happens on every boot:
echo  1. Windows starts booting
echo  2. This script runs automatically
echo  3. Waits for internet connection
echo  4. Sends a Telegram notification
echo  5. You tap "Login" from anywhere
echo  6. Windows logs in automatically
echo.
pause
