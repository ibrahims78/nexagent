#!/usr/bin/env python3
"""
PC Commander - Pre-Login Agent
سكريبت يعمل عند إقلاع ويندوز قبل/عند شاشة تسجيل الدخول
يُرسل إشعاراً على تيليغرام ويستقبل أمر تسجيل الدخول

⚠️ تحذير أمني: يتطلب هذا العميل إرسال كلمة مرور عبر تيليغرام.
استخدمه فقط إذا كنت تثق تماماً بقناة تيليغرام وبالأجهزة التي تستخدمها.
هذه الميزة مخصصة للاستخدام المتقدم فقط.
"""

import asyncio
import json
import os
import sys
import time
import socket
import subprocess
import ctypes
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "pre_login_config.json"
LOG_FILE = Path(__file__).parent / "pre_login.log"

DEFAULT_CONFIG = {
    "bot_token": "",
    "allowed_users": [],
    "notify_on_boot": True,
    "auto_login_enabled": False,
    "wait_for_command": True,
    "command_timeout": 300
}


def log(msg: str):
    entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass
    print(entry.strip())


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(data)
            return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def _build_security_config(config: dict) -> dict:
    """Wrap pre_login config into the shape expected by is_allowed_user."""
    return {
        "telegram": {
            "allowed_users": config.get("allowed_users", [])
        }
    }


def is_internet_available(timeout: int = 5) -> bool:
    for _ in range(10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect(("8.8.8.8", 53))
            return True
        except Exception:
            time.sleep(3)
    return False


def attempt_auto_login(*args, **kwargs):
    raise NotImplementedError(
        "Auto-login via Telegram is disabled for security reasons. "
        "Enable only after reviewing security implications."
    )


def simulate_login_keystrokes(password: str):
    try:
        import win32api
        import win32con
        time.sleep(1)
        for char in password:
            win32api.keybd_event(ord(char.upper()), 0, 0, 0)
            win32api.keybd_event(ord(char.upper()), 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        return True
    except Exception:
        try:
            import win32api
            import win32con
            for char in password:
                vk = win32api.VkKeyScan(char)
                if vk != -1:
                    win32api.keybd_event(vk & 0xFF, 0, 0, 0)
                    win32api.keybd_event(vk & 0xFF, 0, win32con.KEYEVENTF_KEYUP, 0)
                    time.sleep(0.05)
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
            win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
            return True
        except Exception as e:
            log(f"فشل محاكاة ضغط المفاتيح: {e}")
            return False


async def run_pre_login_bot(config: dict):
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        CallbackQueryHandler, filters, ContextTypes
    )

    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    try:
        from utils.security_auth import is_allowed_user
        security_config = _build_security_config(config)

        def is_allowed(uid: int) -> bool:
            return is_allowed_user(uid, security_config)
    except ImportError:
        allowed_users_list = [int(u) for u in config.get("allowed_users", []) if str(u).strip()]

        def is_allowed(uid: int) -> bool:
            return not allowed_users_list or uid in allowed_users_list

    login_event = asyncio.Event()
    login_password = [None]

    allowed_users = [int(u) for u in config.get("allowed_users", []) if str(u).strip()]

    async def send_boot_notification(app):
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        keyboard = [
            [InlineKeyboardButton("🔓 سجّل الدخول الآن", callback_data="login_now")],
            [InlineKeyboardButton("⏳ انتظر", callback_data="login_wait")],
        ]
        msg = (
            "🖥️ **الحاسب أُقلع بنجاح!**\n\n"
            f"💻 الجهاز: `{hostname}`\n"
            f"🌐 IP: `{ip}`\n"
            f"🕐 الوقت: {time.strftime('%H:%M:%S')}\n\n"
            "⏸️ الحاسب في شاشة تسجيل الدخول\n"
            "اضغط **سجّل الدخول** للمتابعة:"
        )
        for uid in allowed_users:
            try:
                await app.bot.send_message(
                    uid, msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            except Exception as e:
                log(f"فشل إرسال الإشعار: {e}")

    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if not is_allowed(query.from_user.id):
            return

        if query.data == "login_now":
            if config.get("auto_login_enabled"):
                await query.message.reply_text("🔓 جاري تسجيل الدخول تلقائياً...")
                login_event.set()
            else:
                await query.message.reply_text(
                    "🔐 أرسل كلمة المرور لتسجيل الدخول:\n\n"
                    "⚠️ ستُحذف الرسالة فوراً بعد الاستخدام"
                )
        elif query.data == "login_wait":
            await query.message.reply_text("⏳ تم. أرسل /login عندما تكون جاهزاً.")

    async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_allowed(update.effective_user.id):
            return
        password = update.message.text
        try:
            await update.message.delete()
        except Exception:
            pass
        await update.message.reply_text("🔓 جاري تسجيل الدخول...")
        login_password[0] = password
        login_event.set()

    async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_allowed(update.effective_user.id):
            return
        await update.message.reply_text(
            "🔐 أرسل كلمة المرور لتسجيل الدخول:"
        )

    app = Application.builder().token(config["bot_token"]).build()
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password))

    async def post_init(application):
        await send_boot_notification(application)

    app.post_init = post_init

    async def run():
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await send_boot_notification(app)

        timeout = config.get("command_timeout", 300)
        try:
            await asyncio.wait_for(login_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            log("⏰ انتهت المهلة - تشغيل Autologon إن وجد")

        await app.updater.stop()
        await app.stop()
        await app.shutdown()

        if login_event.is_set() and login_password[0]:
            log("🔓 محاولة تسجيل الدخول...")
            try:
                attempt_auto_login(login_password[0])
                success = False
            except NotImplementedError as e:
                log(f"⛔ {e}")
                success = False
            if success:
                for uid in allowed_users:
                    try:
                        await app.bot.send_message(
                            uid,
                            "✅ **تم تسجيل الدخول بنجاح!**\nالبوت الرئيسي يعمل الآن.",
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
            else:
                for uid in allowed_users:
                    try:
                        await app.bot.send_message(uid, "❌ فشل تسجيل الدخول. حاول يدوياً.")
                    except Exception:
                        pass

    asyncio.run(run())


def main():
    log("=" * 50)
    log("🚀 Pre-Login Agent بدأ التشغيل")

    config = load_config()

    if not config.get("bot_token"):
        log("❌ Bot Token غير موجود في pre_login_config.json")
        sys.exit(1)

    log("⏳ انتظار الاتصال بالإنترنت...")
    if not is_internet_available():
        log("❌ لا يوجد إنترنت - إنهاء")
        sys.exit(1)

    log("✅ الإنترنت متاح - تشغيل البوت")

    if config.get("notify_on_boot"):
        asyncio.run(run_pre_login_bot(config))


if __name__ == "__main__":
    main()
