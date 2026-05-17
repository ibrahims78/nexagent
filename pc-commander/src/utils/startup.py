import sys
import os

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import winreg

APP_NAME = "PCCommander"
STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def set_startup(enable: bool, exe_path: str = None):
    if not IS_WINDOWS:
        return False
    try:
        if exe_path is None:
            exe_path = sys.executable
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
        if enable:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        return False


def is_startup_enabled() -> bool:
    if not IS_WINDOWS:
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False
