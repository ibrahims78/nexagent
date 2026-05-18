import json
import os
import stat
from pathlib import Path
from cryptography.fernet import Fernet

CONFIG_DIR = Path(os.environ.get("APPDATA", ".")) / "PCCommander"
CONFIG_FILE = CONFIG_DIR / "config.json"
KEY_FILE = CONFIG_DIR / "secret.key"

_SENSITIVE_FIELDS = [
    ("telegram", "bot_token"),
    ("ai", "openai_key"),
    ("ai", "gemini_key"),
    ("tunnel", "ngrok_token"),
    ("security", "session_pin"),
    ("stream", "password"),
]

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
        "model_gemini": "gemini-1.5-flash"
    },
    "tunnel": {
        "provider": "cloudflare",
        "ngrok_token": "",
        "cloudflare_tunnel_id": ""
    },
    "general": {
        "language": "ar",
        "timezone": "Asia/Riyadh",
        "start_with_windows": False,
        "do_not_disturb": False,
        "daily_report_time": "08:00",
        "daily_report_enabled": True,
        "extra_allowed_apps": []
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
        "password": "",
        "fps": 5,
        "quality": 60,
        "scale": 0.8
    },
    "key_source": "appdata"
}


def get_or_create_key() -> bytes:
    """
    Return the Fernet key.

    KEY_SOURCE = "env"    → read from NEXAGENT_SECRET_KEY environment variable.
    KEY_SOURCE = "appdata" (default) → generate/persist in APPDATA key file
                           with 600 permissions (owner read/write only).
    """
    key_source = os.environ.get("NEXAGENT_KEY_SOURCE", "appdata")

    if key_source == "env":
        env_key = os.environ.get("NEXAGENT_SECRET_KEY", "")
        if not env_key:
            raise RuntimeError(
                "KEY_SOURCE is 'env' but NEXAGENT_SECRET_KEY environment variable is not set."
            )
        return env_key.encode() if isinstance(env_key, str) else env_key

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if KEY_FILE.exists():
        with open(KEY_FILE, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    try:
        os.chmod(KEY_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass
    return key


def encrypt_value(value: str) -> str:
    """Encrypt a plaintext string using the local Fernet key."""
    if not value:
        return value
    key = get_or_create_key()
    f = Fernet(key)
    return f.encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    """Decrypt a Fernet-encrypted string; return value unchanged on failure."""
    if not value:
        return value
    try:
        key = get_or_create_key()
        f = Fernet(key)
        return f.decrypt(value.encode()).decode()
    except Exception:
        return value


def _get_nested(d: dict, section: str, key: str) -> str:
    """Safely retrieve a nested config value."""
    return d.get(section, {}).get(key, "")


def _set_nested(d: dict, section: str, key: str, value: str):
    """Safely set a nested config value."""
    if section in d:
        d[section][key] = value


def load_config() -> dict:
    """Load config from disk, decrypting sensitive fields if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_CONFIG.copy()
        deep_merge(merged, data)

        if data.get("_encrypted") is True:
            for section, key in _SENSITIVE_FIELDS:
                raw = _get_nested(merged, section, key)
                if raw:
                    _set_nested(merged, section, key, decrypt_value(raw))

        return merged
    except Exception:
        return DEFAULT_CONFIG.copy()


def deep_merge(base: dict, override: dict):
    """Recursively merge override into base in-place."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


def save_config(config: dict):
    """Encrypt sensitive fields and persist config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    import copy
    data = copy.deepcopy(config)

    for section, key in _SENSITIVE_FIELDS:
        raw = _get_nested(data, section, key)
        if raw:
            _set_nested(data, section, key, encrypt_value(raw))

    data["_encrypted"] = True

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_logs_dir() -> Path:
    """Return (and create) the logs directory."""
    logs_dir = CONFIG_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_config_dir() -> Path:
    """Return (and create) the config directory."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR
