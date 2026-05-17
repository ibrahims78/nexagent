@echo off
chcp 65001 >nul
title PC Commander - Pre-Login Agent Setup
color 0B

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║     إعداد Pre-Login Agent                    ║
echo  ║     سكريبت الإشعار عند الإقلاع              ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Check admin
net session >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] يجب تشغيل هذا الملف كـ Administrator
    echo  انقر بالزر الأيمن واختر "تشغيل كمسؤول"
    pause
    exit /b 1
)

echo  [1/4] تثبيت المتطلبات...
pip install python-telegram-bot==20.7 pywin32 --quiet
echo  [OK] تم التثبيت

echo.
echo  [2/4] بناء ملف exe...
pyinstaller --noconfirm --onefile --noconsole ^
    --name "PCCommander_PreLogin" ^
    --hidden-import "win32api" ^
    --hidden-import "win32con" ^
    --hidden-import "telegram" ^
    pre_login_agent.py

if errorlevel 1 (
    echo  [WARN] فشل بناء exe - سيعمل كـ Python script
    set AGENT_PATH=python "%~dp0pre_login_agent.py"
) else (
    set AGENT_PATH="%~dp0dist\PCCommander_PreLogin.exe"
    echo  [OK] تم بناء exe
)

echo.
echo  [3/4] إنشاء مهمة مجدولة في ويندوز...

:: Create scheduled task that runs at system startup (before login)
schtasks /create /tn "PCCommander_PreLogin" ^
    /tr "%AGENT_PATH%" ^
    /sc onstart ^
    /ru "SYSTEM" ^
    /rl HIGHEST ^
    /f ^
    /delay 0000:30

if errorlevel 1 (
    echo  [ERROR] فشل إنشاء المهمة المجدولة
    pause
    exit /b 1
)

echo  [OK] تم إنشاء المهمة المجدولة

echo.
echo  [4/4] التحقق من الإعداد...
schtasks /query /tn "PCCommander_PreLogin" /fo LIST | findstr "Status"

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║         تم الإعداد بنجاح!                    ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  ما الذي سيحدث عند كل إقلاع:
echo  1. ويندوز يبدأ الإقلاع
echo  2. السكريبت يعمل تلقائياً
echo  3. ينتظر الإنترنت
echo  4. يرسل إشعاراً لتيليغرام
echo  5. تضغط "سجّل الدخول" من أي مكان
echo  6. يدخل ويندوز تلقائياً
echo.
pause
