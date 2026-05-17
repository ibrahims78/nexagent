import sys
import threading
from PIL import Image, ImageDraw

IS_WINDOWS = sys.platform == "win32"


def create_icon_image(size=64, color="#4fc3f7"):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=color, outline="#ffffff", width=2)
    draw.rectangle([size // 4, size // 3, 3 * size // 4, 2 * size // 3], fill="#ffffff")
    return img


class TrayIcon:
    def __init__(self, show_callback=None, quit_callback=None):
        self.show_callback = show_callback
        self.quit_callback = quit_callback
        self.icon = None
        self._thread = None

    def start(self):
        if not IS_WINDOWS:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            import pystray
            image = create_icon_image()
            menu = pystray.Menu(
                pystray.MenuItem("🖥️ NexAgent", lambda: None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("فتح الإعدادات", self._on_show),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("إنهاء البرنامج", self._on_quit)
            )
            self.icon = pystray.Icon("NexAgent", image, "NexAgent", menu)
            self.icon.run()
        except Exception:
            pass

    def _on_show(self, icon=None, item=None):
        if self.show_callback:
            self.show_callback()

    def _on_quit(self, icon=None, item=None):
        if self.icon:
            self.icon.stop()
        if self.quit_callback:
            self.quit_callback()

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass

    def update_status(self, running: bool):
        if self.icon:
            color = "#66bb6a" if running else "#4fc3f7"
            try:
                self.icon.icon = create_icon_image(color=color)
            except Exception:
                pass
