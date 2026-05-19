"""
Tests for src/utils/config.py
Covers: save/load round-trip, encryption activation, deep_merge, default completeness.
"""
import json
import os
import sys
import pytest
from pathlib import Path

# Allow imports from pc-commander root
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Redirect CONFIG_DIR to a temp directory for every test."""
    import src.utils.config as cfg_mod
    test_dir = tmp_path / "PCCommander"
    test_dir.mkdir(parents=True)
    monkeypatch.setattr(cfg_mod, "CONFIG_DIR", test_dir)
    monkeypatch.setattr(cfg_mod, "CONFIG_FILE", test_dir / "config.json")
    monkeypatch.setattr(cfg_mod, "KEY_FILE", test_dir / "secret.key")
    yield test_dir


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_save_and_load_config():
    """Saved config must round-trip back to the same plaintext values."""
    from src.utils.config import save_config, load_config, DEFAULT_CONFIG
    import copy

    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["telegram"]["bot_token"] = "test-token-123"
    cfg["ai"]["openai_key"] = "sk-test-key"

    save_config(cfg)
    loaded = load_config()

    assert loaded["telegram"]["bot_token"] == "test-token-123"
    assert loaded["ai"]["openai_key"] == "sk-test-key"


def test_encryption_activated(isolated_config):
    """
    Raw JSON on disk must NOT contain plaintext sensitive values.
    The _encrypted flag must be True.
    """
    from src.utils.config import save_config, DEFAULT_CONFIG
    import copy

    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["telegram"]["bot_token"] = "plaintext-token"
    cfg["ai"]["gemini_key"] = "plaintext-gemini-key"

    save_config(cfg)

    config_file = isolated_config / "config.json"
    raw = config_file.read_text(encoding="utf-8")
    data = json.loads(raw)

    assert data.get("_encrypted") is True, "_encrypted flag must be True in saved JSON"
    assert "plaintext-token" not in raw, "Bot token must not appear in plaintext"
    assert "plaintext-gemini-key" not in raw, "Gemini key must not appear in plaintext"


def test_deep_merge():
    """deep_merge should recursively override nested keys without wiping siblings."""
    from src.utils.config import deep_merge

    base = {"a": {"x": 1, "y": 2}, "b": 3}
    override = {"a": {"y": 99, "z": 7}}
    deep_merge(base, override)

    assert base["a"]["x"] == 1
    assert base["a"]["y"] == 99
    assert base["a"]["z"] == 7
    assert base["b"] == 3


def test_default_config_complete():
    """DEFAULT_CONFIG must contain all required top-level sections."""
    from src.utils.config import DEFAULT_CONFIG

    required_sections = [
        "telegram", "ai", "tunnel", "general",
        "monitoring", "anydesk", "wol", "security", "stream",
        "server", "vpn",
    ]
    for section in required_sections:
        assert section in DEFAULT_CONFIG, f"Missing section: {section}"

    assert DEFAULT_CONFIG["ai"]["model_gemini"] == "gemini-1.5-flash"
    assert "lan_access" in DEFAULT_CONFIG["server"], "server.lan_access missing"
    assert "use_webhook" in DEFAULT_CONFIG["tunnel"], "tunnel.use_webhook missing"
    assert "webhook_url" in DEFAULT_CONFIG["tunnel"], "tunnel.webhook_url missing"


def test_load_config_returns_defaults_when_no_file(isolated_config):
    """load_config on a fresh directory must return DEFAULT_CONFIG values."""
    config_file = isolated_config / "config.json"
    if config_file.exists():
        config_file.unlink()

    from src.utils.config import load_config, DEFAULT_CONFIG
    loaded = load_config()

    assert loaded["ai"]["provider"] == DEFAULT_CONFIG["ai"]["provider"]
    assert loaded["security"]["require_pin"] == DEFAULT_CONFIG["security"]["require_pin"]
