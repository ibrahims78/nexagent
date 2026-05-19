import asyncio
import collections
import os
import threading
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from src.utils.logger import get_logger, log_command
from src.bot.commands import execute_command
from src.security.auth import (
    check_authorization, request_pin_auth, verify_pin,
    is_waiting_pin, refresh_session
)

logger = get_logger()

MAX_USERS_CONTEXT = 100

QUICK_COMMANDS_AR = [
    ["📸 لقطة شاشة", "screenshot"],
    ["📊 حالة الحاسب", "system_status"],
    ["📁 الملفات", "list_files"],
    ["🖥️ البرامج النشطة", "list_processes"],
    ["🔗 AnyDesk", "anydesk_start"],
    ["📝 تقرير يومي", "daily_report"],
]


class PCCommanderBot:
    def __init__(self, token: str, allowed_users: list, ai_handler, config: dict):
        self.token = token
        self.allowed_users = [int(u) for u in allowed_users if str(u).strip()]
        if not self.allowed_users:
            get_logger().warning(
                "CONFIGURATION WARNING: allowed_users is empty — "
                "the bot will reject ALL incoming messages. "
                "Set telegram.allowed_users in nexagent_config.ini."
            )
        self.ai_handler = ai_handler
        self.config = config
        self.app = None
        self.conversation_context: collections.OrderedDict[int, list] = collections.OrderedDict()
        self.last_activity: dict[int, float] = {}
        self._context_lock = threading.Lock()
        self._running = False
        self._thread = None

    def is_authorized(self, user_id: int) -> bool:
        if not self.allowed_users:
            return False
        return user_id in self.allowed_users

    def _trim_context_unsafe(self) -> None:
        """Evict stale entries — caller must hold self._context_lock."""
        now = time.time()
        stale = [
            uid for uid, ts in self.last_activity.items()
            if now - ts > 7200
        ]
        for uid in stale:
            self.conversation_context.pop(uid, None)
            self.last_activity.pop(uid, None)
        while len(self.conversation_context) > MAX_USERS_CONTEXT:
            self.conversation_context.popitem(last=False)

    def _trim_context_cache(self) -> None:
        """Thread-safe wrapper — acquires lock then trims."""
        with self._context_lock:
            self._trim_context_unsafe()

    async def _check_auth_and_session(self, update: Update) -> bool:
        user = update.effective_user
        uid = user.id
        allowed, reason = check_authorization(uid, self.config)

        if not allowed:
            msg = update.effective_message
            if reason == "NOT_ALLOWED":
                if msg:
                    await msg.reply_text("⛔ غير مصرح لك باستخدام هذا البوت.")
                if self.config.get("security", {}).get("notify_on_unauthorized", True):
                    for admin in self.allowed_users:
                        try:
                            await self.app.bot.send_message(
                                admin,
                                f"⚠️ **تنبيه أمني**\nمحاولة وصول غير مصرح:\n"
                                f"ID: `{uid}`\nاسم: {user.full_name}\n"
                                f"@{user.username or 'بدون username'}"
                            )
                        except Exception:
                            pass
            elif reason == "BLOCKED":
                if msg:
                    await msg.reply_text("🚫 تم حجبك. تواصل مع المسؤول.")
            elif reason == "RATE_LIMITED":
                if msg:
                    await msg.reply_text("⏳ أرسلت أوامر كثيرة. انتظر دقيقة.")
            elif reason == "NO_SESSION":
                status = request_pin_auth(uid, self.config)
                if status == "SESSION_CREATED":
                    return True
                if msg:
                    await msg.reply_text(
                        "🔐 **مطلوب رمز PIN للدخول**\n\n"
                        "أرسل الرمز السري للمتابعة.\n"
                        "⚠️ تنتهي المهلة خلال دقيقتين."
                    )
            return False
        return True

    async def _process_text(
        self,
        user_id: int,
        text: str,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        with self._context_lock:
            self.last_activity[user_id] = time.time()
        refresh_session(user_id)

        if self.config.get("general", {}).get("do_not_disturb", False):
            await update.message.reply_text(
                "🌙 وضع عدم الإزعاج مفعّل. سيتم تنفيذ الأمر لاحقاً."
            )
            return

        await context.bot.send_chat_action(update.effective_chat.id, action="typing")

        with self._context_lock:
            ctx = list(self.conversation_context.get(user_id, []))

        try:
            ai_result = self.ai_handler.process_command(text, ctx)
            command = ai_result.get("command", "chat")
            args = ai_result.get("args", [])
            ai_response = ai_result.get("response", "")

            ctx.append({"role": "user", "content": text})
            ctx.append({"role": "assistant", "content": ai_response})

            with self._context_lock:
                self.conversation_context[user_id] = ctx[-10:]
                self.conversation_context.move_to_end(user_id)
                if len(self.conversation_context) > MAX_USERS_CONTEXT:
                    self._trim_context_unsafe()

            if command != "chat":
                result_text, result_file = execute_command(command, args, self.config, user_id=user_id, bot=self)

                if self.config.get("security", {}).get("log_commands", True):
                    log_command(
                        user_id,
                        update.effective_user.username or "",
                        text,
                        result_text
                    )

                if result_file and os.path.exists(result_file):
                    with open(result_file, "rb") as f:
                        await update.message.reply_photo(f, caption=result_text or "")
                else:
                    if ai_response and ai_response != result_text:
                        await update.message.reply_text(ai_response, parse_mode="Markdown")
                    await update.message.reply_text(result_text, parse_mode="Markdown")
            else:
                reply_text = ai_response or "كيف يمكنني مساعدتك؟"
                await update.message.reply_text(reply_text, parse_mode="Markdown")

                if self.config.get("general", {}).get("voice_reply", False):
                    audio = self.ai_handler.text_to_speech(reply_text)
                    if audio:
                        await update.message.reply_voice(audio)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {e}")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_auth_and_session(update):
            return

        keyboard = []
        row = []
        for i, (label, _) in enumerate(QUICK_COMMANDS_AR):
            row.append(InlineKeyboardButton(label, callback_data=f"quick_{i}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🖥️ **NexAgent**\n\n"
            "مرحباً! أنا هنا للتحكم بحاسبك.\n"
            "يمكنك إرسال أمر نصي أو صوتي، أو استخدام الأزرار أدناه:\n\n"
            "💡 **أمثلة:**\n"
            "• افتح المتصفح\n"
            "• خذ لقطة شاشة\n"
            "• أرسلي حالة الحاسب\n"
            "• اغلق الحاسب بعد 30 دقيقة",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_auth_and_session(update):
            return

        help_text = (
            "📖 **قائمة الأوامر المتاحة:**\n\n"
            "🖼️ `لقطة شاشة` - أخذ صورة للشاشة\n"
            "📊 `حالة الحاسب` - عرض CPU/RAM/قرص\n"
            "📁 `الملفات` - تصفح الملفات\n"
            "🔄 `البرامج النشطة` - قائمة البرامج\n"
            "🔗 `anydesk` - تشغيل AnyDesk\n"
            "📝 `تقرير يومي` - تقرير شامل\n"
            "🔒 `اقفل الشاشة` - قفل الحاسب\n"
            "💤 `اغلق الحاسب` - إيقاف التشغيل\n"
            "🔁 `أعد التشغيل` - إعادة التشغيل\n\n"
            "يمكنك أيضاً إرسال أوامر بالعربي أو الإنجليزي بشكل طبيعي 🤖"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text

        if is_waiting_pin(user_id):
            result = verify_pin(user_id, text, self.config)
            try:
                await update.message.delete()
            except Exception:
                pass
            if result == "OK":
                await update.message.reply_text(
                    "✅ **تم التحقق بنجاح!**\nمرحباً، الجلسة نشطة الآن.",
                    parse_mode="Markdown"
                )
            elif result.startswith("WRONG:"):
                remaining = result.split(":")[1]
                await update.message.reply_text(
                    f"❌ رمز خاطئ. المحاولات المتبقية: {remaining}"
                )
            elif result == "BLOCKED":
                await update.message.reply_text("🚫 تم حجبك بسبب محاولات متكررة.")
            elif result == "EXPIRED":
                await update.message.reply_text(
                    "⏰ انتهت المهلة. أرسل أمراً جديداً لطلب PIN."
                )
            return

        if not await self._check_auth_and_session(update):
            return

        await self._process_text(user_id, text, update, context)

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_auth_and_session(update):
            return

        user_id = update.effective_user.id
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        await update.message.reply_text("🎤 جاري تحويل الصوت...")

        try:
            voice_file = await context.bot.get_file(update.message.voice.file_id)
            voice_data = await voice_file.download_as_bytearray()
            transcribed_text = self.ai_handler.transcribe_audio(bytes(voice_data))

            if transcribed_text.startswith("❌"):
                await update.message.reply_text(transcribed_text)
                return

            await update.message.reply_text(
                f"🎤 سمعتك: _{transcribed_text}_", parse_mode="Markdown"
            )

            await self._process_text(user_id, transcribed_text, update, context)

        except Exception as e:
            await update.message.reply_text(f"❌ فشل تحويل الصوت: {e}")

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_auth_and_session(update):
            return

        try:
            from src.utils.config import get_config_dir
            doc = update.message.document
            file = await context.bot.get_file(doc.file_id)
            downloads_dir = get_config_dir() / "downloads"
            downloads_dir.mkdir(exist_ok=True)
            dest = str(downloads_dir / doc.file_name)
            await file.download_to_drive(dest)
            await update.message.reply_text(
                f"✅ تم استلام الملف: `{doc.file_name}`\n📁 تم حفظه في: `{dest}`",
                parse_mode="Markdown"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ فشل استلام الملف: {e}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if not await self._check_auth_and_session(update):
            return

        data = query.data
        try:
            if data.startswith("quick_"):
                idx = int(data.split("_")[1])
                if idx < len(QUICK_COMMANDS_AR):
                    _, command = QUICK_COMMANDS_AR[idx]
                    result_text, result_file = execute_command(command, [], self.config, user_id=query.from_user.id, bot=self)
                    if result_file and os.path.exists(result_file):
                        with open(result_file, "rb") as f:
                            await query.message.reply_photo(f, caption=result_text or "")
                    else:
                        await query.message.reply_text(
                            result_text or "✅ تم", parse_mode="Markdown"
                        )

            elif data.startswith("wol_manual_"):
                parts = data.split("_", 3)
                mac = parts[2] if len(parts) > 2 else ""
                broadcast = parts[3] if len(parts) > 3 else "255.255.255.255"
                if mac:
                    from src.pc_control.wake_on_lan import send_magic_packet
                    success = send_magic_packet(mac, broadcast)
                    if success:
                        await query.message.reply_text(
                            "✅ **تم إرسال إشارة التشغيل!**\n"
                            "⏳ الحاسب يحتاج 30-60 ثانية للإقلاع.",
                            parse_mode="Markdown"
                        )
                        wol_cfg = self.config.get("wol", {})
                        pc_ip = wol_cfg.get("pc_ip", "")
                        if pc_ip and wol_cfg.get("monitor_startup", True):
                            from src.utils.wol_notifier import WoLNotifier
                            notifier = WoLNotifier(bot=self, config=self.config)
                            notifier.monitor_pc_startup(pc_ip, self.allowed_users)
                    else:
                        await query.message.reply_text("❌ فشل الإرسال. تأكد من الواي فاي.")

            elif data == "wol_start":
                result_text, _ = execute_command("wol_start", [], self.config, user_id=query.from_user.id, bot=self)
                await query.message.reply_text(result_text, parse_mode="Markdown")
                wol_cfg = self.config.get("wol", {})
                if wol_cfg.get("auto_notify_backup", True) and wol_cfg.get("backup_users"):
                    from src.utils.wol_notifier import WoLNotifier
                    notifier = WoLNotifier(bot=self, config=self.config)
                    notifier.notify_async(query.from_user.id)

        except Exception as e:
            logger.error(f"Callback handler error for data='{data}': {e}")
            try:
                await query.message.reply_text(f"❌ حدث خطأ: {e}")
            except Exception:
                pass

    async def send_notification(self, message: str):
        if not self.app or not self.allowed_users:
            return
        for uid in self.allowed_users:
            try:
                await self.app.bot.send_message(uid, message, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run_bot, daemon=True)
        self._thread.start()

    def _run_bot(self):
        asyncio.run(self._async_run())

    async def _async_run(self):
        self._loop = asyncio.get_running_loop()
        self.app = Application.builder().token(self.token).build()

        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)
        )
        self.app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        self.app.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

        await self.app.bot.set_my_commands([
            BotCommand("start", "القائمة الرئيسية"),
            BotCommand("help", "قائمة الأوامر"),
        ])

        if self.config.get("security", {}).get("watchdog_enabled", True):
            from src.utils.watchdog import start_watchdog

            def _get_bot():
                return self.app.bot if self.app else None

            def _get_config():
                return self.config

            def _restart():
                try:
                    self.stop()
                    time.sleep(2)
                    self.start()
                    logger.info("Watchdog restarted the bot successfully.")
                except Exception as e:
                    logger.error(f"Watchdog restart failed: {e}")

            start_watchdog(_get_bot, _get_config, _restart)

        self._start_context_cleanup()

        webhook_url = self.config.get("tunnel", {}).get("webhook_url", "")
        use_webhook = bool(webhook_url) and self.config.get("tunnel", {}).get("use_webhook", False)

        if use_webhook:
            logger.info(f"Starting in WEBHOOK mode: {webhook_url}/webhook")
            from telegram import Update
            from src.server.http_server import register_telegram_webhook

            await self.app.initialize()
            await self.app.bot.set_webhook(
                url=f"{webhook_url}/webhook",
                drop_pending_updates=True,
            )
            await self.app.start()

            def _on_webhook_update(data: dict):
                """Called by Flask on every POST /webhook — thread-safe."""
                update = Update.de_json(data, self.app.bot)
                if self._loop and not self._loop.is_closed():
                    import asyncio
                    asyncio.run_coroutine_threadsafe(
                        self.app.process_update(update), self._loop
                    )

            register_telegram_webhook(_on_webhook_update)
            logger.info("Webhook registered — waiting for updates via Flask /webhook")

            while self._running:
                await asyncio.sleep(1)

            await self.app.bot.delete_webhook()
            await self.app.stop()
            await self.app.shutdown()
        else:
            logger.info("Starting in POLLING mode")
            await self.app.run_polling(drop_pending_updates=True)

    def stop(self):
        self._running = False
        if self.app:
            try:
                loop = getattr(self, "_loop", None)
                if loop and loop.is_running():
                    loop.call_soon_threadsafe(
                        lambda: loop.create_task(self.app.stop())
                    )
                elif loop:
                    loop.run_until_complete(self.app.stop())
            except Exception as e:
                logger.warning(f"Bot stop warning: {e}")

    def _start_context_cleanup(self) -> None:
        """Background thread that evicts idle conversation contexts every hour."""
        def _cleanup_loop():
            while self._running:
                time.sleep(3600)
                self._trim_context_cache()
                logger.info("Hourly context cache cleanup complete.")

        t = threading.Thread(
            target=_cleanup_loop, daemon=True, name="ContextCleanup"
        )
        t.start()
