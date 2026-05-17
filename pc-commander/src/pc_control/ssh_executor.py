"""
NexAgent - SSH Executor (Layer 2 integration)
Connects to the local OpenSSH server (127.0.0.1:22) that is exposed
via the SshRemote bore tunnel.  Provides exec, SFTP upload/download,
and directory listing through a persistent Paramiko client.
"""
import base64
import hashlib
import io
import threading
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger()

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 22
_DEFAULT_TIMEOUT = 15


def _get_known_hosts_file() -> Path:
    from src.utils.config import get_config_dir
    return get_config_dir() / "known_hosts.json"


def _load_known_hosts() -> dict:
    kh_file = _get_known_hosts_file()
    if kh_file.exists():
        import json
        try:
            with open(kh_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_known_hosts(known_hosts: dict):
    import json
    kh_file = _get_known_hosts_file()
    with open(kh_file, "w", encoding="utf-8") as f:
        json.dump(known_hosts, f, indent=2)


def _fingerprint(key) -> str:
    key_bytes = key.asbytes()
    digest = hashlib.sha256(key_bytes).digest()
    return "SHA256:" + base64.b64encode(digest).rstrip(b"=").decode()


class TOFUPolicy:
    """
    Trust On First Use host key policy.
    - First connection: stores the fingerprint and accepts it.
    - Subsequent connections: rejects if fingerprint changed (MITM protection).
    """

    def __init__(self, host: str, port: int):
        self._host_key = f"{host}:{port}"
        self._known_hosts = _load_known_hosts()

    def missing_host_key(self, client, hostname, key):
        import paramiko
        fp = _fingerprint(key)
        stored = self._known_hosts.get(self._host_key)

        if stored is None:
            logger.info(
                f"SSH TOFU: First connection to {self._host_key} — "
                f"storing fingerprint {fp}"
            )
            self._known_hosts[self._host_key] = fp
            _save_known_hosts(self._known_hosts)
            return

        if stored != fp:
            logger.error(
                f"SSH HOST KEY MISMATCH for {self._host_key}! "
                f"Expected {stored}, got {fp}. Possible MITM attack."
            )
            raise paramiko.SSHException(
                f"Host key verification failed for {self._host_key}. "
                "Fingerprint does not match stored value. "
                "If the server key changed legitimately, remove the entry from known_hosts.json."
            )

        logger.debug(f"SSH host key verified for {self._host_key}: {fp}")


class SSHExecutor:
    """
    Thin wrapper around Paramiko that manages a single SSH connection
    to the local OpenSSH server.

    Usage::
        executor = SSHExecutor(username="user", key_path=r"C:\\path\\to\\private_key")
        result   = executor.exec_command("dir C:\\Users")
        executor.close()
    """

    def __init__(
        self,
        username: str,
        key_path: str = None,
        password: str = None,
        host: str = _DEFAULT_HOST,
        port: int = _DEFAULT_PORT,
        timeout: int = _DEFAULT_TIMEOUT,
    ):
        self._host = host
        self._port = port
        self._username = username
        self._key_path = key_path
        self._password = password
        self._timeout = timeout
        self._client = None
        self._lock = threading.Lock()

    def connect(self) -> None:
        """Open an SSH connection to the local server using TOFU host key policy."""
        import paramiko

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(TOFUPolicy(self._host, self._port))

        kwargs = dict(
            hostname=self._host,
            port=self._port,
            username=self._username,
            timeout=self._timeout,
        )

        if self._key_path:
            kwargs["key_filename"] = self._key_path
        elif self._password:
            kwargs["password"] = self._password

        client.connect(**kwargs)
        self._client = client
        logger.info(f"SSH connected to {self._host}:{self._port} as {self._username}")

    def close(self) -> None:
        """Close the SSH connection gracefully."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
            logger.info("SSH connection closed")

    def _ensure_connected(self) -> None:
        """Re-connect if the connection has been dropped."""
        if self._client is None:
            self.connect()
        else:
            try:
                transport = self._client.get_transport()
                if transport is None or not transport.is_active():
                    logger.warning("SSH transport inactive — reconnecting...")
                    self.close()
                    self.connect()
            except Exception:
                self.close()
                self.connect()

    def exec_command(self, cmd: str, timeout: int = 30) -> str:
        """
        Execute a shell command on the local machine via SSH.
        Returns combined stdout + stderr as a single string.
        """
        with self._lock:
            self._ensure_connected()
            try:
                _, stdout, stderr = self._client.exec_command(cmd, timeout=timeout)
                out = stdout.read().decode("utf-8", errors="replace").strip()
                err = stderr.read().decode("utf-8", errors="replace").strip()
                result = out
                if err:
                    result = f"{out}\n⚠️ stderr:\n{err}" if out else f"⚠️ stderr:\n{err}"
                logger.info(f"SSH exec: {cmd!r} -> {len(result)} chars")
                return result or "✅ Command completed (no output)"
            except Exception as e:
                logger.error(f"SSH exec_command error: {e}")
                return f"❌ SSH error: {e}"

    def upload_file(self, local_path: str, remote_path: str) -> str:
        """Upload a local file to the remote path via SFTP."""
        with self._lock:
            self._ensure_connected()
            try:
                sftp = self._client.open_sftp()
                sftp.put(local_path, remote_path)
                sftp.close()
                size = Path(local_path).stat().st_size
                logger.info(f"SFTP upload: {local_path} -> {remote_path} ({size} bytes)")
                return f"✅ تم رفع الملف: `{remote_path}` ({size:,} bytes)"
            except Exception as e:
                logger.error(f"SFTP upload error: {e}")
                return f"❌ فشل رفع الملف: {e}"

    def download_file(self, remote_path: str) -> bytes:
        """Download a remote file and return its contents as bytes."""
        with self._lock:
            self._ensure_connected()
            try:
                sftp = self._client.open_sftp()
                buf = io.BytesIO()
                sftp.getfo(remote_path, buf)
                sftp.close()
                data = buf.getvalue()
                logger.info(f"SFTP download: {remote_path} ({len(data)} bytes)")
                return data
            except Exception as e:
                logger.error(f"SFTP download error: {e}")
                return None

    def list_files(self, remote_path: str = ".") -> str:
        """Return a formatted directory listing of the remote path."""
        with self._lock:
            self._ensure_connected()
            try:
                sftp = self._client.open_sftp()
                items = sftp.listdir_attr(remote_path)
                sftp.close()

                if not items:
                    return f"📁 `{remote_path}` — المجلد فارغ"

                lines = [f"📁 **محتويات `{remote_path}`:**\n"]
                for attr in sorted(items, key=lambda x: x.filename):
                    import stat as stat_mod
                    is_dir = stat_mod.S_ISDIR(attr.st_mode) if attr.st_mode else False
                    icon = "📂" if is_dir else "📄"
                    size = f"{attr.st_size:,} bytes" if not is_dir and attr.st_size else ""
                    lines.append(f"{icon} `{attr.filename}` {size}".strip())

                return "\n".join(lines)
            except Exception as e:
                logger.error(f"SFTP list_files error: {e}")
                return f"❌ فشل عرض الملفات: {e}"

    def get_tunnel_port(self, port_file: str = r"C:\SshRemote_V2\bore_port.txt") -> str:
        """Read the bore port from the port file."""
        result = self.exec_command(f'type "{port_file}"', timeout=5)
        port = result.strip()
        if port.isdigit():
            return port
        return None

    def tunnel_status(self, port_file: str = r"C:\SshRemote_V2\bore_port.txt") -> str:
        """Return a human-readable tunnel status string."""
        with self._lock:
            self._ensure_connected()

        port = self.get_tunnel_port(port_file)
        ps_check = self.exec_command(
            'tasklist /fi "IMAGENAME eq bore.exe" /fo csv /nh', timeout=5
        )
        bore_running = "bore.exe" in ps_check.lower()

        if bore_running and port:
            return (
                f"🟢 **النفق نشط**\n\n"
                f"🔗 للاتصال:\n"
                f"`ssh USER@bore.pub -p {port}`\n\n"
                f"🔑 المفتاح: sshremote_key"
            )
        elif bore_running:
            return "🟡 **bore.exe يعمل** لكن لم يُحدد منفذ بعد"
        else:
            return (
                "🔴 **النفق متوقف**\n\n"
                "شغّل `setup_v2.bat` أو `start_tunnel_v2.bat` لتفعيله."
            )

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()
