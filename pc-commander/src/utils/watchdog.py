"""
NexAgent - Bot Watchdog
Monitors the bot and restarts it automatically on crash.
Sends Telegram notifications on internet disconnect/reconnect.
"""
import time
import threading
import socket
import asyncio
from src.utils.logger import get_logger

logger = get_logger()

_watchdog_thread = None
_running = False
_last_known_online = True
_bot_ref = None
_config_ref = None

CHECK_INTERVAL = 30
RECONNECT_WAIT = 15
OFFLINE_NOTIFY_AFTER = 60


def _is_internet_available() -> bool:
    """Check internet connectivity using a TCP connection to Google DNS."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect(("8.8.8.8", 53))
        return True
    except Exception:
        return False


def _send_telegram_notification(bot, config: dict, text: str):
    """Send a Telegram message to all allowed users."""
    async def _send():
        users = config.get("telegram", {}).get("allowed_users", [])
        for uid in users:
            try:
                await bot.send_message(chat_id=int(uid), text=text, parse_mode="Markdown")
            except Exception as e:
                logger.warning(f"Watchdog: failed to notify {uid}: {e}")

    try:
        asyncio.run(_send())
    except RuntimeError:
        pass
    except Exception as e:
        logger.error(f"Watchdog notification error: {e}")


def _watchdog_loop(get_bot_func, get_config_func, restart_func):
    """Main watchdog loop: monitors internet and bot health."""
    global _last_known_online
    offline_since = None
    offline_notified = False
    bot_failure_count = 0

    while _running:
        time.sleep(CHECK_INTERVAL)
        if not _running:
            break

        config = get_config_func()
        online = _is_internet_available()

        if online and not _last_known_online:
            downtime = int(time.time() - offline_since) if offline_since else 0
            msg = (
                f"✅ **عاد الإنترنت!**\n\n"
                f"⏱ مدة الانقطاع: {downtime // 60} دقيقة {downtime % 60} ثانية\n"
                f"🤖 البوت يعمل الآن بشكل طبيعي"
            )
            try:
                bot = get_bot_func()
                if bot:
                    _send_telegram_notification(bot, config, msg)
            except Exception:
                pass
            offline_since = None
            offline_notified = False
            bot_failure_count = 0
            logger.info("Watchdog: internet restored")

        elif not online and _last_known_online:
            offline_since = time.time()
            logger.warning("Watchdog: internet disconnected")

        elif not online and offline_since:
            elapsed = time.time() - offline_since
            if elapsed >= OFFLINE_NOTIFY_AFTER and not offline_notified:
                logger.warning(f"Watchdog: internet has been down for {int(elapsed)}s")
                offline_notified = True

        _last_known_online = online

        if online:
            try:
                bot = get_bot_func()
                if bot is None:
                    raise RuntimeError("Bot is None")
                bot_failure_count = 0
            except Exception as e:
                bot_failure_count += 1
                logger.error(f"Watchdog: bot unresponsive (attempt {bot_failure_count}): {e}")
                if bot_failure_count >= 3:
                    logger.warning("Watchdog: restarting bot...")
                    try:
                        restart_func()
                        bot_failure_count = 0
                        config = get_config_func()
                        bot = get_bot_func()
                        if bot:
                            _send_telegram_notification(
                                bot, config,
                                "🔄 **تم إعادة تشغيل البوت تلقائياً**\n"
                                "كان هناك عطل وتم الإصلاح التلقائي."
                            )
                    except Exception as re:
                        logger.error(f"Watchdog: restart failed: {re}")


def start_watchdog(get_bot_func, get_config_func, restart_func):
    """Start the watchdog thread if not already running."""
    global _watchdog_thread, _running
    if _running:
        return
    _running = True
    _watchdog_thread = threading.Thread(
        target=_watchdog_loop,
        args=(get_bot_func, get_config_func, restart_func),
        daemon=True,
        name="NexAgent-Watchdog"
    )
    _watchdog_thread.start()
    logger.info("Watchdog started - monitoring bot and connectivity")


def stop_watchdog():
    """Signal the watchdog thread to stop."""
    global _running
    _running = False
    logger.info("Watchdog stopped")


def is_running() -> bool:
    """Return True if the watchdog thread is active."""
    return _running
