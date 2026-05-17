"""
Tests for src/utils/security_auth.py
Covers: whitelist, rate-limit, block/unblock, PIN verify, session lifecycle.
"""
import sys
import time
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import src.utils.security_auth as sa


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config(require_pin: bool = False, pin: str = "1234") -> dict:
    return {
        "telegram": {"allowed_users": [111, 222]},
        "security": {
            "require_pin": require_pin,
            "session_pin": pin,
        }
    }


def _reset():
    """Clear all in-memory auth state between tests."""
    sa._sessions.clear()
    sa._pending_pin.clear()
    sa._rate_limits.clear()
    sa._blocked_users.clear()


@pytest.fixture(autouse=True)
def clean_state():
    _reset()
    yield
    _reset()


# ---------------------------------------------------------------------------
# Whitelist
# ---------------------------------------------------------------------------

def test_is_allowed_user_in_list():
    assert sa.is_allowed_user(111, _config()) is True


def test_is_allowed_user_not_in_list():
    assert sa.is_allowed_user(999, _config()) is False


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def test_rate_limit_not_triggered():
    """First 29 requests must not be rate-limited."""
    for _ in range(sa.RATE_LIMIT_MAX - 1):
        assert sa.is_rate_limited(555) is False


def test_rate_limit_triggered():
    """Request number RATE_LIMIT_MAX+1 must be rate-limited."""
    for _ in range(sa.RATE_LIMIT_MAX):
        sa.is_rate_limited(666)
    assert sa.is_rate_limited(666) is True


# ---------------------------------------------------------------------------
# Block / unblock
# ---------------------------------------------------------------------------

def test_block_and_unblock():
    sa.block_user(777)
    assert sa.is_blocked(777) is True

    sa.unblock_user(777)
    assert sa.is_blocked(777) is False


# ---------------------------------------------------------------------------
# PIN verification
# ---------------------------------------------------------------------------

def test_pin_verify_correct():
    sa.request_pin_auth(111, _config(require_pin=True))
    result = sa.verify_pin(111, "1234", _config(require_pin=True))
    assert result == "OK"
    assert sa.is_session_valid(111, _config(require_pin=True)) is True


def test_pin_verify_wrong():
    sa.request_pin_auth(111, _config(require_pin=True))
    result = sa.verify_pin(111, "0000", _config(require_pin=True))
    assert result.startswith("WRONG:")


def test_pin_verify_expired(monkeypatch):
    sa.request_pin_auth(111, _config(require_pin=True))
    # Force expiry by back-dating the pending entry
    with sa._lock:
        sa._pending_pin[111]["expires_at"] = time.time() - 1
    result = sa.verify_pin(111, "1234", _config(require_pin=True))
    assert result == "EXPIRED"


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------

def test_session_created_and_valid():
    sa.create_session(333)
    assert sa.is_session_valid(333, _config(require_pin=True)) is True


def test_session_expired(monkeypatch):
    sa.create_session(444)
    with sa._lock:
        sa._sessions[444]["created_at"] = time.time() - (sa.SESSION_TIMEOUT + 1)
    assert sa.is_session_valid(444, _config(require_pin=True)) is False
