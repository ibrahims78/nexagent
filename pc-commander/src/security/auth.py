import hashlib
import secrets
import json
from pathlib import Path
from src.utils.config import get_config_dir

AUTH_FILE = get_config_dir() / "auth.json"


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_user(user_id: int, allowed_users: list) -> bool:
    if not allowed_users:
        return True
    return user_id in [int(u) for u in allowed_users if str(u).strip()]


def get_my_telegram_id(bot_token: str) -> str:
    try:
        import requests
        response = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getUpdates",
            timeout=5
        )
        data = response.json()
        if data.get("ok") and data.get("result"):
            for update in data["result"]:
                msg = update.get("message") or update.get("edited_message")
                if msg and msg.get("from"):
                    return str(msg["from"]["id"])
    except Exception:
        pass
    return None


def validate_telegram_token(token: str) -> dict:
    try:
        import requests
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=10
        )
        data = response.json()
        if data.get("ok"):
            return {"valid": True, "bot_name": data["result"]["first_name"], "username": data["result"]["username"]}
        return {"valid": False, "error": data.get("description", "رمز غير صالح")}
    except Exception as e:
        return {"valid": False, "error": str(e)}
