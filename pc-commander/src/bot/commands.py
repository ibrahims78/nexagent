import os
import sys
import json
from pathlib import Path


def execute_command(command: str, args: list, config: dict) -> tuple:
    from src.pc_control import screenshot, process_manager, file_manager, word_handler, system_monitor, anydesk

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
            user_cmd = " ".join(args) if args else ""
            result_text, result_file = _vision_execute(user_cmd, config)

        elif command == "vision_describe":
            result_text = _vision_describe(config)

        elif command == "vision_find_click":
            element = " ".join(args) if args else ""
            result_text = _vision_find_click(element, config)

        elif command == "vision_task":
            task = " ".join(args) if args else ""
            result_text, result_file = _vision_task(task, config)

        elif command == "autologon_enable":
            username = args[0] if len(args) > 0 else ""
            password = args[1] if len(args) > 1 else ""
            domain   = args[2] if len(args) > 2 else ""
            if not username or not password:
                result_text = "⚠️ الاستخدام: autologon_enable <username> <password> [domain]"
            else:
                from src.pc_control.autologon import setup_autologon
                result_text = setup_autologon(username, password, domain)

        elif command == "autologon_disable":
            from src.pc_control.autologon import disable_autologon
            result_text = disable_autologon()

        elif command == "autologon_status":
            from src.pc_control.autologon import is_autologon_enabled, get_current_username
            enabled = is_autologon_enabled()
            user    = get_current_username()
            status  = "✅ مفعّل" if enabled else "❌ غير مفعّل"
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
                result_text = "❌ **Pre-Login Agent غير مثبّت**\nافتح الإعدادات ← تسجيل الدخول لتثبيته."

        elif command == "chat":
            result_text = args[0] if args else ""

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
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        result = s.connect_ex((pc_ip, 445))
        s.close()
        if result == 0:
            return f"✅ **الحاسب يعمل الآن**\n🌐 IP: `{pc_ip}`"
        return f"❌ **الحاسب مطفأ أو غير متاح**\n🌐 IP: `{pc_ip}`"
    except Exception as e:
        return f"❌ فشل الفحص: {e}"


def _get_smart_executor(config: dict):
    provider = config.get("ai", {}).get("provider", "openai")
    if provider != "openai":
        raise RuntimeError("❌ التحكم البصري يتطلب OpenAI (GPT-4o)")
    key = config.get("ai", {}).get("openai_key", "")
    if not key:
        raise RuntimeError("❌ مفتاح OpenAI غير موجود")
    from src.ai.vision_handler import VisionHandler
    from src.pc_control.smart_executor import SmartExecutor
    return SmartExecutor(VisionHandler(api_key=key, model="gpt-4o"))


def _vision_execute(user_cmd: str, config: dict) -> tuple:
    import tempfile, os
    executor = _get_smart_executor(config)
    result = executor.execute_smart_command(user_cmd)

    actions_summary = "\n".join(result.get("actions_taken", []))
    text = (
        f"🧠 **التحكم البصري الذكي**\n\n"
        f"📺 الشاشة: {result.get('screen_description', '')[:200]}\n\n"
        f"⚡ الإجراءات المنفذة:\n{actions_summary}\n\n"
        f"💬 {result.get('response', '')}"
    )
    annotated = result.get("annotated_screenshot")
    filepath = None
    if annotated:
        from src.utils.config import get_config_dir
        screenshots_dir = get_config_dir() / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        from datetime import datetime
        filepath = str(screenshots_dir / f"vision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        with open(filepath, "wb") as f:
            f.write(annotated)
    return text, filepath


def _vision_describe(config: dict) -> str:
    executor = _get_smart_executor(config)
    description = executor.describe_current_screen()
    return f"👁️ **وصف الشاشة الحالية:**\n\n{description}"


def _vision_find_click(element: str, config: dict) -> str:
    executor = _get_smart_executor(config)
    return executor.find_and_click(element)


def _vision_task(task: str, config: dict) -> tuple:
    executor = _get_smart_executor(config)
    steps = executor.multi_step_task(task, max_steps=6)
    text = f"🔄 **مهمة ذكية متعددة الخطوات:**\n\n" + "\n".join(
        [f"{i+1}. {s}" for i, s in enumerate(steps)]
    )
    return text, None
