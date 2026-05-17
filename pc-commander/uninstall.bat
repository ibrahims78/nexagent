@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title NexAgent — Uninstaller

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║              NexAgent — إلغاء التثبيت               ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.
echo  سيقوم هذا السكريبت بـ:
echo    - إيقاف بوت NexAgent
echo    - إزالة التشغيل التلقائي مع ويندوز
echo    - إيقاف نفق SSH وإزالة المهمة المجدولة
echo    - حذف ملفات التثبيت (مع الاحتفاظ بإعداداتك)
echo.
set /p CONFIRM=  هل أنت متأكد؟ [y/N]: 
if /i not "%CONFIRM%"=="y" (
    echo  تم الإلغاء.
    pause
    exit /b 0
)

:: ─────────────────────────────────────────────────────
:: [1] Stop running bot process
:: ─────────────────────────────────────────────────────
echo.
echo  [1/4] إيقاف بوت NexAgent...
taskkill /f /im "NexAgent.exe" >nul 2>&1
taskkill /f /im "python.exe"   >nul 2>&1
echo  [1/4] تم إيقاف العمليات... OK

:: ─────────────────────────────────────────────────────
:: [2] Remove Windows startup entry
:: ─────────────────────────────────────────────────────
echo.
echo  [2/4] إزالة التشغيل التلقائي...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "NexAgent" /f >nul 2>&1
echo  [2/4] تم حذف مدخل الإقلاع التلقائي... OK

:: ─────────────────────────────────────────────────────
:: [3] Uninstall SSH Layer 2 (SshRemote V2)
:: ─────────────────────────────────────────────────────
echo.
echo  [3/4] إلغاء تثبيت طبقة SSH (SshRemote V2)...
set "CORE=%~dp0core"
if exist "%CORE%\uninstall_v2.bat" (
    call "%CORE%\uninstall_v2.bat"
    echo  [3/4] طبقة SSH أُزيلت... OK
) else (
    :: Try to remove scheduled task directly
    schtasks /delete /tn "SshRemoteTunnel_V2" /f >nul 2>&1
    taskkill /f /im "bore.exe" >nul 2>&1
    echo  [3/4] تم حذف مهمة SSH المجدولة... OK
)

:: ─────────────────────────────────────────────────────
:: [4] Summary
:: ─────────────────────────────────────────────────────
echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║              اكتمل إلغاء التثبيت!                   ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.
echo  ملاحظة: إعداداتك محفوظة في:
echo    %%APPDATA%%\PCCommander\config.json
echo.
echo  لحذفها نهائياً، احذف المجلد:
echo    %%APPDATA%%\PCCommander\
echo.
pause
endlocal
