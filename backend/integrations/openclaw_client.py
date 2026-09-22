"""Optional OpenClaw memory bridge with a local LEVI fallback."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time

from memory.memory_manager import add_session_summary, load_memory, save_memory, sanitize_memory_text


MEMORY_DIR = os.path.expanduser("~/.openclaw/workspace/memory")


def _openclaw_path():
    return shutil.which("openclaw")


def _local_search(query: str, max_results: int):
    needle = (query or "").lower().strip()
    data = load_memory()
    records = []

    for session in data.get("sessions", []):
        text = session.get("summary", "")
        if needle in text.lower():
            records.append({"type": "session", **session})

    for project in data.get("active_projects", []):
        if needle in project.lower():
            records.append({"type": "project", "name": project})

    user = data.get("user", {})
    for key, value in user.get("preferences", {}).items():
        item = f"{key}: {value}"
        if needle in item.lower():
            records.append({"type": "preference", "text": item})

    return records[-max_results:]


def search_memory(query: str, max_results: int = 5):
    """Search OpenClaw when installed, otherwise search LEVI's local memory."""
    if _openclaw_path():
        try:
            result = subprocess.run(
                [
                    _openclaw_path(),
                    "memory",
                    "search",
                    "--query",
                    query,
                    "--max-results",
                    str(max_results),
                    "--json",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout.strip())
                except json.JSONDecodeError:
                    data = result.stdout.strip()
                return {"success": True, "provider": "openclaw", "query": query, "results": data}
        except (subprocess.TimeoutExpired, OSError):
            pass

    return {"success": True, "provider": "local", "query": query, "results": _local_search(query, max_results)}


def write_memory(text: str):
    """Persist memory locally and optionally mirror it into OpenClaw."""
    if not text or not text.strip():
        return {"success": False, "error": "Memory text cannot be empty."}

    clean_text = sanitize_memory_text(text)
    if not clean_text:
        return {"success": False, "error": "Memory text cannot be empty after sanitization."}

    entry = add_session_summary(clean_text)
    openclaw_file = None

    if _openclaw_path():
        try:
            os.makedirs(MEMORY_DIR, exist_ok=True)
            openclaw_file = os.path.join(MEMORY_DIR, f"memory_{int(time.time())}.md")
            with open(openclaw_file, "w", encoding="utf-8") as file:
                file.write(clean_text)
            subprocess.run(
                [_openclaw_path(), "memory", "index"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            openclaw_file = None

    return {"success": True, "provider": "openclaw" if openclaw_file else "local", "memory": entry, "mirror": openclaw_file}


__all__ = ["search_memory", "write_memory"]

