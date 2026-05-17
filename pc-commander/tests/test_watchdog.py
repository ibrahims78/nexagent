"""
Tests for src/utils/watchdog.py
Covers: socket context manager usage, internet availability detection.
"""
import sys
import socket
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

import src.utils.watchdog as wd


# ---------------------------------------------------------------------------
# _is_internet_available
# ---------------------------------------------------------------------------

def test_internet_available_returns_true():
    """When socket.connect succeeds, must return True."""
    mock_sock = MagicMock()
    mock_sock.__enter__ = lambda s: s
    mock_sock.__exit__ = MagicMock(return_value=False)

    with patch("src.utils.watchdog.socket.socket", return_value=mock_sock):
        result = wd._is_internet_available()

    assert result is True


def test_internet_unavailable_returns_false():
    """When socket.connect raises an exception, must return False."""
    mock_sock = MagicMock()
    mock_sock.__enter__ = lambda s: s
    mock_sock.__exit__ = MagicMock(return_value=False)
    mock_sock.connect.side_effect = OSError("unreachable")

    with patch("src.utils.watchdog.socket.socket", return_value=mock_sock):
        result = wd._is_internet_available()

    assert result is False


def test_socket_closed_after_check():
    """
    The socket must be used as a context manager so it is always closed,
    i.e. __exit__ must be called exactly once.
    """
    mock_sock = MagicMock()
    mock_sock.__enter__ = lambda s: s
    mock_sock.__exit__ = MagicMock(return_value=False)

    with patch("src.utils.watchdog.socket.socket", return_value=mock_sock):
        wd._is_internet_available()

    mock_sock.__exit__.assert_called_once()


# ---------------------------------------------------------------------------
# start / stop lifecycle
# ---------------------------------------------------------------------------

def test_start_watchdog_sets_running():
    """start_watchdog must set _running to True."""
    wd._running = False

    dummy_bot = lambda: None
    dummy_cfg = lambda: {}
    dummy_restart = lambda: None

    wd.start_watchdog(dummy_bot, dummy_cfg, dummy_restart)
    assert wd.is_running() is True

    # Cleanup
    wd.stop_watchdog()


def test_stop_watchdog_clears_running():
    """stop_watchdog must set _running to False."""
    wd._running = True
    wd.stop_watchdog()
    assert wd.is_running() is False
