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

        elif command == "chat":
            result_text = args[0] if args else ""

        else:
            result_text = f"⚠️ أمر غير معروف: {command}"

    except Exception as e:
        result_text = f"❌ خطأ في تنفيذ الأمر: {e}"

    return result_text, result_file
