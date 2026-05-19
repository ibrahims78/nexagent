"""Tests for vpn_manager.py — non-Windows tests skip gracefully."""
import sys
import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="VPN tests require Windows"
)


def test_generate_psk_length():
    from src.pc_control.vpn_manager import _generate_psk
    psk = _generate_psk(32)
    assert len(psk) == 32


def test_generate_password_length():
    from src.pc_control.vpn_manager import _generate_password
    pwd = _generate_password(14)
    assert len(pwd) == 14


def test_get_local_ip():
    from src.pc_control.vpn_manager import get_local_ip
    ip = get_local_ip()
    assert ip and "." in ip


def test_windows_edition_check():
    from src.pc_control.vpn_manager import check_windows_edition
    result = check_windows_edition()
    assert "supported" in result
    assert "edition" in result


def test_vpn_commands_in_whitelist():
    from src.pc_control.command_whitelist import COMMAND_REGISTRY
    for cmd in ["vpn_server_enable", "vpn_server_disable",
                "vpn_server_status", "vpn_client_list"]:
        assert cmd in COMMAND_REGISTRY, f"{cmd} missing from whitelist"
