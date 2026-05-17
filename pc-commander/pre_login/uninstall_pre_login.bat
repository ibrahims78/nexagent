@echo off
chcp 65001 >nul
title Uninstall Pre-Login Agent

net session >nul 2>&1
if errorlevel 1 (
    echo Must run as Administrator. Right-click and choose "Run as administrator"
    pause
    exit /b 1
)

schtasks /delete /tn "PCCommander_PreLogin" /f
echo Done. Pre-Login Agent scheduled task removed.
pause
