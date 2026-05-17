"""
Tests for src/bot/commands.py
Covers: screenshot, system_status, unknown command, vision handler guard.
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

import src.bot.commands as cmd_mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_vision_handler():
    """Ensure _vision_handler is None before each test."""
    cmd_mod._vision_handler = None
    yield
    cmd_mod._vision_handler = None


SAMPLE_CONFIG = {
    "ai": {"provider": "openai", "openai_key": ""},
    "anydesk": {"path": ""},
    "wol": {"pc_ip": ""},
    "security": {"log_commands": False, "require_pin": False},
    "general": {"do_not_disturb": False},
    "stream": {"enabled": False},
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_screenshot_command():
    """screenshot command must return a non-empty result_text and a file path."""
    fake_path = "/tmp/fake_screenshot.png"
    with patch("src.pc_control.screenshot.take_screenshot_file", return_value=fake_path):
        result_text, result_file = cmd_mod.execute_command("screenshot", [], SAMPLE_CONFIG)

    assert result_text != ""
    assert result_file == fake_path


def test_system_status_command():
    """system_status must return a non-empty status string."""
    fake_status = "CPU: 10% | RAM: 40%"
    with patch("src.pc_control.system_monitor.get_system_status", return_value=fake_status):
        result_text, result_file = cmd_mod.execute_command(
            "system_status", [], SAMPLE_CONFIG
        )

    assert result_text == fake_status
    assert result_file is None


def test_unknown_command_returns_error():
    """Unrecognised commands must return a warning string, not raise."""
    result_text, result_file = cmd_mod.execute_command(
        "this_does_not_exist", [], SAMPLE_CONFIG
    )

    assert "غير معروف" in result_text or "unknown" in result_text.lower()
    assert result_file is None


def test_vision_handler_not_set_vision_do():
    """vision_do with no handler must return an Arabic error, not raise."""
    result_text, result_file = cmd_mod.execute_command(
        "vision_do", ["افتح المتصفح"], SAMPLE_CONFIG
    )

    assert "❌" in result_text
    assert result_file is None


def test_vision_handler_not_set_vision_describe():
    """vision_describe with no handler must return an Arabic error, not raise."""
    result_text, _ = cmd_mod.execute_command(
        "vision_describe", [], SAMPLE_CONFIG
    )
    assert "❌" in result_text


def test_set_vision_handler_stores_handler():
    """set_vision_handler must update the module-level _vision_handler."""
    fake_handler = MagicMock()
    cmd_mod.set_vision_handler(fake_handler)
    assert cmd_mod._vision_handler is fake_handler


def test_chat_command_returns_args():
    """chat command must echo back the first arg as result_text."""
    result_text, result_file = cmd_mod.execute_command(
        "chat", ["مرحبا"], SAMPLE_CONFIG
    )
    assert result_text == "مرحبا"
    assert result_file is None
