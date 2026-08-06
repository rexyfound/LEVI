import subprocess
import pyautogui
import pyperclip
import pygetwindow as gw
import traceback

try:
    import tools.desktop
except Exception:
    traceback.print_exc()

pyautogui.FAILSAFE = True


def launch_app(path):
    subprocess.Popen(path)

    return {
        "success": True,
        "app": path
    }


def mouse_move(x, y):

    pyautogui.moveTo(
        x,
        y,
        duration=0.2
    )

    return {
        "success": True
    }


def mouse_click(button="left"):

    pyautogui.click(button=button)

    return {
        "success": True
    }


def keyboard_type(text):

    pyautogui.write(
        text,
        interval=0.01
    )

    return {
        "success": True
    }


def press_key(key):

    pyautogui.press(key)

    return {
        "success": True
    }


def hotkey(*keys):

    pyautogui.hotkey(*keys)

    return {
        "success": True
    }


def screenshot(path="desktop.png"):

    pyautogui.screenshot().save(path)

    return {
        "success": True,
        "path": path
    }


def active_window():

    w = gw.getActiveWindow()

    if not w:
        return {
            "success": False
        }

    return {
        "success": True,
        "title": w.title
    }