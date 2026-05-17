@echo off
chcp 65001 >nul
title NexAgent - Build Script
color 0A
setlocal enabledelayedexpansion

:: Read current version from VERSION file
set /p VER=<VERSION
if "%VER%"=="" set VER=1

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║          NexAgent Build Script                   ║
echo  ║          Version: %VER%                                ║
echo  ║   Layer 1: Bot  ^|  Layer 2: SSH (SshRemote V2)   ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ─────────────────────────────────────────
:: [1/6] Check Python
:: ─────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install from python.org and add to PATH.
    pause
    exit /b 1
)
echo  [1/6] Python found... OK

:: ─────────────────────────────────────────
:: [2/6] Install dependencies
:: ─────────────────────────────────────────
echo.
echo  [2/6] Installing dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo  [ERROR] Dependency installation failed.
    pause
    exit /b 1
)
echo  [2/6] Dependencies installed... OK

:: ─────────────────────────────────────────
:: [3/6] Create icon
:: ─────────────────────────────────────────
echo.
echo  [3/6] Creating icon...
python create_icon.py 2>nul
echo  [3/6] Icon created... OK

:: ─────────────────────────────────────────
:: [4/6] Build executable with PyInstaller
:: ─────────────────────────────────────────
echo.
echo  [4/6] Building executable (NexAgent)...

if exist "dist\NexAgent" rmdir /s /q "dist\NexAgent"

pyinstaller --noconfirm ^
    --onedir ^
    --windowed ^
    --name "NexAgent" ^
    --icon "assets\icon.ico" ^
    --add-data "assets;assets" ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "pystray._win32" ^
    --hidden-import "telegram" ^
    --hidden-import "openai" ^
    --hidden-import "google.generativeai" ^
    --hidden-import "flask" ^
    --hidden-import "apscheduler" ^
    --hidden-import "pyngrok" ^
    --hidden-import "docx" ^
    --hidden-import "psutil" ^
    --hidden-import "pyautogui" ^
    --hidden-import "cryptography" ^
    --hidden-import "pycaw" ^
    --hidden-import "comtypes" ^
    --hidden-import "paramiko" ^
    --collect-all "customtkinter" ^
    --collect-all "pystray" ^
    main.py

if errorlevel 1 (
    echo  [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)
echo  [4/6] Executable built at dist\NexAgent\NexAgent.exe... OK

:: ─────────────────────────────────────────
:: [5/6] Package release zip (both layers)
:: ─────────────────────────────────────────
echo.
echo  [5/6] Packaging release zip (Layer 1 + Layer 2)...

set "RELEASE_NAME=NexAgent_V%VER%"
set "RELEASE_DIR=dist\%RELEASE_NAME%"
set "RELEASE_ZIP=dist\%RELEASE_NAME%.zip"

:: Build staging folder
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%\core"

:: Layer 1 — bot executable
xcopy /y /q /s "dist\NexAgent\*" "%RELEASE_DIR%\" >nul 2>&1

:: Layer 2 — SshRemote V2 core files
for %%F in (
    core\sshremote_tunnel_v2.ps1
    core\sshremote_config.ini
    core\setup_v2.bat
    core\start_tunnel_v2.bat
    core\stop_tunnel_v2.bat
    core\show_port_v2.bat
    core\uninstall_v2.bat
    core\README_AR.txt
    core\README_EN.txt
) do (
    if exist "%%F" xcopy /y /q "%%F" "%RELEASE_DIR%\core\" >nul 2>&1
)

if exist "core\sshremote_key.pub" xcopy /q "core\sshremote_key.pub" "%RELEASE_DIR%\core\" >nul 2>&1
if not exist "%RELEASE_DIR%\core\sshremote_key.pub" (
    echo NOTE: Generate your SSH key pair: ssh-keygen -t ed25519 -f core\sshremote_key > "%RELEASE_DIR%\core\GENERATE_SSH_KEY.txt"
)

:: bore.exe note (Windows binary — add manually)
(
    echo NOTE: bore.exe must be placed in this core\ folder manually.
    echo It is a Windows binary and cannot be bundled from Replit.
    echo Download: https://github.com/ekzhang/bore/releases
) > "%RELEASE_DIR%\core\BORE_README.txt"

:: Docs + config + scripts
for %%F in (nexagent_config.ini DOCS.md INSTALL_AR.txt INSTALL_EN.txt LICENSE.txt install.bat uninstall.bat) do (
    if exist "%%F" copy /y "%%F" "%RELEASE_DIR%\" >nul 2>&1
)

:: Create zip
if exist "%RELEASE_ZIP%" del "%RELEASE_ZIP%"
powershell -Command "Compress-Archive -Path '%RELEASE_DIR%\*' -DestinationPath '%RELEASE_ZIP%' -Force"
if errorlevel 1 (
    echo  [WARN] Zip creation failed - staging folder available at %RELEASE_DIR%\
) else (
    echo  [5/6] Release packaged: %RELEASE_ZIP%... OK
)

:: Optional: Inno Setup GUI installer
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo.
    echo  [5b] Creating GUI installer (Inno Setup)...
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
    if errorlevel 1 (
        echo  [WARN] Inno Setup failed - zip package is still available
    ) else (
        echo  [5b] GUI installer: dist\installer\NexAgent_Setup_v1.1.0.exe... OK
    )
) else (
    echo  [5b] Inno Setup not installed - skipping GUI installer
    echo       Get it from: jrsoftware.org/isdl.php
)

:: ─────────────────────────────────────────
:: [6/6] Bump VERSION
:: ─────────────────────────────────────────
echo.
echo  [6/6] Bumping version number...
python scripts\bump_version.py
echo  [6/6] Version bumped to next build... OK

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║                Build Complete!                   ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  Executable  : dist\NexAgent\NexAgent.exe
echo  Release zip : dist\%RELEASE_NAME%.zip
echo.
echo  Release zip contents:
echo    NexAgent.exe  (Layer 1 — Telegram bot)
echo    core\         (Layer 2 — SSH tunnel scripts)
echo    install.bat   uninstall.bat
echo    DOCS.md       INSTALL_AR.txt   INSTALL_EN.txt
echo    nexagent_config.ini
echo.
echo  REMINDER: Place bore.exe in core\ before distributing.
echo.
pause
endlocal
