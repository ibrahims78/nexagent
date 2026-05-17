"""
PC Commander - Bot Watchdog
يراقب البوت ويعيد تشغيله تلقائياً عند الانهيار
ويرسل إشعارات عند انقطاع/عودة الإنترنت
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

CHECK_INTERVAL   = 30
RECONNECT_WAIT   = 15
OFFLINE_NOTIFY_AFTER = 60


def _is_internet_available() -> bool:
    try:
        socket.setdefaulttimeout(5)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except Exception:
        return False


def _send_telegram_notification(bot, config: dict, text: str):
    try:
        users = config.get("telegram", {}).get("allowed_users", [])
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def _send():
            for uid in users:
                try:
                    await bot.send_message(chat_id=int(uid), text=text, parse_mode="Markdown")
                except Exception as e:
                    logger.warning(f"Watchdog: فشل إرسال الإشعار لـ {uid}: {e}")
        loop.run_until_complete(_send())
        loop.close()
    except Exception as e:
        logger.error(f"Watchdog notification error: {e}")


def _watchdog_loop(get_bot_func, get_config_func, restart_func):
    global _last_known_online, _running
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
            logger.info("✅ Watchdog: الإنترنت عاد")

        elif not online and _last_known_online:
            offline_since = time.time()
            logger.warning("⚠️ Watchdog: انقطع الإنترنت")

        elif not online and offline_since:
            elapsed = time.time() - offline_since
            if elapsed >= OFFLINE_NOTIFY_AFTER and not offline_notified:
                logger.warning(f"📵 Watchdog: الإنترنت منقطع منذ {int(elapsed)} ثانية")
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
                logger.error(f"Watchdog: البوت لا يستجيب (محاولة {bot_failure_count}): {e}")
                if bot_failure_count >= 3:
                    logger.warning("🔄 Watchdog: إعادة تشغيل البوت...")
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
                        logger.error(f"Watchdog: فشل إعادة التشغيل: {re}")


def start_watchdog(get_bot_func, get_config_func, restart_func):
    global _watchdog_thread, _running
    if _running:
        return
    _running = True
    _watchdog_thread = threading.Thread(
        target=_watchdog_loop,
        args=(get_bot_func, get_config_func, restart_func),
        daemon=True,
        name="PCCommander-Watchdog"
    )
    _watchdog_thread.start()
    logger.info("🐕 Watchdog بدأ - يراقب البوت والاتصال")


def stop_watchdog():
    global _running
    _running = False
    logger.info("🐕 Watchdog توقف")


def is_running() -> bool:
    return _running
