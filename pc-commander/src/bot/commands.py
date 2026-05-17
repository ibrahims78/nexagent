import os
from src.pc_control.command_whitelist import validate_command
from src.utils.logger import get_logger

logger = get_logger()

_vision_handler = None
_ssh_executor = None


def set_vision_handler(handler) -> None:
    global _vision_handler
    _vision_handler = handler


def set_ssh_executor(executor) -> None:
    global _ssh_executor
    _ssh_executor = executor


def execute_command(command: str, args: list, config: dict) -> tuple:
    """
    Dispatch a command string to the appropriate PC-control function.
    Returns (result_text, result_file_path_or_None).
    """
    from src.pc_control import (
        screenshot, process_manager, file_manager,
        word_handler, system_monitor, anydesk
    )

    valid, reason = validate_command(command, args)
    if not valid:
        logger.warning(f"Command rejected by whitelist: '{command}' args={args} reason={reason}")
        return reason, None

    result_text = ""
    result_file = None

    try:
        if command == "screenshot":
            result_file = screenshot.take_screenshot_file()
            result_text = "📸 لقطة الشاشة:"

        elif command == "open_app":
            app_name = " ".join(args) if args else ""
            result_text = process_manager.open_application(app_name)

        elif command == "close_app":
            app_name = " ".join(args) if args else ""
            result_text = process_manager.close_application(app_name)

        elif command == "list_processes":
            result_text = process_manager.list_running_processes()

        elif command == "run_cmd":
            cmd = " ".join(args) if args else ""
            result_text = process_manager.run_command(cmd)

        elif command == "shutdown":
            delay = int(args[0]) if args else 0
            result_text = process_manager.shutdown_pc(delay)

        elif command == "restart":
            delay = int(args[0]) if args else 0
            result_text = process_manager.restart_pc(delay)

        elif command == "cancel_shutdown":
            result_text = process_manager.cancel_shutdown()

        elif command == "lock":
            result_text = process_manager.lock_screen()

        elif command == "volume":
            level = int(args[0]) if args else 50
            result_text = process_manager.set_volume(level)

        elif command == "list_files":
            path = args[0] if args else None
            result_text = file_manager.list_directory(path)

        elif command == "delete_file":
            path = args[0] if args else ""
            result_text = file_manager.delete_file(path)

        elif command == "open_file":
            path = args[0] if args else ""
            result_text = file_manager.open_file(path)

        elif command == "search_files":
            folder = args[0] if args else os.path.expanduser("~")
            pattern = args[1] if len(args) > 1 else "*"
            result_text = file_manager.search_files(folder, pattern)

        elif command == "read_word":
            path = args[0] if args else ""
            result_text = word_handler.open_and_read_word(path)

        elif command == "edit_word":
            path = args[0] if args else ""
            text = " ".join(args[1:]) if len(args) > 1 else ""
            result_text = word_handler.append_to_word(path, text)

        elif command == "create_word":
            path = args[0] if args else ""
            title = args[1] if len(args) > 1 else ""
            content = " ".join(args[2:]) if len(args) > 2 else ""
            result_text = word_handler.create_word_document(path, title, content)

        elif command == "system_status":
            result_text = system_monitor.get_system_status()

        elif command == "daily_report":
            result_text = system_monitor.get_daily_report()

        elif command == "anydesk_start":
            anydesk_path = config.get("anydesk", {}).get("path", "")
            result_text = anydesk.start_anydesk(anydesk_path if anydesk_path else None)

        elif command == "anydesk_stop":
            result_text = anydesk.stop_anydesk()

        elif command == "anydesk_id":
            anydesk_path = config.get("anydesk", {}).get("path", "")
            anydesk_id = anydesk.get_anydesk_id(anydesk_path if anydesk_path else None)
            result_text = f"🔑 **رقم AnyDesk:** `{anydesk_id}`"

        elif command == "wol_start":
            from src.pc_control.wake_on_lan import wol_command
            result_text = wol_command(config)

        elif command == "wol_notify":
            result_text = "📲 سيتم إرسال إشعار للشخص الاحتياطي في المنزل..."

        elif command == "wol_status":
            result_text = _wol_check_status(config)

        elif command == "vision_do":
            if _vision_handler is None:
                result_text = "❌ التحكم البصري غير مهيأ. تحقق من مزود الذكاء الاصطناعي."
            else:
                from src.pc_control.smart_executor import SmartExecutor
                result = SmartExecutor(_vision_handler).execute_smart_command(
                    " ".join(args) if args else ""
                )
                actions_summary = "\n".join(result.get("actions_taken", []))
                result_text = (
                    f"🧠 **التحكم البصري الذكي**\n\n"
                    f"📺 الشاشة: {result.get('screen_description', '')[:200]}\n\n"
                    f"⚡ الإجراءات المنفذة:\n{actions_summary}\n\n"
                    f"💬 {result.get('response', '')}"
                )
                annotated = result.get("annotated_screenshot")
                if annotated:
                    from src.utils.config import get_config_dir
                    from datetime import datetime
                    screenshots_dir = get_config_dir() / "screenshots"
                    screenshots_dir.mkdir(exist_ok=True)
                    result_file = str(
                        screenshots_dir / f"vision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    )
                    with open(result_file, "wb") as fh:
                        fh.write(annotated)

        elif command == "vision_describe":
            if _vision_handler is None:
                result_text = "❌ التحكم البصري غير مهيأ. تحقق من مزود الذكاء الاصطناعي."
            else:
                from src.pc_control.smart_executor import SmartExecutor
                description = SmartExecutor(_vision_handler).describe_current_screen()
                result_text = f"👁️ **وصف الشاشة الحالية:**\n\n{description}"

        elif command == "vision_find_click":
            if _vision_handler is None:
                result_text = "❌ التحكم البصري غير مهيأ. تحقق من مزود الذكاء الاصطناعي."
            else:
                from src.pc_control.smart_executor import SmartExecutor
                result_text = SmartExecutor(_vision_handler).find_and_click(
                    args[0] if args else ""
                )

        elif command == "vision_task":
            if _vision_handler is None:
                result_text = "❌ التحكم البصري غير مهيأ. تحقق من مزود الذكاء الاصطناعي."
            else:
                from src.pc_control.smart_executor import SmartExecutor
                steps = SmartExecutor(_vision_handler).multi_step_task(
                    " ".join(args) if args else ""
                )
                result_text = (
                    "🔄 **مهمة ذكية متعددة الخطوات:**\n\n"
                    + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
                )

        elif command == "autologon_enable":
            username = args[0] if len(args) > 0 else ""
            domain = args[1] if len(args) > 1 else ""
            if not username:
                result_text = (
                    "⚠️ الاستخدام: autologon_enable <username> [domain]\n"
                    "⚠️ كلمة المرور لا تُرسَل عبر تيليغرام — ستُدخَل محلياً من نافذة الإعدادات فقط."
                )
            else:
                result_text = (
                    "🔐 **تفعيل Autologon**\n\n"
                    f"المستخدم: `{username}`\n\n"
                    "⚠️ لأسباب أمنية، كلمة المرور لا تُرسَل عبر تيليغرام.\n"
                    "افتح نافذة الإعدادات على الجهاز مباشرةً ← تبويب \"تسجيل الدخول\" لإتمام الإعداد."
                )

        elif command == "autologon_disable":
            from src.pc_control.autologon import disable_autologon
            result_text = disable_autologon()

        elif command == "autologon_status":
            from src.pc_control.autologon import is_autologon_enabled, get_current_username
            enabled = is_autologon_enabled()
            user = get_current_username()
            status = "✅ مفعّل" if enabled else "❌ غير مفعّل"
            result_text = (
                f"🔑 **حالة Autologon**\n\n"
                f"الحالة: {status}\n"
                f"المستخدم: `{user}`"
            )

        elif command == "pre_login_status":
            import subprocess
            r = subprocess.run(
                ["schtasks", "/query", "/tn", "PCCommander_PreLogin", "/fo", "LIST"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore"
            )
            if r.returncode == 0:
                result_text = "✅ **Pre-Login Agent مثبّت**\nيعمل تلقائياً عند كل إقلاع."
            else:
                result_text = (
                    "❌ **Pre-Login Agent غير مثبّت**\n"
                    "افتح الإعدادات ← تسجيل الدخول لتثبيته."
                )

        elif command == "stream_start":
            from src.streaming.screen_stream import start_stream, get_stream_status
            result_text = start_stream(config)
            status = get_stream_status(config)
            if status["running"]:
                port = status["port"]
                result_text += (
                    f"\n\n🌐 **الوصول للبث:**\n"
                    f"• شبكة منزلية: `http://localhost:{port}`\n"
                    f"• عبر الإنترنت: أرسل `/tunnel_start` أولاً للحصول على رابط عام"
                )

        elif command == "stream_stop":
            from src.streaming.screen_stream import stop_stream
            result_text = stop_stream()

        elif command == "stream_status":
            from src.streaming.screen_stream import get_stream_status
            status = get_stream_status(config)
            if status["running"]:
                port = status["port"]
                result_text = (
                    f"📡 **بث الشاشة يعمل**\n\n"
                    f"🟢 الحالة: نشط\n"
                    f"🔌 المنفذ: `{port}`\n"
                    f"🌐 شبكة منزلية: `http://localhost:{port}`"
                )
            else:
                result_text = "⏸️ **بث الشاشة متوقف**\nأرسل /stream_start لتشغيله"

        elif command == "security_report":
            from src.utils.security_auth import get_security_report
            result_text = get_security_report(config)

        elif command == "security_block":
            uid_str = args[0] if args else ""
            if uid_str.isdigit():
                from src.utils.security_auth import block_user
                block_user(int(uid_str))
                result_text = f"🚫 تم حجب المستخدم {uid_str}"
            else:
                result_text = "⚠️ أرسل User ID صحيح"

        elif command == "security_unblock":
            uid_str = args[0] if args else ""
            if uid_str.isdigit():
                from src.utils.security_auth import unblock_user
                unblock_user(int(uid_str))
                result_text = f"✅ تم رفع الحجب عن {uid_str}"
            else:
                result_text = "⚠️ أرسل User ID صحيح"

        elif command == "watchdog_status":
            from src.utils.watchdog import is_running as wd_running
            result_text = (
                "🐕 **Watchdog يعمل**\nيراقب البوت والإنترنت تلقائياً."
                if wd_running() else
                "❌ **Watchdog متوقف**"
            )

        elif command == "logout":
            from src.utils.security_auth import invalidate_session
            invalidate_session(args[0] if args else 0)
            result_text = "🔒 تم إنهاء الجلسة"

        elif command == "chat":
            result_text = args[0] if args else ""

        elif command == "ssh_exec":
            if _ssh_executor is None:
                result_text = "❌ SSH غير مهيأ. تحقق من إعدادات [ssh] في النظام."
            else:
                cmd = " ".join(args) if args else ""
                if not cmd:
                    result_text = "⚠️ الاستخدام: ssh_exec <command>"
                else:
                    result_text = _ssh_executor.exec_command(cmd)

        elif command == "ssh_status":
            if _ssh_executor is None:
                result_text = "❌ SSH غير مهيأ."
            else:
                bore_port_file = config.get("ssh", {}).get(
                    "bore_port_file", r"C:\SshRemote_V2\bore_port.txt"
                )
                result_text = _ssh_executor.tunnel_status(bore_port_file)

        elif command == "ssh_list":
            if _ssh_executor is None:
                result_text = "❌ SSH غير مهيأ."
            else:
                path = args[0] if args else "."
                result_text = _ssh_executor.list_files(path)

        elif command == "sftp_get":
            if _ssh_executor is None:
                result_text = "❌ SSH غير مهيأ."
            else:
                remote_path = args[0] if args else ""
                if not remote_path:
                    result_text = "⚠️ الاستخدام: sftp_get <remote_path>"
                else:
                    data = _ssh_executor.download_file(remote_path)
                    if data is None:
                        result_text = f"❌ فشل تنزيل الملف: `{remote_path}`"
                    else:
                        from src.utils.config import get_config_dir
                        filename = remote_path.replace("\\", "/").split("/")[-1]
                        out = get_config_dir() / "downloads" / filename
                        out.parent.mkdir(parents=True, exist_ok=True)
                        out.write_bytes(data)
                        result_file = str(out)
                        result_text = f"✅ تم تنزيل الملف: `{filename}` ({len(data):,} bytes)"

        elif command == "sftp_put":
            if _ssh_executor is None:
                result_text = "❌ SSH غير مهيأ."
            else:
                local_path = args[0] if args else ""
                remote_path = args[1] if len(args) > 1 else ""
                if not local_path or not remote_path:
                    result_text = "⚠️ الاستخدام: sftp_put <local_path> <remote_path>"
                else:
                    result_text = _ssh_executor.upload_file(local_path, remote_path)

        elif command == "ssh_bore_port":
            if _ssh_executor is None:
                result_text = "❌ SSH غير مهيأ."
            else:
                bore_port_file = config.get("ssh", {}).get(
                    "bore_port_file", r"C:\SshRemote_V2\bore_port.txt"
                )
                port = _ssh_executor.get_tunnel_port(bore_port_file)
                if port:
                    bore_server = config.get("bore", {}).get("bore_server", "bore.pub")
                    result_text = (
                        f"🔗 **منفذ النفق الحالي:**\n\n"
                        f"`{port}`\n\n"
                        f"للاتصال:\n`ssh USER@{bore_server} -p {port}`"
                    )
                else:
                    result_text = "❌ لا يوجد منفذ نشط. تأكد من تشغيل النفق على الجهاز."

        else:
            result_text = f"⚠️ أمر غير معروف: {command}"

    except Exception as e:
        result_text = f"❌ خطأ في تنفيذ الأمر: {e}"

    return result_text, result_file


def _wol_check_status(config: dict) -> str:
    import socket
    pc_ip = config.get("wol", {}).get("pc_ip", "")
    if not pc_ip:
        return "❌ لم يتم ضبط IP الحاسب في إعدادات WoL"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            result = s.connect_ex((pc_ip, 445))
        if result == 0:
            return f"✅ **الحاسب يعمل الآن**\n🌐 IP: `{pc_ip}`"
        return f"❌ **الحاسب مطفأ أو غير متاح**\n🌐 IP: `{pc_ip}`"
    except Exception as e:
        return f"❌ فشل الفحص: {e}"
