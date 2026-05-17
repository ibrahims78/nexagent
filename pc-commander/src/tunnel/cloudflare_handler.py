import subprocess
import sys
import os
import time
import re
import threading

IS_WINDOWS = sys.platform == "win32"

CLOUDFLARED_PATHS = [
    "cloudflared",
    "C:\\Program Files\\cloudflared\\cloudflared.exe",
    os.path.expanduser("~\\cloudflared.exe"),
    os.path.join(os.path.dirname(sys.executable), "cloudflared.exe"),
]


class CloudflareHandler:
    def __init__(self, port: int = 5000):
        self.port = port
        self.public_url = None
        self.process = None
        self._url_event = threading.Event()

    def _find_cloudflared(self) -> str:
        for path in CLOUDFLARED_PATHS:
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0:
                    return path
            except Exception:
                continue
        return None

    def start(self) -> str:
        cloudflared = self._find_cloudflared()
        if not cloudflared:
            return None

        try:
            self.process = subprocess.Popen(
                [cloudflared, "tunnel", "--url", f"http://localhost:{self.port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            url = self._wait_for_url(timeout=30)
            self.public_url = url
            return url
        except Exception as e:
            return None

    def _wait_for_url(self, timeout: int = 30) -> str:
        if not self.process:
            return None
        start = time.time()
        while time.time() - start < timeout:
            line = self.process.stdout.readline()
            if not line:
                break
            match = re.search(r"https://[a-z0-9\-]+\.trycloudflare\.com", line)
            if match:
                return match.group(0)
        return None

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None
            self.public_url = None

    def get_url(self) -> str:
        return self.public_url

    def is_available(self) -> bool:
        return self._find_cloudflared() is not None

    def download_cloudflared(self) -> bool:
        try:
            import urllib.request
            if IS_WINDOWS:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
                dest = os.path.expanduser("~\\cloudflared.exe")
                urllib.request.urlretrieve(url, dest)
                return os.path.exists(dest)
        except Exception:
            return False
        return False
