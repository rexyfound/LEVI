import os
import sys

try:
    import winreg
except ImportError:
    winreg = None

REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "LEVI_AI_Assistant"

def get_executable_path() -> str:
    if getattr(sys, 'frozen', False):
        return sys.executable
    return f'"{sys.executable}" "{os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))}"'

def set_autostart(enable: bool = True) -> dict:
    """
    Enable or disable Windows startup auto-start.
    """
    if winreg is None:
        return {"success": False, "error": "Windows Registry autostart is available only on Windows."}
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE)
        if enable:
            exec_path = get_executable_path()
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exec_path)
            winreg.CloseKey(key)
            return {"success": True, "autostart": True, "message": "LEVI auto-start enabled in Windows Registry."}
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
            return {"success": True, "autostart": False, "message": "LEVI auto-start disabled."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_autostart_status() -> dict:
    """
    Check if auto-start is currently enabled in Windows Registry.
    """
    if winreg is None:
        return {"success": False, "error": "Windows Registry autostart is available only on Windows."}
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ)
        try:
            val, _ = winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return {"success": True, "autostart": True, "path": val}
        except FileNotFoundError:
            winreg.CloseKey(key)
            return {"success": True, "autostart": False}
    except Exception as e:
        return {"success": False, "error": str(e)}
