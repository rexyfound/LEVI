import os
from pending_actions import create_pending_action
from pathlib import Path

WORKSPACE = Path("D:/Projects").resolve()
DOCUMENTS = Path(os.getenv("LEVI_DOCUMENTS_ROOT", Path.home() / "Documents")).expanduser().resolve()
ALLOWED_ROOTS = (WORKSPACE, DOCUMENTS)


def _resolve_target(path):
    """Resolve a user path inside the project or the user's Documents folder."""
    requested = Path(str(path or ".")).expanduser()
    target = requested.resolve() if requested.is_absolute() else (WORKSPACE / requested).resolve()
    if not any(target == root or root in target.parents for root in ALLOWED_ROOTS):
        return None
    return target


def list_files(path="."):
    target = _resolve_target(path)

    if target is None:
        return {"error": "Access outside workspace denied"}

    if not target.exists():
        return {"error": "Path does not exist"}

    if not target.is_dir():
        return {"error": "Path is not a directory"}

    return {
        "path": str(target),
        "files": [
            {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file"
            }
            for item in target.iterdir()
        ]
    }


def read_file(path):
    target = _resolve_target(path)

    if target is None:
        return {"error": "Access outside workspace denied"}

    if not target.exists() or not target.is_file():
        return {"error": "File does not exist"}

    return {
        "path": str(target),
        "content": target.read_text(
            encoding="utf-8",
            errors="replace"
        )
    }

def write_file(path, content):
    target = _resolve_target(path)

    if target is None:
        return {"error": "Access outside workspace denied"}

    if target.exists():
        action_id = create_pending_action(
            "overwrite_file",
            {
                "path": str(target),
                "content": content
            }
        )

        return {
            "requires_confirmation": True,
            "action_id": action_id,
            "action": "overwrite_file",
            "path": str(target)
        }

    try:
        target.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        target.write_text(
            content,
            encoding="utf-8"
        )

        return {
            "success": True,
            "action": "created",
            "path": str(target)
        }

    except Exception as e:
        return {"error": str(e)}
