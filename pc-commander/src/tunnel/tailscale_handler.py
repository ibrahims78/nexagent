"""
NexAgent - Tailscale VPN Handler
Detects if Tailscale is running and returns the device IP.
Tailscale gives a stable 100.x.x.x IP reachable from any device
on the same Tailscale network — no port forwarding, no dynamic DNS.
"""
import subprocess
import re
import sys
from src.utils.logger import get_logger

logger = get_logger()
IS_WINDOWS = sys.platform == "win32"


class TailscaleHandler:
    def __init__(self, port: int = 5000):
        self.port = port
        self._ip = None

    def get_tailscale_ip(self) -> str:
        """Return the Tailscale IP (100.x.x.x) if available."""
        try:
            cmd = ["tailscale", "ip", "-4"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            ip = result.stdout.strip()
            if re.match(r"^100\.\d+\.\d+\.\d+$", ip):
                return ip
        except Exception:
            pass
        try:
            result = subprocess.run(
                ["tailscale", "status"], capture_output=True, text=True, timeout=2
            )
            match = re.search(r"(100\.\d+\.\d+\.\d+)", result.stdout)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    def is_available(self) -> bool:
        return self.get_tailscale_ip() is not None

    def start(self) -> str:
        ip = self.get_tailscale_ip()
        if not ip:
            logger.debug("Tailscale not running or not installed — skipping")
            return None
        self._ip = ip
        url = f"http://{ip}:{self.port}"
        logger.info(f"Tailscale VPN active — NexAgent reachable at {url}")
        return url

    def stop(self):
        self._ip = None

    def get_url(self) -> str:
        return f"http://{self._ip}:{self.port}" if self._ip else None

    def get_install_instructions(self) -> str:
        return (
            "📦 **تثبيت Tailscale:**\n\n"
            "1. حمّل من https://tailscale.com/download/windows\n"
            "2. سجّل دخول بحساب Google أو GitHub\n"
            "3. ثبّت نفس التطبيق على هاتفك\n"
            "4. كلا الجهازين سيحصلان على IP ثابت 100.x.x.x\n\n"
            "🔒 الاتصال مشفر بـ WireGuard تلقائياً"
        )
