import subprocess
from pending_actions import create_pending_action

SAFE_COMMAND_PREFIXES = (
    "dir", "ls", "type", "cat", "echo",
    "git status", "git log", "git diff", "git branch",
    "python --version", "python -V", "node --version", "npm --version", "pip list", "pip --version",
    "ollama list", "ollama ps",
    "wmic", "powershell", "cmd", "systeminfo", "hostname", "whoami", "tasklist", "ipconfig", "netstat",
    "get-process", "get-wmiobject", "get-counter"
)


def is_safe_command(command: str) -> bool:
    cmd_lower = command.strip().lower()
    return any(cmd_lower.startswith(prefix) for prefix in SAFE_COMMAND_PREFIXES)

def run_terminal(command):
    command = command.strip()

    if not is_safe_command(command):
        action_id = create_pending_action(
            "run_terminal",
            {"command": command}
        )
        return {
            "requires_confirmation": True,
            "action_id": action_id,
            "action": "run_terminal",
            "command": command
        }

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd="D:/Projects",
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except Exception as e:
        return {"error": str(e)}