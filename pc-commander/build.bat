@echo off
chcp 65001 >nul
title NexAgent - Build Script
color 0A

:: Read current version from VERSION file
set /p VER=<VERSION
if "%VER%"=="" set VER=1

echo.
echo  ╔══════════════════════════════════════╗
echo  ║        NexAgent Build Script         ║
echo  ║              V%VER%                        ║
echo  ╚══════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install from python.org and add to PATH.
    pause
    exit /b 1
)

echo  [1/5] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] Dependency installation failed.
    pause
    exit /b 1
)
echo  [OK] Dependencies installed

echo.
echo  [2/5] Creating icon...
python create_icon.py
echo  [OK] Icon created

echo.
echo  [3/5] Building executable...
pyinstaller --noconfirm ^
    --onedir ^
    --windowed ^
    --name "PCCommander" ^
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
    echo  [ERROR] Build failed.
    pause
    exit /b 1
)
echo  [OK] Executable built

echo.
echo  [4/5] Packaging release...
:: Create the release zip
set RELEASE_NAME=NexAgent_V%VER%
if exist "dist\%RELEASE_NAME%.zip" del "dist\%RELEASE_NAME%.zip"
powershell -Command "Compress-Archive -Path 'dist\PCCommander\*' -DestinationPath 'dist\%RELEASE_NAME%.zip' -Force"
if errorlevel 1 (
    echo  [WARN] Zip packaging failed - executable is still available in dist\PCCommander\
) else (
    echo  [OK] Release packaged: %RELEASE_NAME%.zip
)

echo.
echo  [5/5] Creating installer (Inno Setup)...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
    if errorlevel 1 (
        echo  [WARN] Installer creation failed - zip package is still available
    ) else (
        echo  [OK] Installer created in dist\installer\
    )
) else (
    echo  [INFO] Inno Setup not found - skipping installer creation
    echo  [INFO] Install from: jrsoftware.org/isdl.php
)

:: Increment VERSION on successful build
python scripts\bump_version.py

echo.
echo  ╔══════════════════════════════════════╗
echo  ║          Build complete!             ║
echo  ╚══════════════════════════════════════╝
echo.
echo  Executable:  dist\PCCommander\PCCommander.exe
echo  Release zip: dist\NexAgent_V%VER%.zip
echo.
pause
