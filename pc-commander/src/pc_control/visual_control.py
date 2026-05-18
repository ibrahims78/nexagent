import sys
import time
from src.utils.logger import get_logger

logger = get_logger()
IS_WINDOWS = sys.platform == "win32"


def execute_visual_actions(actions: list) -> list:
    results = []
    for action in actions:
        result = _execute_single_action(action)
        results.append(result)
        time.sleep(0.3)
    return results


def _execute_single_action(action: dict) -> str:
    action_type = action.get("type", "")
    desc = action.get("description", action_type)

    try:
        if action_type == "click":
            _click(action["x"], action["y"])
            return f"✅ ضغط على: {desc}"

        elif action_type == "double_click":
            _double_click(action["x"], action["y"])
            return f"✅ نقر مزدوج على: {desc}"

        elif action_type == "right_click":
            _right_click(action["x"], action["y"])
            return f"✅ نقر أيمن على: {desc}"

        elif action_type == "type":
            _type_text(action.get("text", ""))
            return f"✅ كتابة: {action.get('text', '')[:50]}"

        elif action_type == "key":
            _press_key(action.get("key", ""))
            return f"✅ مفتاح: {action.get('key', '')}"

        elif action_type == "hotkey":
            _hotkey(action.get("keys", []))
            return f"✅ اختصار: {'+'.join(action.get('keys', []))}"

        elif action_type == "scroll":
            _scroll(action.get("x", 0), action.get("y", 0),
                    action.get("direction", "down"),
                    action.get("amount", 3))
            return f"✅ تمرير: {action.get('direction', 'down')}"

        elif action_type == "describe":
            return f"ℹ️ {desc}"

        else:
            return f"⚠️ نوع إجراء غير معروف: {action_type}"

    except Exception as e:
        logger.error(f"Action error [{action_type}]: {e}")
        return f"❌ فشل {desc}: {e}"


def _click(x: int, y: int):
    import pyautogui
    pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.click(x, y)


def _double_click(x: int, y: int):
    import pyautogui
    pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.doubleClick(x, y)


def _right_click(x: int, y: int):
    import pyautogui
    pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.rightClick(x, y)


def _type_text(text: str):
    """Type text. Uses clipboard paste to support Unicode/Arabic characters."""
    try:
        import pyperclip
        import pyautogui
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
    except Exception:
        import pyautogui
        pyautogui.typewrite(text, interval=0.05)


def _press_key(key: str):
    import pyautogui
    key_map = {
        "enter": "enter", "tab": "tab", "escape": "esc", "esc": "esc",
        "delete": "delete", "backspace": "backspace", "space": "space",
        "up": "up", "down": "down", "left": "left", "right": "right",
        "home": "home", "end": "end", "pageup": "pageup", "pagedown": "pagedown",
        "f1": "f1", "f2": "f2", "f3": "f3", "f4": "f4", "f5": "f5",
    }
    mapped = key_map.get(key.lower(), key.lower())
    pyautogui.press(mapped)


def _hotkey(keys: list):
    import pyautogui
    pyautogui.hotkey(*keys)


def _scroll(x: int, y: int, direction: str, amount: int):
    import pyautogui
    pyautogui.moveTo(x, y, duration=0.2)
    clicks = amount if direction == "up" else -amount
    pyautogui.scroll(clicks)


def move_mouse_to(x: int, y: int):
    import pyautogui
    pyautogui.moveTo(x, y, duration=0.5)
    return f"✅ تم تحريك المؤشر إلى ({x}, {y})"


def get_screen_size() -> tuple:
    import pyautogui
    return pyautogui.size()


def take_annotated_screenshot(actions: list) -> bytes:
    from src.pc_control.screenshot import take_screenshot
    from PIL import Image, ImageDraw
    import io

    screenshot_data = take_screenshot()
    img = Image.open(io.BytesIO(screenshot_data))
    draw = ImageDraw.Draw(img)

    colors = ["#FF0000", "#00FF00", "#0000FF", "#FF8800", "#FF00FF"]
    for i, action in enumerate(actions):
        if "x" in action and "y" in action:
            x, y = action["x"], action["y"]
            color = colors[i % len(colors)]
            r = 15
            draw.ellipse([x - r, y - r, x + r, y + r], outline=color, width=3)
            draw.text((x + r + 5, y - 10), f"{i+1}", fill=color)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()
