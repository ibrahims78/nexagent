import subprocess
import sys
import os
import time
import re

IS_WINDOWS = sys.platform == "win32"

DEFAULT_PATHS = [
    "C:\\Program Files (x86)\\AnyDesk\\AnyDesk.exe",
    "C:\\Program Files\\AnyDesk\\AnyDesk.exe",
    os.path.expanduser("~\\AppData\\Local\\Programs\\AnyDesk\\AnyDesk.exe"),
]


def find_anydesk() -> str:
    for path in DEFAULT_PATHS:
        if os.path.exists(path):
            return path
    return None


def get_anydesk_id(anydesk_path: str = None) -> str:
    if not IS_WINDOWS:
        return "❌ AnyDesk متاح على ويندوز فقط"
    
    path = anydesk_path or find_anydesk()
    if not path:
        return "❌ لم يتم العثور على AnyDesk. تأكد من تثبيته أولاً."
    
    try:
        result = subprocess.run(
            [path, "--get-id"],
            capture_output=True, text=True, timeout=10
        )
        anydesk_id = result.stdout.strip()
        if anydesk_id and anydesk_id.isdigit():
            return anydesk_id
        
        result2 = subprocess.run(
            ["powershell", "-Command",
             "Get-Content '$env:APPDATA\\AnyDesk\\system.conf' -ErrorAction SilentlyContinue | Select-String 'ad.anynet.id'"],
            capture_output=True, text=True, timeout=5
        )
        match = re.search(r"ad\.anynet\.id=(\d+)", result2.stdout)
        if match:
            return match.group(1)
        
        return "❌ تعذر الحصول على ID، تأكد أن AnyDesk يعمل"
    except Exception as e:
        return f"❌ خطأ: {e}"


def start_anydesk(anydesk_path: str = None) -> str:
    if not IS_WINDOWS:
        return "❌ AnyDesk متاح على ويندوز فقط"
    
    path = anydesk_path or find_anydesk()
    if not path:
        return "❌ لم يتم العثور على AnyDesk"
    
    try:
        subprocess.Popen([path])
        time.sleep(3)
        anydesk_id = get_anydesk_id(path)
        return f"✅ تم تشغيل AnyDesk\n🔑 **رقم الاتصال:** `{anydesk_id}`\n\nاستخدم هذا الرقم للاتصال بحاسبك"
    except Exception as e:
        return f"❌ فشل تشغيل AnyDesk: {e}"


def stop_anydesk() -> str:
    if not IS_WINDOWS:
        return "❌ AnyDesk متاح على ويندوز فقط"
    try:
        subprocess.run(["taskkill", "/F", "/IM", "AnyDesk.exe"], capture_output=True)
        return "✅ تم إغلاق AnyDesk"
    except Exception as e:
        return f"❌ فشل إغلاق AnyDesk: {e}"


def set_anydesk_password(password: str, anydesk_path: str = None) -> str:
    if not IS_WINDOWS:
        return "❌ AnyDesk متاح على ويندوز فقط"
    path = anydesk_path or find_anydesk()
    if not path:
        return "❌ لم يتم العثور على AnyDesk"
    try:
        subprocess.run([path, "--set-password", password], capture_output=True, timeout=5)
        return "✅ تم تعيين كلمة مرور AnyDesk"
    except Exception as e:
        return f"❌ فشل تعيين كلمة المرور: {e}"
