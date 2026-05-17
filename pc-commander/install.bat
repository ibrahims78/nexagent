@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title NexAgent — Installer

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║     NexAgent Unified Installer                        ║
echo  ║     Remote PC Control via Telegram + SSH              ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.

:: ─────────────────────────────────────────────────────
:: [0] Check Admin
:: ─────────────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] This installer requires Administrator rights.
    echo      Right-click install.bat and choose "Run as administrator"
    echo.
    pause
    exit /b 1
)
echo  [0/6] Administrator rights... OK

:: ─────────────────────────────────────────────────────
:: [1] Check Python
:: ─────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [!] Python not found or not in PATH.
    echo      Download from: https://python.org/downloads
    echo      During install: check "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do set PYVER=%%V
echo  [1/6] Python %PYVER%... OK

:: ─────────────────────────────────────────────────────
:: [2] Install Python dependencies
:: ─────────────────────────────────────────────────────
echo.
echo  [2/6] Installing Python dependencies (requirements.txt)...
pip install -r "%~dp0requirements.txt" --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  [!] Dependency installation failed. Check internet connection and retry.
    pause
    exit /b 1
)
echo  [2/6] Dependencies installed... OK

:: ─────────────────────────────────────────────────────
:: [3] Copy nexagent_config.ini if not present
:: ─────────────────────────────────────────────────────
echo.
echo  [3/6] Setting up configuration file...
set "CFG=%~dp0nexagent_config.ini"
if not exist "%CFG%" (
    if exist "%~dp0nexagent_config.ini.template" (
        copy /y "%~dp0nexagent_config.ini.template" "%CFG%" >nul
    )
    echo  [3/6] Created nexagent_config.ini — open it and fill in your credentials... OK
) else (
    echo  [3/6] nexagent_config.ini already exists... skipped
)

:: ─────────────────────────────────────────────────────
:: [4] Layer 2 — SshRemote V2 setup
:: ─────────────────────────────────────────────────────
echo.
echo  [4/6] Layer 2 — SshRemote V2 (SSH Tunnel)...
set "CORE=%~dp0core"
if not exist "%CORE%\setup_v2.bat" (
    echo  [4/6] core\ files not found — skipping Layer 2 setup
    goto :skip_layer2
)

:: Check if sshremote_config.ini is filled
findstr /c:"YOUR_BOT_TOKEN_HERE" "%CORE%\sshremote_config.ini" >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo  ┌──────────────────────────────────────────────────────┐
    echo  │  Layer 2 requires manual configuration:              │
    echo  │                                                      │
    echo  │  1. Open file:                                       │
    echo  │     core\sshremote_config.ini                        │
    echo  │  2. Enter your Bot Token and Chat ID                 │
    echo  │  3. Then run:  core\setup_v2.bat  as Administrator   │
    echo  └──────────────────────────────────────────────────────┘
    echo.
    echo  [4/6] Layer 2: requires manual setup (see instructions above)
    goto :skip_layer2
)

echo  [4/6] Running setup_v2.bat...
call "%CORE%\setup_v2.bat"
if %errorlevel% neq 0 (
    echo  [!] Layer 2 setup failed — check core\setup_v2.bat
)
:skip_layer2

:: ─────────────────────────────────────────────────────
:: [5] Windows startup (optional)
:: ─────────────────────────────────────────────────────
echo.
set /p STARTUP=  [5/6] Start NexAgent automatically with Windows? [y/N]: 
if /i "%STARTUP%"=="y" (
    set "EXE=%~dp0main.py"
    set "CMD=python \"%~dp0main.py\" --startup"
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "NexAgent" /t REG_SZ /d "!CMD!" /f >nul 2>&1
    echo  [5/6] Auto-start with Windows... enabled
) else (
    echo  [5/6] Auto-start... disabled
)

:: ─────────────────────────────────────────────────────
:: [6] Done
:: ─────────────────────────────────────────────────────
echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║          Installation complete!                       ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.
echo  Next steps:
echo.
echo  1. Open nexagent_config.ini and fill in:
echo       - Bot Token (from @BotFather)
echo       - Chat ID   (from @userinfobot)
echo       - API key   (OpenAI or Gemini)
echo.
echo  2. Start the bot:
echo       python main.py
echo.
echo  3. To enable SSH Layer 2:
echo       Open core\sshremote_config.ini
echo       Run core\setup_v2.bat as Administrator
echo.
echo  Reference: INSTALL_EN.txt  ^|  DOCS.md
echo.
pause
endlocal
