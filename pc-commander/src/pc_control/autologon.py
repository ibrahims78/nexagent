import sys
import subprocess
import os
import hashlib
import urllib.request
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger()
IS_WINDOWS = sys.platform == "win32"

AUTOLOGON_URL = "https://live.sysinternals.com/Autologon.exe"
AUTOLOGON_PATH = Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "PCCommander" / "Autologon.exe"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_autologon() -> bool:
    try:
        AUTOLOGON_PATH.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(AUTOLOGON_URL, str(AUTOLOGON_PATH))
        if AUTOLOGON_PATH.exists():
            file_size = AUTOLOGON_PATH.stat().st_size
            if file_size < 100_000 or file_size > 2_000_000:
                logger.error(f"Autologon.exe unexpected size: {file_size} bytes")
                AUTOLOGON_PATH.unlink(missing_ok=True)
                return False
            actual_hash = _sha256_file(AUTOLOGON_PATH)
            from src.utils.config import get_config_dir
            hash_file = get_config_dir() / "autologon_hash.txt"
            if hash_file.exists():
                known = hash_file.read_text().strip()
                if known != actual_hash:
                    logger.warning(
                        f"Autologon.exe hash CHANGED: was {known}, now {actual_hash}. "
                        "This may indicate a legitimate update from Sysinternals or tampering. "
                        "Delete autologon_hash.txt to accept the new version."
                    )
                    AUTOLOGON_PATH.unlink(missing_ok=True)
                    return False
            else:
                hash_file.write_text(actual_hash)
                logger.info(f"Autologon.exe hash stored for future verification: {actual_hash}")
        return AUTOLOGON_PATH.exists()
    except Exception as e:
        logger.error(f"Failed to download Autologon: {e}")
        return False


def setup_autologon(username: str, password: str, domain: str = "") -> str:
    if not IS_WINDOWS:
        return "❌ هذه الميزة لويندوز فقط"

    if not AUTOLOGON_PATH.exists():
        if not download_autologon():
            return "❌ فشل تحميل أداة Autologon"

    try:
        if not domain:
            domain = os.environ.get("USERDOMAIN", os.environ.get("COMPUTERNAME", "."))

        result = subprocess.run(
            [str(AUTOLOGON_PATH), username, domain, "/accepteula"],
            input=password,
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            logger.info("Autologon configured successfully")
            return "✅ تم ضبط تسجيل الدخول التلقائي بنجاح!\nسيدخل الحاسب تلقائياً عند الإقلاع."
        return f"❌ فشل الضبط: {result.stderr or result.stdout}"
    except Exception as e:
        return f"❌ خطأ: {e}"


def disable_autologon() -> str:
    if not IS_WINDOWS:
        return "❌ هذه الميزة لويندوز فقط"
    try:
        if IS_WINDOWS:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "AutoAdminLogon", 0, winreg.REG_SZ, "0")
            winreg.SetValueEx(key, "DefaultPassword", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
        return "✅ تم إلغاء تسجيل الدخول التلقائي"
    except Exception as e:
        return f"❌ خطأ: {e}"


def is_autologon_enabled() -> bool:
    if not IS_WINDOWS:
        return False
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
            0, winreg.KEY_READ
        )
        val, _ = winreg.QueryValueEx(key, "AutoAdminLogon")
        winreg.CloseKey(key)
        return val == "1"
    except Exception:
        return False


def get_current_username() -> str:
    return os.environ.get("USERNAME", os.environ.get("USER", ""))


def get_current_domain() -> str:
    return os.environ.get("USERDOMAIN", os.environ.get("COMPUTERNAME", ""))
