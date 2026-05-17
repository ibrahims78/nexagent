import threading
import time
import socket
from src.utils.logger import get_logger

logger = get_logger()


class NetworkMonitor:
    def __init__(self, bot=None, check_interval: int = 30):
        self.bot = bot
        self.check_interval = check_interval
        self._running = False
        self._was_connected = True
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("✅ مراقب الشبكة يعمل")

    def stop(self):
        self._running = False

    def _monitor_loop(self):
        while self._running:
            connected = self._check_connection()
            if not connected and self._was_connected:
                logger.warning("⚠️ انقطع الإنترنت")
                self._was_connected = False
            elif connected and not self._was_connected:
                logger.info("✅ عاد الإنترنت")
                self._was_connected = True
                if self.bot:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(
                        self.bot.send_notification("✅ **عاد الاتصال بالإنترنت**\nجميع الخدمات تعمل الآن.")
                    )
                    loop.close()
            time.sleep(self.check_interval)

    def _check_connection(self) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect(("8.8.8.8", 53))
            return True
        except Exception:
            return False

    @staticmethod
    def is_connected() -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect(("8.8.8.8", 53))
            return True
        except Exception:
            return False
