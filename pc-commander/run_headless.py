"""
Headless entry point for running NexAgent on Replit (Linux, no GUI).
Reads configuration from environment variables or falls back to config file.
"""
import sys
import os
import signal
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import get_logger
from src.utils.config import load_config, DEFAULT_CONFIG, deep_merge
from src.main_service import PCCommanderService

logger = get_logger()


def load_config_from_env() -> dict:
    """
    Build config dict by overlaying environment variables on top of the
    file-based config (or defaults).  Secrets are never stored in code.
    """
    try:
        config = load_config()
    except Exception:
        config = DEFAULT_CONFIG.copy()

    env_overrides = {}

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if bot_token:
        env_overrides.setdefault("telegram", {})["bot_token"] = bot_token

    allowed_users_raw = os.environ.get("TELEGRAM_ALLOWED_USERS", "")
    if allowed_users_raw:
        users = [u.strip() for u in allowed_users_raw.split(",") if u.strip()]
        env_overrides.setdefault("telegram", {})["allowed_users"] = users

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        env_overrides.setdefault("ai", {})["openai_key"] = openai_key

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        env_overrides.setdefault("ai", {})["gemini_key"] = gemini_key

    ai_provider = os.environ.get("AI_PROVIDER", "")
    if ai_provider:
        env_overrides.setdefault("ai", {})["provider"] = ai_provider

    if env_overrides:
        deep_merge(config, env_overrides)

    return config


def validate_config(config: dict) -> bool:
    """Check required fields are present before starting."""
    if not config.get("telegram", {}).get("bot_token"):
        logger.error(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Add it as a secret in the Replit Secrets panel."
        )
        return False

    if not config.get("telegram", {}).get("allowed_users"):
        logger.error(
            "TELEGRAM_ALLOWED_USERS is not set. "
            "Add your Telegram chat ID(s) as a secret."
        )
        return False

    provider = config.get("ai", {}).get("provider", "openai")
    if provider == "openai" and not config.get("ai", {}).get("openai_key"):
        logger.error(
            "OPENAI_API_KEY is not set. "
            "Add it as a secret in the Replit Secrets panel."
        )
        return False
    if provider == "gemini" and not config.get("ai", {}).get("gemini_key"):
        logger.error(
            "GEMINI_API_KEY is not set. "
            "Add it as a secret in the Replit Secrets panel."
        )
        return False

    return True


def main():
    logger.info("NexAgent starting in headless mode (Replit)")

    config = load_config_from_env()

    if not validate_config(config):
        logger.error(
            "\n\nRequired secrets are missing. Please set the following in the "
            "Replit Secrets panel (Tools → Secrets):\n"
            "  TELEGRAM_BOT_TOKEN    — from @BotFather on Telegram\n"
            "  TELEGRAM_ALLOWED_USERS — your Telegram chat ID (from @userinfobot)\n"
            "  OPENAI_API_KEY        — from platform.openai.com  (if using OpenAI)\n"
            "  GEMINI_API_KEY        — from aistudio.google.com  (if using Gemini)\n"
        )
        sys.exit(1)

    service = PCCommanderService()

    def handle_shutdown(signum, frame):
        logger.info("Received shutdown signal, stopping services...")
        service.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        service.start(config)
        logger.info("NexAgent is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        service.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        service.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
