import secrets
from src.utils.logger import get_logger

logger = get_logger()


class PCCommanderService:
    def __init__(self):
        self.config = None
        self.bot = None
        self.tunnel = None
        self.scheduler = None
        self.network_monitor = None
        self.server_thread = None
        self.ai_handler = None
        self._ssh_executor = None
        self._running = False

    def start(self, config: dict):
        self.config = config
        logger.info("=" * 50)
        logger.info("NexAgent starting")
        logger.info("=" * 50)

        try:
            self._start_server()
            self._start_tunnel()
            self._start_ai()
            self._wire_vision_handler()
            self._wire_ssh_executor()
            self._ensure_stream_password()
            self._start_bot()
            self._start_scheduler()
            self._start_network_monitor()
            self._running = True
            logger.info("All services started successfully")
        except Exception as e:
            logger.error(f"Startup failed: {e}")
            raise

    def _start_server(self):
        from src.server.http_server import start_server, set_secret_token
        token = secrets.token_urlsafe(16)
        set_secret_token(token)
        self.server_thread = start_server(port=5000)
        logger.info("Local HTTP server listening on port 5000")

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
            logger.info(f"Tunnel active: {url}")
        else:
            logger.warning("Tunnel failed to start - bot will run without tunnel")

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
                model=self.config["ai"].get("model_gemini", "gemini-1.5-flash")
            )
        logger.info(f"AI provider: {provider}")

    def _wire_vision_handler(self):
        """Share a single VisionHandler instance with the commands module."""
        try:
            from src.bot.commands import set_vision_handler
            from src.ai.vision_handler import VisionHandler
            set_vision_handler(VisionHandler(self.ai_handler))
            logger.info("VisionHandler wired into commands")
        except Exception as e:
            logger.warning(f"VisionHandler not wired (non-fatal): {e}")

    def _wire_ssh_executor(self):
        """Instantiate SSHExecutor from config and share with commands module."""
        ssh_cfg = self.config.get("ssh", {})
        username = ssh_cfg.get("username", "")
        if not username:
            logger.warning("SSH layer disabled — ssh.username not set in config")
            return
        try:
            from src.pc_control.ssh_executor import SSHExecutor
            from src.bot.commands import set_ssh_executor
            executor = SSHExecutor(
                username=username,
                key_path=ssh_cfg.get("key_path") or None,
                password=ssh_cfg.get("password") or None,
                host=ssh_cfg.get("host", "127.0.0.1"),
                port=int(ssh_cfg.get("port", 22)),
            )
            set_ssh_executor(executor)
            self._ssh_executor = executor
            logger.info(f"SSHExecutor wired (user={username})")
        except Exception as e:
            logger.warning(f"SSHExecutor not wired (non-fatal): {e}")

    def _ensure_stream_password(self):
        """
        If stream is enabled and no password is set, generate a random one
        and schedule a one-time notification to the owner via Telegram.
        """
        stream_cfg = self.config.get("stream", {})
        if not stream_cfg.get("enabled", False):
            return

        password = stream_cfg.get("password", "")
        if not password:
            new_password = secrets.token_urlsafe(12)
            self.config["stream"]["password"] = new_password
            logger.info("Stream password was empty — generated a random password.")

            from src.utils.config import save_config
            try:
                save_config(self.config)
            except Exception as e:
                logger.warning(f"Could not persist generated stream password: {e}")

            self._pending_stream_password_notice = new_password
        else:
            self._pending_stream_password_notice = None

    def _notify_stream_password(self, password: str):
        """Send the auto-generated stream password to all allowed users once."""
        if not self.bot:
            return
        import asyncio
        message = (
            "🔐 **كلمة مرور البث العشوائية**\n\n"
            f"`{password}`\n\n"
            "⚠️ احفظها — لن تُرسل مرة أخرى.\n"
            "يمكنك تغييرها من الإعدادات."
        )
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.bot.send_notification(message))
            loop.close()
        except Exception as e:
            logger.error(f"Failed to notify stream password: {e}")

    def _start_bot(self):
        from src.bot.telegram_bot import PCCommanderBot
        self.bot = PCCommanderBot(
            token=self.config["telegram"]["bot_token"],
            allowed_users=self.config["telegram"].get("allowed_users", []),
            ai_handler=self.ai_handler,
            config=self.config
        )
        self.bot.start()
        logger.info("Telegram bot started")

        notice = getattr(self, "_pending_stream_password_notice", None)
        if notice:
            import threading
            import time

            def _delayed_notify():
                time.sleep(5)
                self._notify_stream_password(notice)

            threading.Thread(target=_delayed_notify, daemon=True).start()

    def _start_scheduler(self):
        from src.scheduler.task_scheduler import TaskScheduler
        self.scheduler = TaskScheduler(bot=self.bot, config=self.config)
        self.scheduler.start()
        logger.info("Scheduler started")

    def _start_network_monitor(self):
        from src.utils.network_monitor import NetworkMonitor
        self.network_monitor = NetworkMonitor(bot=self.bot, check_interval=30)
        self.network_monitor.start()
        logger.info("Network monitor started")

    def stop(self):
        logger.info("Stopping all services...")
        if self.network_monitor:
            self.network_monitor.stop()
        if self.scheduler:
            self.scheduler.stop()
        if self.bot:
            self.bot.stop()
        if self.tunnel:
            self.tunnel.stop()
        if self._ssh_executor:
            self._ssh_executor.close()
        self._running = False
        logger.info("All services stopped")

    def is_running(self) -> bool:
        return self._running
