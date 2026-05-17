import os as _os
import psutil
import sys
from datetime import datetime

IS_WINDOWS = sys.platform == "win32"
_SYSTEM_DRIVE = (_os.getenv("SystemDrive", "C:") + "\\") if IS_WINDOWS else "/"


def get_system_status() -> str:
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(_SYSTEM_DRIVE)
    battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None

    status = "📊 **حالة الحاسب:**\n\n"
    status += f"🔲 **المعالج (CPU):** {cpu:.1f}%\n"
    status += f"{'🔴' if cpu > 90 else '🟡' if cpu > 70 else '🟢'} {_progress_bar(cpu)}\n\n"

    status += f"💾 **الذاكرة (RAM):** {ram.percent:.1f}%\n"
    status += f"{'🔴' if ram.percent > 90 else '🟡' if ram.percent > 70 else '🟢'} {_progress_bar(ram.percent)}\n"
    status += f"   المستخدم: {_human_size(ram.used)} / {_human_size(ram.total)}\n\n"

    status += f"💿 **القرص:** {disk.percent:.1f}%\n"
    status += f"{'🔴' if disk.percent > 90 else '🟡' if disk.percent > 70 else '🟢'} {_progress_bar(disk.percent)}\n"
    status += f"   المتاح: {_human_size(disk.free)} / {_human_size(disk.total)}\n\n"

    if IS_WINDOWS:
        try:
            temps = _get_cpu_temp_windows()
            if temps:
                status += f"🌡️ **درجة الحرارة:** {temps}°C\n\n"
        except Exception:
            pass

    if battery:
        status += f"🔋 **البطارية:** {battery.percent:.0f}% {'🔌 متصل' if battery.power_plugged else '🔋 على البطارية'}\n\n"

    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes = remainder // 60
    status += f"⏱️ **وقت التشغيل:** {hours} ساعة و {minutes} دقيقة\n"
    status += f"🕐 **التاريخ والوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return status


def get_daily_report() -> str:
    cpu = psutil.cpu_percent(interval=2)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(_SYSTEM_DRIVE)
    net = psutil.net_io_counters()

    report = f"📅 **التقرير اليومي - {datetime.now().strftime('%Y-%m-%d')}**\n\n"
    report += f"🔲 المعالج: {cpu:.1f}%\n"
    report += f"💾 الذاكرة: {ram.percent:.1f}% (متاح: {_human_size(ram.available)})\n"
    report += f"💿 القرص: {disk.percent:.1f}% (متاح: {_human_size(disk.free)})\n"
    report += f"🌐 الشبكة: ↑{_human_size(net.bytes_sent)} ↓{_human_size(net.bytes_recv)}\n"
    report += f"⏱️ وقت التشغيل: {_get_uptime()}\n"

    alerts = check_alerts()
    if alerts:
        report += "\n⚠️ **تنبيهات:**\n" + "\n".join(alerts)

    return report


def check_alerts(config: dict = None) -> list:
    alerts = []
    cpu_thresh = 90
    ram_thresh = 90
    disk_thresh = 90

    if config:
        cpu_thresh = config.get("monitoring", {}).get("cpu_alert_threshold", 90)
        ram_thresh = config.get("monitoring", {}).get("ram_alert_threshold", 90)
        disk_thresh = config.get("monitoring", {}).get("disk_alert_threshold", 90)

    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage(_SYSTEM_DRIVE).percent

    if cpu > cpu_thresh:
        alerts.append(f"🔴 المعالج مرتفع: {cpu:.1f}%")
    if ram > ram_thresh:
        alerts.append(f"🔴 الذاكرة ممتلئة: {ram:.1f}%")
    if disk > disk_thresh:
        alerts.append(f"🔴 القرص ممتلئ: {disk:.1f}%")

    return alerts


def _get_cpu_temp_windows():
    try:
        import subprocess
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace root/wmi | Select CurrentTemperature"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.isdigit():
                return round((int(line) / 10) - 273.15, 1)
    except Exception:
        pass
    return None


def _progress_bar(percent: float, length: int = 10) -> str:
    filled = int(length * percent / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percent:.1f}%"


def _human_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def _get_uptime() -> str:
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes = remainder // 60
    return f"{hours}h {minutes}m"
