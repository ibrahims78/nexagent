import sys
import threading
from src.utils.config import load_config
from src.utils.logger import get_logger
from src.server.http_server import start_server

logger = get_logger()


class PCCommanderService:
    def __init__(self):
        self.config = None
        self.bot = None
        self.tunnel = None
        self.scheduler = None
        self.network_monitor = None
        self.server_thread = None
        self._running = False

    def start(self, config: dict):
        self.config = config
        logger.info("=" * 50)
        logger.info("🚀 بدء تشغيل PC Commander")
        logger.info("=" * 50)

        try:
            self._start_server()
            self._start_tunnel()
            self._start_ai()
            self._start_bot()
            self._start_scheduler()
            self._start_network_monitor()
            self._running = True
            logger.info("✅ جميع الخدمات تعمل بنجاح")
        except Exception as e:
            logger.error(f"❌ فشل التشغيل: {e}")
            raise

    def _start_server(self):
        from src.server.http_server import start_server, set_secret_token
        import secrets
        token = secrets.token_urlsafe(16)
        set_secret_token(token)
        self.server_thread = start_server(port=5000)
        logger.info("✅ السيرفر المحلي يعمل على المنفذ 5000")

    def _start_tunnel(self):
        provider = self.config["tunnel"].get("provider", "cloudflare")
        if provider == "cloudflare":
            from src.tunnel.cloudflare_handler import CloudflareHandler
            self.tunnel = CloudflareHandler(port=5000)
        else:
            from src.tunnel.ngrok_handler import NgrokHandler
            self.tunnel = NgrokHandler(
                auth_token=self.config["tunnel"].get("ngrok_token", ""),
                port=5000
            )

        url = self.tunnel.start()
        if url:
            logger.info(f"✅ النفق يعمل: {url}")
        else:
            logger.warning("⚠️ فشل تشغيل النفق - سيعمل البوت بدون نفق")

    def _start_ai(self):
        provider = self.config["ai"].get("provider", "openai")
        if provider == "openai":
            from src.ai.openai_handler import OpenAIHandler
            self.ai_handler = OpenAIHandler(
                api_key=self.config["ai"]["openai_key"],
                model=self.config["ai"].get("model_openai", "gpt-4o")
            )
        else:
            from src.ai.gemini_handler import GeminiHandler
            self.ai_handler = GeminiHandler(
                api_key=self.config["ai"]["gemini_key"],
                model=self.config["ai"].get("model_gemini", "gemini-pro")
            )
        logger.info(f"✅ الذكاء الاصطناعي: {provider}")

    def _start_bot(self):
        from src.bot.telegram_bot import PCCommanderBot
        self.bot = PCCommanderBot(
            token=self.config["telegram"]["bot_token"],
            allowed_users=self.config["telegram"].get("allowed_users", []),
            ai_handler=self.ai_handler,
            config=self.config
        )
        self.bot.start()
        logger.info("✅ بوت تيليغرام يعمل")

    def _start_scheduler(self):
        from src.scheduler.task_scheduler import TaskScheduler
        self.scheduler = TaskScheduler(bot=self.bot, config=self.config)
        self.scheduler.start()
        logger.info("✅ المجدول يعمل")

    def _start_network_monitor(self):
        from src.utils.network_monitor import NetworkMonitor
        self.network_monitor = NetworkMonitor(bot=self.bot, check_interval=30)
        self.network_monitor.start()
        logger.info("✅ مراقب الشبكة يعمل")

    def stop(self):
        logger.info("⏹️ إيقاف الخدمات...")
        if self.network_monitor:
            self.network_monitor.stop()
        if self.scheduler:
            self.scheduler.stop()
        if self.bot:
            self.bot.stop()
        if self.tunnel:
            self.tunnel.stop()
        self._running = False
        logger.info("✅ تم إيقاف جميع الخدمات")

    def is_running(self) -> bool:
        return self._running
