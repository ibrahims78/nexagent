"""Tests for file_manager path traversal protection."""
import sys
import os
import platform
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pc_control.file_manager import is_safe_path, list_directory, delete_file


def test_safe_path_home_dir():
    assert is_safe_path(os.path.expanduser("~")) is True


def test_safe_path_blocks_system_root():
    if platform.system() == "Windows":
        assert is_safe_path("C:\\Windows\\System32") is False
    else:
        assert is_safe_path("/etc/passwd") is False
        assert is_safe_path("/root") is False


def test_safe_path_blocks_traversal():
    home = os.path.expanduser("~")
    traversal = home + "/../../etc"
    assert is_safe_path(traversal) is False


def test_safe_path_blocks_empty_string():
    assert is_safe_path("") is False
    assert is_safe_path("   ") is False


def test_list_directory_rejects_system_path():
    if platform.system() == "Windows":
        result = list_directory("C:\\Windows\\System32")
    else:
        result = list_directory("/etc")
    assert "مرفوض" in result or "rejected" in result.lower() or "❌" in result


def test_delete_file_rejects_system_path():
    if platform.system() == "Windows":
        result = delete_file("C:\\Windows\\system.ini")
    else:
        result = delete_file("/etc/passwd")
    assert "مرفوض" in result or "❌" in result
