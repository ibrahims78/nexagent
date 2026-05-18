# Compatibility shim — import from canonical location
from src.security.auth import (
    check_authorization,
    is_allowed_user,
    is_rate_limited,
    is_blocked,
    block_user,
    unblock_user,
    is_session_valid,
    create_session,
    refresh_session,
    invalidate_session,
    request_pin_auth,
    verify_pin,
    is_waiting_pin,
    get_security_report,
    validate_telegram_token,
    # Internal state — re-exported so tests can reset between runs
    _sessions,
    _pending_pin,
    _rate_limits,
    _blocked_users,
    _lock,
    # Constants
    SESSION_TIMEOUT,
    IDLE_TIMEOUT,
    PIN_TIMEOUT,
    RATE_LIMIT_WINDOW,
    RATE_LIMIT_MAX,
    MAX_PIN_ATTEMPTS,
)

__all__ = [
    "check_authorization", "is_allowed_user", "is_rate_limited",
    "is_blocked", "block_user", "unblock_user", "is_session_valid",
    "create_session", "refresh_session", "invalidate_session",
    "request_pin_auth", "verify_pin", "is_waiting_pin",
    "get_security_report", "validate_telegram_token",
    "_sessions", "_pending_pin", "_rate_limits", "_blocked_users", "_lock",
    "SESSION_TIMEOUT", "IDLE_TIMEOUT", "PIN_TIMEOUT",
    "RATE_LIMIT_WINDOW", "RATE_LIMIT_MAX", "MAX_PIN_ATTEMPTS",
]
