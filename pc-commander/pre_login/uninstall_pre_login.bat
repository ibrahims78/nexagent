@echo off
chcp 65001 >nul
title إلغاء Pre-Login Agent

net session >nul 2>&1
if errorlevel 1 (
    echo يجب تشغيل كـ Administrator
    pause
    exit /b 1
)

schtasks /delete /tn "PCCommander_PreLogin" /f
echo ✅ تم إلغاء المهمة المجدولة بنجاح
pause
