#!/usr/bin/env python3
"""
PC Commander - WoL Agent للهاتف الاحتياطي في المنزل
يعمل على أندرويد عبر Termux
"""

import asyncio
import socket
import struct
import re
import json
import os
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

CONFIG_FILE = Path(__file__).parent / "wol_config.json"

DEFAULT_CONFIG = {
    "bot_token": "",
    "allowed_users": [],
    "pc_mac": "",
    "pc_broadcast": "255.255.255.255",
    "pc_ip": "",
    "agent_name": "Home Agent"
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cfg = DEFAULT_CONFIG.copy()
        cfg.update(data)
        return cfg
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def send_magic_packet(mac: str, broadcast: str = "255.255.255.255") -> bool:
    mac_clean = re.sub(r"[:\-\.]", "", mac).upper()
    if len(mac_clean) != 12:
        return False
    mac_bytes = bytes.fromhex(mac_clean)
    magic = b"\xFF" * 6 + mac_bytes * 16
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(magic, (broadcast, 9))
            s.sendto(magic, (broadcast, 7))
        return True
    except Exception as e:
        print(f"WoL error: {e}")
        return False


def is_pc_online(ip: str, timeout: int = 3) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((ip, 445))
        s.close()
        return result == 0
    except Exception:
        return False


config = load_config()


def is_allowed(user_id: int) -> bool:
    if not config["allowed_users"]:
        return True
    return user_id in [int(u) for u in config["allowed_users"]]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("⛔ غير مصرح")
        return

    keyboard = [
        [InlineKeyboardButton("🖥️ تشغيل الحاسب", callback_data="wol_start")],
        [InlineKeyboardButton("🔍 هل الحاسب يعمل؟", callback_data="wol_check")],
        [InlineKeyboardButton("ℹ️ معلومات", callback_data="wol_info")],
    ]
    await update.message.reply_text(
        f"🏠 **{config['agent_name']}**\n\nأنا هنا للتحكم بتشغيل الحاسب المنزلي.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_allowed(query.from_user.id):
        return

    data = query.data

    if data == "wol_start" or data.startswith("wol_manual_"):
        if data.startswith("wol_manual_"):
            parts = data.split("_", 3)
            mac = parts[2] if len(parts) > 2 else config["pc_mac"]
            broadcast = parts[3] if len(parts) > 3 else config["pc_broadcast"]
        else:
            mac = config["pc_mac"]
            broadcast = config["pc_broadcast"]

        if not mac:
            await query.message.reply_text("❌ لم يتم ضبط MAC Address. راجع الإعدادات.")
            return

        await query.message.reply_text("📡 جاري إرسال إشارة الإيقاظ...")
        success = send_magic_packet(mac, broadcast)

        if success:
            await query.message.reply_text(
                "✅ **تم إرسال إشارة الإيقاظ بنجاح!**\n\n"
                "⏳ الحاسب يحتاج 30-60 ثانية للإقلاع الكامل.\n"
                "اضغط 'هل الحاسب يعمل؟' بعد دقيقة للتحقق.",
                parse_mode="Markdown"
            )
        else:
            await query.message.reply_text("❌ فشل الإرسال. تأكد من اتصالك بالواي فاي المنزلي.")

    elif data == "wol_check":
        pc_ip = config.get("pc_ip", "")
        if not pc_ip:
            await query.message.reply_text("❌ لم يتم ضبط IP الحاسب في الإعدادات.")
            return
        await query.message.reply_text("🔍 جاري الفحص...")
        online = is_pc_online(pc_ip)
        if online:
            await query.message.reply_text("✅ **الحاسب يعمل الآن!**", parse_mode="Markdown")
        else:
            keyboard = [[InlineKeyboardButton("🖥️ شغّله الآن", callback_data="wol_start")]]
            await query.message.reply_text(
                "❌ **الحاسب غير متصل.**\n\nهل تريد تشغيله؟",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

    elif data == "wol_info":
        info = (
            f"ℹ️ **معلومات الإعداد:**\n\n"
            f"🖥️ MAC: `{config.get('pc_mac', 'غير مضبوط')}`\n"
            f"🌐 IP: `{config.get('pc_ip', 'غير مضبوط')}`\n"
            f"📡 Broadcast: `{config.get('pc_broadcast', '255.255.255.255')}`\n"
        )
        await query.message.reply_text(info, parse_mode="Markdown")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    text = update.message.text.lower()
    if any(word in text for word in ["شغل", "تشغيل", "wake", "start", "اقلع", "اوقظ"]):
        success = send_magic_packet(config["pc_mac"], config["pc_broadcast"])
        if success:
            await update.message.reply_text("✅ تم إرسال إشارة الإيقاظ!")
        else:
            await update.message.reply_text("❌ فشل الإرسال. تأكد من الواي فاي.")
    elif any(word in text for word in ["حالة", "status", "يعمل", "متصل"]):
        online = is_pc_online(config.get("pc_ip", ""))
        await update.message.reply_text("✅ الحاسب يعمل" if online else "❌ الحاسب مطفأ")
    else:
        await update.message.reply_text("💡 أرسل /start لفتح القائمة")


def main():
    if not config["bot_token"]:
        print("ERROR: Please set bot_token in wol_config.json first")
        print("See SETUP_ANDROID_AR.txt for setup instructions")
        return

    print(f"Agent '{config['agent_name']}' is running...")
    app = Application.builder().token(config["bot_token"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
