@echo off
chcp 65001 >nul
title PC Commander - Build Script
color 0A

echo.
echo  ╔══════════════════════════════════════╗
echo  ║      PC Commander Build Script       ║
echo  ║              v1.0.0                  ║
echo  ╚══════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python غير مثبت. قم بتثبيته من python.org
    pause
    exit /b 1
)

echo  [1/5] تثبيت المتطلبات...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] فشل تثبيت المتطلبات
    pause
    exit /b 1
)
echo  [OK] تم تثبيت المتطلبات

echo.
echo  [2/5] إنشاء الأيقونة...
python create_icon.py
echo  [OK] تم إنشاء الأيقونة

echo.
echo  [3/5] بناء الملف التنفيذي...
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
    --collect-all "customtkinter" ^
    --collect-all "pystray" ^
    main.py

if errorlevel 1 (
    echo  [ERROR] فشل بناء الملف التنفيذي
    pause
    exit /b 1
)
echo  [OK] تم بناء الملف التنفيذي

echo.
echo  [4/5] إنشاء ملف الترخيص...
echo PC Commander v1.0.0 > dist\PCCommander\LICENSE.txt
echo برنامج مجاني للاستخدام الشخصي >> dist\PCCommander\LICENSE.txt
copy dist\PCCommander\LICENSE.txt LICENSE.txt >nul

echo.
echo  [5/5] إنشاء حزمة التثبيت...
:: Check if Inno Setup is installed
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
    if errorlevel 1 (
        echo  [WARN] فشل إنشاء setup.exe لكن الملف التنفيذي جاهز في dist\PCCommander
    ) else (
        echo  [OK] تم إنشاء setup.exe في dist\installer
    )
) else (
    echo  [INFO] Inno Setup غير مثبت - يمكن تشغيل البرنامج مباشرة من dist\PCCommander\PCCommander.exe
    echo  [INFO] لإنشاء setup.exe قم بتثبيت Inno Setup 6 من jrsoftware.org/isinfo.php
)

echo.
echo  ╔══════════════════════════════════════╗
echo  ║         اكتمل البناء بنجاح!          ║
echo  ╚══════════════════════════════════════╝
echo.
echo  الملف التنفيذي: dist\PCCommander\PCCommander.exe
if exist "dist\installer\PCCommander_Setup_v1.0.0.exe" (
    echo  حزمة التثبيت: dist\installer\PCCommander_Setup_v1.0.0.exe
)
echo.
pause
