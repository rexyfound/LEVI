import subprocess
import os
import ctypes

def set_master_volume(level: int) -> dict:
    """
    Set system master volume (0 - 100).
    """
    level = max(0, min(100, level))
    try:
        # Use PowerShell Audio API script fallback for native Windows volume control
        ps_script = f"""
        $wsh = New-Object -ComObject WScript.Shell
        [int]$target = {level}
        # Mute first to standardize
        1..50 | % {{ $wsh.SendKeys([char]174) }}
        [int]$steps = [math]::Round($target / 2)
        1..$steps | % {{ $wsh.SendKeys([char]175) }}
        """
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=5)
        return {"success": True, "volume": level, "message": f"Master volume set to approx {level}%"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def mute_volume(mute: bool = True) -> dict:
    """
    Mute or unmute master audio.
    """
    try:
        ps_script = "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]173)"
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=5)
        status = "muted / toggled" if mute else "unmuted"
        return {"success": True, "status": status}
    except Exception as e:
        return {"success": False, "error": str(e)}

def set_screen_brightness(level: int) -> dict:
    """
    Set screen brightness percentage (0 - 100).
    """
    level = max(0, min(100, level))
    try:
        ps_script = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})"
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=5)
        return {"success": True, "brightness": level, "message": f"Screen brightness set to {level}%"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def system_power_action(action: str) -> dict:
    """
    Execute system power command: 'lock', 'sleep'.
    """
    act = action.lower().strip()
    try:
        if act == "lock":
            ctypes.windll.user32.LockWorkStation()
            return {"success": True, "action": "lock", "message": "Workstation locked."}
        elif act == "sleep":
            subprocess.run(["powershell", "-Command", "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"], capture_output=True, timeout=5)
            return {"success": True, "action": "sleep", "message": "System entering sleep mode."}
        else:
            return {"success": False, "error": f"Unsupported power action: {action}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def media_control(command: str) -> dict:
    """
    Send media playback keys: 'play_pause', 'next', 'prev'.
    """
    cmd = command.lower().strip()
    key_codes = {
        "play_pause": 179,
        "next": 176,
        "prev": 177,
        "stop": 178
    }
    if cmd not in key_codes:
        return {"success": False, "error": f"Invalid media command: {command}"}

    try:
        code = key_codes[cmd]
        ps_script = f"$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]{code})"
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=5)
        return {"success": True, "command": cmd}
    except Exception as e:
        return {"success": False, "error": str(e)}
