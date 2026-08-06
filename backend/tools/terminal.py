import subprocess

ALLOWED_COMMANDS = {
    "dir",
    "git status",
    "python --version",
    "node --version",
    "npm --version",
    "ollama list"
}


def run_terminal(command):
    command = command.strip()

    if command not in ALLOWED_COMMANDS:
        return {
            "requires_confirmation": True,
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