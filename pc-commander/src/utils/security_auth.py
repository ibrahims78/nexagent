"""
PC Commander - Security & Authorization
طبقات الأمان: User ID + PIN + Session + Rate Limiting
"""
import json
import time
import hashlib
import hmac
import os
import secrets
import threading
from collections import defaultdict
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger()

_sessions: dict[int, dict] = {}
_pending_pin: dict[int, dict] = {}
_rate_limits: dict[int, list] = defaultdict(list)
_blocked_users: set[int] = set()
_lock = threading.Lock()

SESSION_TIMEOUT    = 3600
IDLE_TIMEOUT       = 1800
PIN_TIMEOUT        = 120
RATE_LIMIT_WINDOW  = 60
RATE_LIMIT_MAX     = 30
MAX_PIN_ATTEMPTS   = 3


def _get_state_file() -> Path:
    from src.utils.config import get_config_dir
    return get_config_dir() / "security_state.json"


def _load_state():
    """Load persisted security state (blocked users) from disk on startup."""
    global _blocked_users
    state_file = _get_state_file()
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            _blocked_users = set(int(u) for u in data.get("blocked_users", []))
            logger.info(f"Security state loaded: {len(_blocked_users)} blocked user(s)")
        except Exception as e:
            logger.warning(f"Failed to load security state: {e}")


def _save_state():
    """Persist the current blocked users list to disk."""
    try:
        state_file = _get_state_file()
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"blocked_users": list(_blocked_users)}, f)
    except Exception as e:
        logger.warning(f"Failed to save security state: {e}")


_load_state()


_PIN_SALT = b"nexagent-pin-v1"


def _hash_pin(pin: str, salt: bytes = _PIN_SALT) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 100_000).hex()


def is_allowed_user(user_id: int, config: dict) -> bool:
    allowed = config.get("telegram", {}).get("allowed_users", [])
    if not allowed:
        return False
    return str(user_id) in [str(u) for u in allowed]


def is_rate_limited(user_id: int) -> bool:
    with _lock:
        now = time.time()
        events = [t for t in _rate_limits[user_id] if now - t < RATE_LIMIT_WINDOW]
        _rate_limits[user_id] = events
        if len(events) >= RATE_LIMIT_MAX:
            return True
        _rate_limits[user_id].append(now)
        return False


def is_blocked(user_id: int) -> bool:
    return user_id in _blocked_users


def block_user(user_id: int):
    _blocked_users.add(user_id)
    _save_state()
    logger.warning(f"User blocked: {user_id}")


def unblock_user(user_id: int):
    _blocked_users.discard(user_id)
    _save_state()
    logger.info(f"User unblocked: {user_id}")


def is_session_valid(user_id: int, config: dict) -> bool:
    security = config.get("security", {})
    pin_required = security.get("require_pin", False)
    if not pin_required:
        return True
    with _lock:
        session = _sessions.get(user_id)
        if not session:
            return False
        now = time.time()
        if now - session["created_at"] > SESSION_TIMEOUT:
            del _sessions[user_id]
            return False
        if now - session.get("last_activity", session["created_at"]) > IDLE_TIMEOUT:
            del _sessions[user_id]
            return False
        return True


def create_session(user_id: int):
    with _lock:
        now = time.time()
        _sessions[user_id] = {
            "created_at": now,
            "last_activity": now,
            "token": secrets.token_hex(16)
        }


def refresh_session(user_id: int):
    """Update last_activity timestamp to keep the session alive."""
    with _lock:
        session = _sessions.get(user_id)
        if session:
            session["last_activity"] = time.time()


def invalidate_session(user_id: int):
    with _lock:
        _sessions.pop(user_id, None)


def request_pin_auth(user_id: int, config: dict) -> str:
    pin = config.get("security", {}).get("session_pin", "")
    if not pin:
        create_session(user_id)
        return "SESSION_CREATED"
    with _lock:
        now = time.time()
        expired = [uid for uid, p in list(_pending_pin.items())
                   if now > p.get("expires_at", 0)]
        for uid in expired:
            del _pending_pin[uid]
        _pending_pin[user_id] = {
            "expires_at": now + PIN_TIMEOUT,
            "attempts": 0
        }
    return "PIN_REQUIRED"


def verify_pin(user_id: int, entered_pin: str, config: dict) -> str:
    stored_pin = config.get("security", {}).get("session_pin", "")
    pin_hash = _hash_pin(stored_pin)
    entered_hash = _hash_pin(entered_pin.strip())

    with _lock:
        pending = _pending_pin.get(user_id)
        if not pending:
            return "NO_PENDING"
        if time.time() > pending["expires_at"]:
            del _pending_pin[user_id]
            return "EXPIRED"
        if not hmac.compare_digest(entered_hash, pin_hash):
            pending["attempts"] += 1
            if pending["attempts"] >= MAX_PIN_ATTEMPTS:
                del _pending_pin[user_id]
                block_user(user_id)
                logger.warning(f"User {user_id} blocked after {MAX_PIN_ATTEMPTS} failed PIN attempts")
                return "BLOCKED"
            return f"WRONG:{MAX_PIN_ATTEMPTS - pending['attempts']}"
        del _pending_pin[user_id]

    create_session(user_id)
    logger.info(f"New session created for user {user_id}")
    return "OK"


def is_waiting_pin(user_id: int) -> bool:
    with _lock:
        pending = _pending_pin.get(user_id)
        if not pending:
            return False
        if time.time() > pending["expires_at"]:
            del _pending_pin[user_id]
            return False
        return True


def check_authorization(user_id: int, config: dict) -> tuple[bool, str]:
    """
    يتحقق من صلاحية المستخدم بالترتيب:
    1. هل هو في قائمة allowed_users؟
    2. هل هو محجوب؟
    3. هل تجاوز حد الطلبات؟
    4. هل لديه جلسة نشطة (إذا كان PIN مفعّلاً)؟
    """
    if not is_allowed_user(user_id, config):
        logger.warning(f"Unauthorized access attempt: {user_id}")
        return False, "NOT_ALLOWED"

    if is_blocked(user_id):
        return False, "BLOCKED"

    if is_rate_limited(user_id):
        logger.warning(f"Rate limit exceeded for user {user_id}")
        return False, "RATE_LIMITED"

    if not is_session_valid(user_id, config):
        return False, "NO_SESSION"

    return True, "OK"


def get_security_report(config: dict) -> str:
    security = config.get("security", {})
    allowed  = config.get("telegram", {}).get("allowed_users", [])
    pin_on   = security.get("require_pin", False)
    active   = len(_sessions)
    blocked  = len(_blocked_users)

    lines = [
        "🔒 **تقرير الأمان**\n",
        f"👤 المستخدمون المصرّح لهم: {len(allowed)} شخص",
        f"🔑 رمز PIN: {'✅ مفعّل' if pin_on else '❌ غير مفعّل'}",
        f"🟢 الجلسات النشطة: {active}",
        f"🚫 المحجوبون: {blocked}",
        f"⏱ انتهاء الجلسة بعد: {SESSION_TIMEOUT // 60} دقيقة",
        f"⏱ انتهاء الجلسة بعد خمول: {IDLE_TIMEOUT // 60} دقيقة",
        f"🛡 حد الطلبات: {RATE_LIMIT_MAX} أمر / دقيقة",
    ]
    if blocked > 0:
        lines.append(f"\nالمحجوبون: {', '.join(str(u) for u in _blocked_users)}")
    return "\n".join(lines)


def validate_telegram_token(token: str) -> dict:
    """Validate a Telegram bot token via the getMe API (stdlib only)."""
    import urllib.request
    import urllib.error
    import json as _json
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = _json.loads(resp.read())
        if data.get("ok"):
            bot = data["result"]
            return {
                "valid": True,
                "bot_name": bot.get("first_name", ""),
                "username": bot.get("username", ""),
            }
        return {"valid": False, "error": "استجابة غير صحيحة من Telegram"}
    except urllib.error.HTTPError as e:
        return {"valid": False, "error": f"HTTP {e.code}: Token غير صالح"}
    except Exception as e:
        return {"valid": False, "error": str(e)}
