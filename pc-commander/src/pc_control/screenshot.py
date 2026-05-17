import io
import sys
from datetime import datetime

IS_WINDOWS = sys.platform == "win32"


def take_screenshot() -> bytes:
    try:
        if IS_WINDOWS:
            import pyautogui
            screenshot = pyautogui.screenshot()
        else:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
        buf = io.BytesIO()
        screenshot.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()
    except Exception as e:
        raise RuntimeError(f"فشل أخذ لقطة الشاشة: {e}")


def take_screenshot_file() -> str:
    from src.utils.config import get_config_dir
    screenshots_dir = get_config_dir() / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = str(screenshots_dir / filename)
    data = take_screenshot()
    with open(filepath, "wb") as f:
        f.write(data)
    return filepath
