import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
import base64

CONFIG_DIR = Path(os.environ.get("APPDATA", ".")) / "PCCommander"
CONFIG_FILE = CONFIG_DIR / "config.json"
KEY_FILE = CONFIG_DIR / "secret.key"

DEFAULT_CONFIG = {
    "telegram": {
        "bot_token": "",
        "allowed_users": []
    },
    "ai": {
        "provider": "openai",
        "openai_key": "",
        "gemini_key": "",
        "model_openai": "gpt-4o",
        "model_gemini": "gemini-pro"
    },
    "tunnel": {
        "provider": "cloudflare",
        "ngrok_token": "",
        "cloudflare_tunnel_id": ""
    },
    "general": {
        "language": "ar",
        "start_with_windows": False,
        "do_not_disturb": False,
        "daily_report_time": "08:00",
        "daily_report_enabled": True
    },
    "monitoring": {
        "cpu_alert_threshold": 90,
        "ram_alert_threshold": 90,
        "temp_alert_threshold": 80,
        "disk_alert_threshold": 90
    },
    "anydesk": {
        "path": "C:\\Program Files (x86)\\AnyDesk\\AnyDesk.exe",
        "auto_accept": False
    },
    "wol": {
        "mac_address": "",
        "broadcast_ip": "255.255.255.255",
        "pc_ip": "",
        "backup_users": [],
        "auto_notify_backup": True,
        "monitor_startup": True
    },
    "security": {
        "log_commands": True,
        "notify_on_unauthorized": True,
        "require_pin": False,
        "session_pin": "",
        "watchdog_enabled": True
    },
    "stream": {
        "enabled": False,
        "port": 8765,
        "password": "pccommander",
        "fps": 5,
        "quality": 60,
        "scale": 0.8
    }
}


def get_or_create_key():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if KEY_FILE.exists():
        with open(KEY_FILE, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key


def encrypt_value(value: str) -> str:
    if not value:
        return value
    key = get_or_create_key()
    f = Fernet(key)
    return f.encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    if not value:
        return value
    try:
        key = get_or_create_key()
        f = Fernet(key)
        return f.decrypt(value.encode()).decode()
    except Exception:
        return value


def load_config() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_CONFIG.copy()
        deep_merge(merged, data)
        return merged
    except Exception:
        return DEFAULT_CONFIG.copy()


def deep_merge(base: dict, override: dict):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_logs_dir() -> Path:
    logs_dir = CONFIG_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR
