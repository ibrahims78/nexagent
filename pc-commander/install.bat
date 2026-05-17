@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title NexAgent — Installer

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║              NexAgent — المثبّت الموحد               ║
echo  ║         التحكم الكامل بالحاسب عبر تيليغرام          ║
echo  ║   الطبقة الأولى: بوت AI  +  الطبقة الثانية: SSH     ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.

:: ─────────────────────────────────────────────────────
:: [0] Check Admin
:: ─────────────────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] يتطلب هذا المثبّت صلاحيات المدير.
    echo      انقر بزر الفأرة الأيمن على install.bat واختر "تشغيل كمسؤول"
    echo.
    pause
    exit /b 1
)
echo  [0/6] صلاحيات المدير... موجودة

:: ─────────────────────────────────────────────────────
:: [1] Check Python
:: ─────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [!] Python غير موجود أو غير مضاف لـ PATH.
    echo      قم بتنزيله من: https://python.org/downloads
    echo      تأكد من تفعيل "Add Python to PATH" أثناء التثبيت.
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
echo  [2/6] تثبيت المكتبات المطلوبة (requirements.txt)...
pip install -r "%~dp0requirements.txt" --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  [!] فشل تثبيت المكتبات. تحقق من اتصال الإنترنت ثم أعد المحاولة.
    pause
    exit /b 1
)
echo  [2/6] المكتبات مثبتة... OK

:: ─────────────────────────────────────────────────────
:: [3] Copy nexagent_config.ini if not present
:: ─────────────────────────────────────────────────────
echo.
echo  [3/6] إعداد ملف الإعدادات الموحد...
set "CFG=%~dp0nexagent_config.ini"
if not exist "%CFG%" (
    if exist "%~dp0nexagent_config.ini.template" (
        copy /y "%~dp0nexagent_config.ini.template" "%CFG%" >nul
    )
    echo  [3/6] تم إنشاء nexagent_config.ini — افتحه وأدخل بياناتك... OK
) else (
    echo  [3/6] nexagent_config.ini موجود بالفعل... تجاوز
)

:: ─────────────────────────────────────────────────────
:: [4] Layer 2 — SshRemote V2 setup
:: ─────────────────────────────────────────────────────
echo.
echo  [4/6] الطبقة الثانية — SshRemote V2 (SSH Tunnel)...
set "CORE=%~dp0core"
if not exist "%CORE%\setup_v2.bat" (
    echo  [4/6] ملفات core\ غير موجودة — تخطي تثبيت الطبقة الثانية
    goto :skip_layer2
)

:: Check if sshremote_config.ini is filled
findstr /c:"YOUR_BOT_TOKEN_HERE" "%CORE%\sshremote_config.ini" >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo  ┌──────────────────────────────────────────────────────┐
    echo  │  الطبقة الثانية تحتاج إلى إعداد يدوي:              │
    echo  │                                                      │
    echo  │  1. افتح الملف:                                      │
    echo  │     core\sshremote_config.ini                        │
    echo  │  2. ضع Bot Token و Chat ID الخاصين بك               │
    echo  │  3. ثم شغّل:  core\setup_v2.bat  كمسؤول             │
    echo  └──────────────────────────────────────────────────────┘
    echo.
    echo  [4/6] الطبقة الثانية: تحتاج إعداد يدوي (انظر التعليمات أعلاه)
    goto :skip_layer2
)

echo  [4/6] تشغيل setup_v2.bat...
call "%CORE%\setup_v2.bat"
if %errorlevel% neq 0 (
    echo  [!] فشل تثبيت الطبقة الثانية — تحقق من core\setup_v2.bat
)
:skip_layer2

:: ─────────────────────────────────────────────────────
:: [5] Windows startup (optional)
:: ─────────────────────────────────────────────────────
echo.
set /p STARTUP=  [5/6] هل تريد تشغيل NexAgent تلقائياً مع ويندوز؟ [y/N]: 
if /i "%STARTUP%"=="y" (
    set "EXE=%~dp0main.py"
    set "CMD=python \"%~dp0main.py\" --startup"
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "NexAgent" /t REG_SZ /d "!CMD!" /f >nul 2>&1
    echo  [5/6] التشغيل التلقائي مع ويندوز... مفعّل
) else (
    echo  [5/6] التشغيل التلقائي... غير مفعّل
)

:: ─────────────────────────────────────────────────────
:: [6] Done
:: ─────────────────────────────────────────────────────
echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║              اكتمل التثبيت بنجاح!                   ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.
echo  الخطوات التالية:
echo.
echo  1. افتح nexagent_config.ini وأدخل:
echo       - Bot Token (من @BotFather)
echo       - Chat ID   (من @userinfobot)
echo       - مفتاح API (OpenAI أو Gemini)
echo.
echo  2. شغّل البوت:
echo       python main.py
echo.
echo  3. لتفعيل SSH Layer 2:
echo       افتح core\sshremote_config.ini
echo       شغّل core\setup_v2.bat كمسؤول
echo.
echo  مرجع: INSTALL_AR.txt  ^|  DOCS.md
echo.
pause
endlocal
