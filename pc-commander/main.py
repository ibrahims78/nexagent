import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import threading
from src.utils.config import load_config
from src.utils.logger import get_logger
from src.main_service import PCCommanderService

logger = get_logger()
service = PCCommanderService()


def on_start(config: dict):
    service.start(config)


def on_stop():
    service.stop()


def main():
    config = load_config()

    auto_start = "--silent" in sys.argv or "--startup" in sys.argv

    from src.gui.settings_window import SettingsWindow
    from src.gui.tray_icon import TrayIcon

    window = SettingsWindow(
        on_start_callback=on_start,
        on_stop_callback=on_stop
    )

    def show_window():
        window.deiconify()
        window.lift()
        window.focus_force()

    def quit_app():
        on_stop()
        tray.stop()
        window.destroy()
        sys.exit(0)

    tray = TrayIcon(show_callback=show_window, quit_callback=quit_app)
    tray.start()

    window.protocol("WM_DELETE_WINDOW", window._minimize_to_tray)

    if auto_start and config["telegram"].get("bot_token"):
        try:
            on_start(config)
            window.set_running_status(True)
            window.withdraw()
        except Exception as e:
            logger.error(f"Auto-start failed: {e}")

    window.mainloop()


if __name__ == "__main__":
    main()
