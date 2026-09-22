"""Local repository watcher for LEVI.

The watcher intentionally uses only the Python standard library so it works on
Windows without an additional native file-system dependency. It observes file
metadata, batches changes, and emits read-only status events through LEVI's
existing EventBus. It never executes commands or reads file contents.
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Any


DEFAULT_POLL_SECONDS = 1.0

# These directories contain dependencies, generated output, caches, or runtime
# artifacts. They should not create noisy repository-change events.
IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
}
IGNORED_FILE_NAMES = {
    ".DS_Store",
}
IGNORED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".log",
    ".tmp",
    ".mp3",
    ".wav",
    ".webm",
}


def repo_root() -> Path:
    """Return the configured repository root, defaulting to this checkout."""
    configured = os.getenv("LEVI_REPO_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def _is_ignored(path: Path) -> bool:
    if any(part in IGNORED_DIR_NAMES for part in path.parts):
        return True
    if path.name in IGNORED_FILE_NAMES:
        return True
    return path.suffix.lower() in IGNORED_SUFFIXES


def snapshot_repository(root: Path | None = None) -> dict[str, tuple[int, int, int]]:
    """Create a metadata-only snapshot keyed by path relative to *root*."""
    root = (root or repo_root()).resolve()
    if not root.exists() or not root.is_dir():
        return {}

    snapshot: dict[str, tuple[int, int, int]] = {}
    for current_root, dir_names, file_names in os.walk(root):
        current_path = Path(current_root)
        dir_names[:] = [name for name in dir_names if name not in IGNORED_DIR_NAMES]
        for name in file_names:
            path = current_path / name
            if _is_ignored(path):
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            relative = path.relative_to(root).as_posix()
            # Include ctime as a second signal for fast same-size edits on
            # file systems whose mtime resolution is coarser than the poll loop.
            snapshot[relative] = (stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)
    return snapshot


def _changes_between(
    previous: dict[str, tuple[int, int, int]],
    current: dict[str, tuple[int, int, int]],
) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for path in sorted(current.keys() - previous.keys()):
        changes.append({"path": path, "change": "added"})
    for path in sorted(previous.keys() - current.keys()):
        changes.append({"path": path, "change": "deleted"})
    for path in sorted(current.keys() & previous.keys()):
        if current[path] != previous[path]:
            changes.append({"path": path, "change": "modified"})
    return changes


def _status(root: Path, snapshot: dict[str, tuple[int, int]], running: bool = True) -> dict[str, Any]:
    return {
        "root": str(root),
        "running": running,
        "file_count": len(snapshot),
        "poll_seconds": float(os.getenv("LEVI_REPO_POLL_SECONDS", DEFAULT_POLL_SECONDS)),
    }


def get_repo_status() -> dict[str, Any]:
    """Return a one-shot repository status suitable for the REST API."""
    root = repo_root()
    snapshot = snapshot_repository(root)
    return {"success": True, **_status(root, snapshot, running=False)}


async def repo_watcher_loop(event_bus=None) -> None:
    """Poll the local checkout and broadcast change batches over EventBus."""
    root = repo_root()
    previous = await asyncio.to_thread(snapshot_repository, root)
    if event_bus:
        await event_bus.emit("repo_watcher_ready", _status(root, previous))

    try:
        poll_seconds = max(0.25, float(os.getenv("LEVI_REPO_POLL_SECONDS", DEFAULT_POLL_SECONDS)))
    except ValueError:
        poll_seconds = DEFAULT_POLL_SECONDS

    while True:
        try:
            current = await asyncio.to_thread(snapshot_repository, root)
            changes = _changes_between(previous, current)
            if changes and event_bus:
                await event_bus.emit(
                    "repo_changed",
                    {
                        **_status(root, current),
                        "changes": changes[:200],
                        "change_count": len(changes),
                        "truncated": len(changes) > 200,
                    },
                )
            previous = current
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if event_bus:
                await event_bus.emit(
                    "repo_watcher_error",
                    {"root": str(root), "error": f"{type(exc).__name__}: {exc}"},
                )
        await asyncio.sleep(poll_seconds)


__all__ = ["get_repo_status", "repo_root", "repo_watcher_loop", "snapshot_repository"]

