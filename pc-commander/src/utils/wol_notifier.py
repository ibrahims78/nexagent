import asyncio
import threading
import time
from src.utils.logger import get_logger

logger = get_logger()


class WoLNotifier:
    """
    مسؤول عن إرسال إشعار للشخص الاحتياطي في المنزل
    عند فشل الإيقاظ التلقائي أو عند الطلب
    """

    def __init__(self, bot=None, config: dict = None):
        self.bot = bot
        self.config = config or {}

    def get_backup_users(self) -> list:
        return self.config.get("wol", {}).get("backup_users", [])

    async def notify_backup_person(self, requester_id: int = None):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        backup_users = self.get_backup_users()
        if not backup_users:
            return False

        mac = self.config.get("wol", {}).get("mac_address", "")
        broadcast = self.config.get("wol", {}).get("broadcast_ip", "255.255.255.255")

        keyboard = [[
            InlineKeyboardButton("✅ شغّل الحاسب الآن", callback_data=f"wol_manual_{mac}_{broadcast}"),
        ]]
        markup = InlineKeyboardMarkup(keyboard)

        message = (
            "🔔 **طلب تشغيل الحاسب**\n\n"
            "شخص يطلب تشغيل الحاسب المنزلي.\n"
            "اضغط الزر أدناه لتشغيله:"
        )

        sent = False
        for uid in backup_users:
            try:
                await self.bot.app.bot.send_message(
                    int(uid),
                    message,
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
                sent = True
                logger.info(f"✅ تم إرسال إشعار WoL للمستخدم {uid}")
            except Exception as e:
                logger.error(f"❌ فشل إرسال إشعار لـ {uid}: {e}")

        return sent

    def notify_async(self, requester_id: int = None):
        def run():
            try:
                asyncio.run(self.notify_backup_person(requester_id))
            except RuntimeError:
                pass

        t = threading.Thread(target=run, daemon=True)
        t.start()

    async def notify_wol_success(self, target_users: list):
        message = "✅ **الحاسب المنزلي جاهز الآن!**\nيمكنك البدء باستخدامه."
        for uid in target_users:
            try:
                await self.bot.app.bot.send_message(int(uid), message, parse_mode="Markdown")
            except Exception:
                pass

    def monitor_pc_startup(self, pc_ip: str, target_users: list, timeout: int = 120):
        def _check():
            import socket
            start = time.time()
            while time.time() - start < timeout:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(3)
                        result = sock.connect_ex((pc_ip, 445))
                    if result == 0:
                        try:
                            asyncio.run(self.notify_wol_success(target_users))
                        except RuntimeError:
                            pass
                        return
                except Exception:
                    pass
                time.sleep(5)

        t = threading.Thread(target=_check, daemon=True)
        t.start()
