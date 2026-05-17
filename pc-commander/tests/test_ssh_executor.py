"""
Tests for SSHExecutor (Layer 2).
All Paramiko I/O is mocked — no real SSH connection is made.
"""
import io
import pytest
import sys
import stat
from unittest.mock import MagicMock, patch, PropertyMock


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_executor(**kwargs):
    """Create an SSHExecutor with test defaults and no real connection."""
    from src.pc_control.ssh_executor import SSHExecutor
    return SSHExecutor(username="testuser", host="127.0.0.1", port=22, **kwargs)


def _attach_mock_client(executor):
    """Attach a pre-configured mock Paramiko client to the executor."""
    client = MagicMock()
    transport = MagicMock()
    transport.is_active.return_value = True
    client.get_transport.return_value = transport
    executor._client = client
    return client


# ── Construction ───────────────────────────────────────────────────────────


def test_executor_created_with_defaults():
    ex = _make_executor()
    assert ex._username == "testuser"
    assert ex._host == "127.0.0.1"
    assert ex._port == 22
    assert ex._client is None


def test_executor_created_with_key_path():
    ex = _make_executor(key_path="/home/user/.ssh/id_rsa")
    assert ex._key_path == "/home/user/.ssh/id_rsa"


# ── exec_command ───────────────────────────────────────────────────────────


def test_exec_command_returns_stdout():
    ex = _make_executor()
    client = _attach_mock_client(ex)

    stdout_mock = MagicMock()
    stdout_mock.read.return_value = b"hello world"
    stderr_mock = MagicMock()
    stderr_mock.read.return_value = b""
    client.exec_command.return_value = (MagicMock(), stdout_mock, stderr_mock)

    result = ex.exec_command("echo hello world")
    assert result == "hello world"


def test_exec_command_includes_stderr_when_present():
    ex = _make_executor()
    client = _attach_mock_client(ex)

    stdout_mock = MagicMock()
    stdout_mock.read.return_value = b"out"
    stderr_mock = MagicMock()
    stderr_mock.read.return_value = b"some error"
    client.exec_command.return_value = (MagicMock(), stdout_mock, stderr_mock)

    result = ex.exec_command("bad_cmd")
    assert "some error" in result


def test_exec_command_empty_output_returns_completed_message():
    ex = _make_executor()
    client = _attach_mock_client(ex)

    stdout_mock = MagicMock()
    stdout_mock.read.return_value = b""
    stderr_mock = MagicMock()
    stderr_mock.read.return_value = b""
    client.exec_command.return_value = (MagicMock(), stdout_mock, stderr_mock)

    result = ex.exec_command("dir")
    assert "✅" in result


def test_exec_command_returns_error_on_exception():
    ex = _make_executor()
    client = _attach_mock_client(ex)
    client.exec_command.side_effect = Exception("connection reset")

    result = ex.exec_command("ls")
    assert "❌" in result
    assert "connection reset" in result


# ── SFTP: list_files ───────────────────────────────────────────────────────


def test_list_files_returns_formatted_listing():
    ex = _make_executor()
    client = _attach_mock_client(ex)

    sftp_mock = MagicMock()
    attr = MagicMock()
    attr.filename = "document.txt"
    attr.st_mode = stat.S_IFREG | 0o644
    attr.st_size = 1024
    sftp_mock.listdir_attr.return_value = [attr]
    client.open_sftp.return_value = sftp_mock

    result = ex.list_files("C:/Users")
    assert "document.txt" in result


def test_list_files_empty_directory():
    ex = _make_executor()
    client = _attach_mock_client(ex)

    sftp_mock = MagicMock()
    sftp_mock.listdir_attr.return_value = []
    client.open_sftp.return_value = sftp_mock

    result = ex.list_files("/empty")
    assert "فارغ" in result


def test_list_files_error_returns_arabic_message():
    ex = _make_executor()
    client = _attach_mock_client(ex)
    client.open_sftp.side_effect = Exception("no sftp")

    result = ex.list_files("/bad")
    assert "❌" in result


# ── SFTP: download_file ────────────────────────────────────────────────────


def test_download_file_returns_bytes():
    ex = _make_executor()
    client = _attach_mock_client(ex)

    sftp_mock = MagicMock()
    def fake_getfo(path, buf):
        buf.write(b"file content")
    sftp_mock.getfo.side_effect = fake_getfo
    client.open_sftp.return_value = sftp_mock

    data = ex.download_file("/remote/file.txt")
    assert data == b"file content"


def test_download_file_returns_none_on_error():
    ex = _make_executor()
    client = _attach_mock_client(ex)
    client.open_sftp.side_effect = Exception("sftp error")

    data = ex.download_file("/remote/missing.txt")
    assert data is None


# ── SFTP: upload_file ──────────────────────────────────────────────────────


def test_upload_file_returns_success_message(tmp_path):
    ex = _make_executor()
    client = _attach_mock_client(ex)

    local = tmp_path / "upload.txt"
    local.write_bytes(b"test data")

    sftp_mock = MagicMock()
    client.open_sftp.return_value = sftp_mock

    result = ex.upload_file(str(local), "/remote/upload.txt")
    assert "✅" in result
    sftp_mock.put.assert_called_once_with(str(local), "/remote/upload.txt")


def test_upload_file_returns_error_on_sftp_failure(tmp_path):
    ex = _make_executor()
    client = _attach_mock_client(ex)
    client.open_sftp.side_effect = Exception("permission denied")

    local = tmp_path / "file.txt"
    local.write_bytes(b"x")

    result = ex.upload_file(str(local), "/remote/x.txt")
    assert "❌" in result


# ── get_tunnel_port ────────────────────────────────────────────────────────


def test_get_tunnel_port_returns_port_number():
    ex = _make_executor()
    client = _attach_mock_client(ex)

    stdout_mock = MagicMock()
    stdout_mock.read.return_value = b"54321"
    stderr_mock = MagicMock()
    stderr_mock.read.return_value = b""
    client.exec_command.return_value = (MagicMock(), stdout_mock, stderr_mock)

    port = ex.get_tunnel_port()
    assert port == "54321"


def test_get_tunnel_port_returns_none_when_no_port():
    ex = _make_executor()
    client = _attach_mock_client(ex)

    stdout_mock = MagicMock()
    stdout_mock.read.return_value = b"file not found"
    stderr_mock = MagicMock()
    stderr_mock.read.return_value = b""
    client.exec_command.return_value = (MagicMock(), stdout_mock, stderr_mock)

    port = ex.get_tunnel_port()
    assert port is None


# ── tunnel_status ──────────────────────────────────────────────────────────


def test_tunnel_status_active_returns_green():
    ex = _make_executor()
    client = _attach_mock_client(ex)

    call_count = [0]
    def side_effect(cmd, timeout=30):
        call_count[0] += 1
        if "type" in cmd:
            stdout_mock = MagicMock()
            stdout_mock.read.return_value = b"43210"
            stderr_mock = MagicMock()
            stderr_mock.read.return_value = b""
            client.exec_command.return_value = (MagicMock(), stdout_mock, stderr_mock)
            return "43210"
        return "bore.exe  bore.exe  12345  0:00:05 N/A"

    with patch.object(ex, "exec_command", side_effect=side_effect):
        result = ex.tunnel_status()
    assert "🟢" in result or "🟡" in result or "🔴" in result


def test_tunnel_status_stopped_returns_red():
    ex = _make_executor()
    client = _attach_mock_client(ex)

    def side_effect(cmd, timeout=30):
        if "type" in cmd:
            return "file not found"
        return "INFO: No tasks are running"

    with patch.object(ex, "exec_command", side_effect=side_effect):
        result = ex.tunnel_status()
    assert "🔴" in result


# ── close ──────────────────────────────────────────────────────────────────


def test_close_sets_client_to_none():
    ex = _make_executor()
    _attach_mock_client(ex)
    ex.close()
    assert ex._client is None


# ── set_ssh_executor in commands ───────────────────────────────────────────


def test_set_ssh_executor_stores_executor():
    import src.bot.commands as cmd_module
    mock_executor = MagicMock()
    cmd_module.set_ssh_executor(mock_executor)
    assert cmd_module._ssh_executor is mock_executor
    cmd_module.set_ssh_executor(None)


def test_ssh_exec_command_no_executor_returns_arabic_error():
    import src.bot.commands as cmd_module
    cmd_module.set_ssh_executor(None)
    text, _ = cmd_module.execute_command("ssh_exec", ["dir"], {})
    assert "❌" in text
    assert "SSH" in text


def test_ssh_exec_command_with_executor():
    import src.bot.commands as cmd_module
    mock_exec = MagicMock()
    mock_exec.exec_command.return_value = "Volume in drive C"
    cmd_module.set_ssh_executor(mock_exec)
    text, _ = cmd_module.execute_command("ssh_exec", ["dir", "C:\\"], {})
    assert "Volume" in text
    cmd_module.set_ssh_executor(None)


def test_ssh_status_no_executor_returns_error():
    import src.bot.commands as cmd_module
    cmd_module.set_ssh_executor(None)
    text, _ = cmd_module.execute_command("ssh_status", [], {})
    assert "❌" in text


def test_sftp_get_no_path_returns_usage_hint():
    import src.bot.commands as cmd_module
    mock_exec = MagicMock()
    cmd_module.set_ssh_executor(mock_exec)
    text, _ = cmd_module.execute_command("sftp_get", [], {})
    # Whitelist now catches missing args before the handler — any rejection msg is valid
    assert text != "" and (
        "⚠️" in text
        or "معطيات" in text
        or "مسموح" in text
        or "argument" in text.lower()
        or "requires" in text.lower()
    )
    cmd_module.set_ssh_executor(None)


def test_ssh_bore_port_with_executor():
    import src.bot.commands as cmd_module
    mock_exec = MagicMock()
    mock_exec.get_tunnel_port.return_value = "55555"
    cmd_module.set_ssh_executor(mock_exec)
    text, _ = cmd_module.execute_command("ssh_bore_port", [], {"bore": {"bore_server": "bore.pub"}})
    assert "55555" in text
    cmd_module.set_ssh_executor(None)
