import shlex
import subprocess
import sys
import psutil
import os
from src.utils.logger import get_logger

logger = get_logger()

IS_WINDOWS = sys.platform == "win32"

ALLOWED_COMMANDS: set = {
    "shutdown", "restart", "screenshot", "system_status", "list_processes",
    "list_files", "run_command", "open_application", "close_application",
    "lock_screen", "volume", "anydesk", "daily_report", "cancel_shutdown",
}

DANGEROUS_EXTENSIONS = {".bat", ".ps1", ".vbs", ".cmd"}

SAFE_APPS: set = {
    "notepad", "notepad.exe",
    "calc", "calc.exe",
    "explorer", "explorer.exe",
    "mspaint", "mspaint.exe",
    "wordpad", "wordpad.exe",
    "chrome", "chrome.exe",
    "firefox", "firefox.exe",
    "msedge", "msedge.exe",
    "code", "code.exe",
    "anydesk", "anydesk.exe",
    "taskmgr", "taskmgr.exe",
}

BLOCKED_CMD_PREFIXES = {
    "format", "del /f /s", "rd /s", "rmdir /s",
    "rm -rf", "dd if=", ":(){:|:&};:",
    "mkfs", "fdisk", "diskpart",
    "reg delete", "reg add",
    "netsh firewall", "sc delete",
    "bcdedit", "bootrec",
}


def open_application(app_name: str) -> str:
    if not app_name:
        return "❌ لم يتم تحديد اسم التطبيق"

    name_lower = app_name.lower().strip()
    base_name = os.path.basename(name_lower)

    ext = os.path.splitext(base_name)[1]
    if ext in DANGEROUS_EXTENSIONS:
        return f"❌ نوع الملف غير مسموح به للفتح: {ext}"

    if base_name not in SAFE_APPS and name_lower not in SAFE_APPS:
        return f"❌ التطبيق '{app_name}' غير موجود في قائمة التطبيقات المسموح بها"

    try:
        if IS_WINDOWS:
            subprocess.Popen([app_name], shell=False)
        else:
            subprocess.Popen(["xdg-open", app_name])
        return f"✅ تم فتح: {app_name}"
    except Exception as e:
        return f"❌ فشل فتح {app_name}: {e}"


def close_application(process_name: str) -> str:
    killed = []
    for proc in psutil.process_iter(["name", "pid"]):
        if process_name.lower() in proc.info["name"].lower():
            try:
                proc.terminate()
                killed.append(proc.info["name"])
            except Exception:
                pass
    if killed:
        return f"✅ تم إغلاق: {', '.join(killed)}"
    return f"❌ لم يتم العثور على عملية: {process_name}"


def list_running_processes() -> str:
    procs = []
    for proc in psutil.process_iter(["name", "pid", "cpu_percent", "memory_percent"]):
        try:
            if proc.info["cpu_percent"] > 0.1:
                procs.append(f"• {proc.info['name']} (PID: {proc.info['pid']}) CPU: {proc.info['cpu_percent']:.1f}%")
        except Exception:
            pass
    procs.sort()
    return "📋 **البرامج النشطة:**\n" + "\n".join(procs[:20]) if procs else "لا توجد برامج نشطة"


def run_command(command: str) -> str:
    cmd_lower = command.lower().strip()
    for blocked in BLOCKED_CMD_PREFIXES:
        if cmd_lower.startswith(blocked) or blocked in cmd_lower:
            logger.warning(f"Blocked dangerous command attempt: {command[:100]}")
            return f"❌ الأمر محظور لأسباب أمنية: `{command[:50]}`"
    try:
        args = shlex.split(command)
        if not args:
            return "❌ أمر فارغ"
        result = subprocess.run(
            args, shell=False, capture_output=True, text=True,
            timeout=30, encoding="utf-8", errors="replace"
        )
        output = result.stdout or result.stderr or "✅ تم تنفيذ الأمر"
        return f"```\n{output[:2000]}\n```"
    except subprocess.TimeoutExpired:
        return "❌ انتهت مهلة تنفيذ الأمر (30 ثانية)"
    except Exception as e:
        return f"❌ خطأ في التنفيذ: {e}"


def shutdown_pc(delay_minutes: int = 0) -> str:
    if IS_WINDOWS:
        subprocess.run(["shutdown", "/s", "/t", str(delay_minutes * 60)], check=False)
    else:
        subprocess.run(["shutdown", "-h", f"+{delay_minutes}"], check=False)
    return f"✅ سيتم إغلاق الحاسب {'الآن' if delay_minutes == 0 else f'بعد {delay_minutes} دقيقة'}"


def restart_pc(delay_minutes: int = 0) -> str:
    if IS_WINDOWS:
        subprocess.run(["shutdown", "/r", "/t", str(delay_minutes * 60)], check=False)
    else:
        subprocess.run(["shutdown", "-r", f"+{delay_minutes}"], check=False)
    return f"✅ سيتم إعادة تشغيل الحاسب {'الآن' if delay_minutes == 0 else f'بعد {delay_minutes} دقيقة'}"


def cancel_shutdown() -> str:
    if IS_WINDOWS:
        subprocess.run(["shutdown", "/a"], check=False)
    return "✅ تم إلغاء إيقاف التشغيل"


def lock_screen() -> str:
    if IS_WINDOWS:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return "✅ تم قفل الشاشة"
    return "❌ هذه الميزة متاحة على ويندوز فقط"


def set_volume(level: int) -> str:
    if IS_WINDOWS:
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100, None)
            return f"✅ تم ضبط الصوت على {level}%"
        except Exception:
            subprocess.run(
                ["powershell", "-c",
                 "(New-Object -com Shell.Application).sendkeys([char]174)"],
                check=False
            )
            return "✅ تم تعديل الصوت"
    return "❌ هذه الميزة متاحة على ويندوز فقط"
