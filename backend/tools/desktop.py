import os
import subprocess
from pathlib import Path

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

if pyautogui is not None:
    pyautogui.FAILSAFE = True

# Absolute directory for screenshots — never depends on CWD
SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

from pending_actions import create_pending_action


def launch_app(path):
    try:
        action_id = create_pending_action(
            "launch_app",
            {"path": path}
        )
        return {
            "requires_confirmation": True,
            "action_id": action_id,
            "action": "launch_app",
            "path": path
        }
    except Exception as e:
        return {"error": str(e)}


def mouse_move(x, y):
    try:
        pyautogui.moveTo(
            x,
            y,
            duration=0.2
        )

        return {
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}


def mouse_click(button="left"):
    try:
        pyautogui.click(button=button)

        return {
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}


def keyboard_type(text):
    try:
        pyautogui.write(
            text,
            interval=0.01
        )

        return {
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}


def press_key(key):
    try:
        pyautogui.press(key)

        return {
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}


def hotkey(*keys):
    try:
        pyautogui.hotkey(*keys)

        return {
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}


def screenshot(path=None):
    try:
        if path is None:
            path = str(SCREENSHOT_DIR / "desktop.png")

        pyautogui.screenshot().save(path)

        return {
            "success": True,
            "path": path
        }
    except Exception as e:
        return {"error": str(e)}


def active_window():
    try:
        w = gw.getActiveWindow()

        if not w:
            return {
                "error": "No active window found"
            }

        return {
            "success": True,
            "title": w.title
        }
    except Exception as e:
        return {"error": str(e)}