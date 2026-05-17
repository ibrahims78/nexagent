import subprocess
import sys
import psutil
import os

IS_WINDOWS = sys.platform == "win32"


def open_application(app_name: str) -> str:
    try:
        if IS_WINDOWS:
            os.startfile(app_name)
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
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace"
        )
        output = result.stdout or result.stderr or "✅ تم تنفيذ الأمر"
        return f"```\n{output[:2000]}\n```"
    except subprocess.TimeoutExpired:
        return "❌ انتهت مهلة تنفيذ الأمر (30 ثانية)"
    except Exception as e:
        return f"❌ خطأ في التنفيذ: {e}"


def shutdown_pc(delay_minutes: int = 0) -> str:
    if IS_WINDOWS:
        os.system(f"shutdown /s /t {delay_minutes * 60}")
    else:
        os.system(f"shutdown -h +{delay_minutes}")
    return f"✅ سيتم إغلاق الحاسب {'الآن' if delay_minutes == 0 else f'بعد {delay_minutes} دقيقة'}"


def restart_pc(delay_minutes: int = 0) -> str:
    if IS_WINDOWS:
        os.system(f"shutdown /r /t {delay_minutes * 60}")
    else:
        os.system(f"shutdown -r +{delay_minutes}")
    return f"✅ سيتم إعادة تشغيل الحاسب {'الآن' if delay_minutes == 0 else f'بعد {delay_minutes} دقيقة'}"


def cancel_shutdown() -> str:
    if IS_WINDOWS:
        os.system("shutdown /a")
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
            os.system(f"powershell -c \"(New-Object -com Shell.Application).sendkeys([char]174)\"")
            return f"✅ تم تعديل الصوت"
    return "❌ هذه الميزة متاحة على ويندوز فقط"
