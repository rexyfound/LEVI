from pending_actions import create_pending_action
from pathlib import Path

WORKSPACE = Path("D:/Projects").resolve()


def list_files(path="."):
    target = (WORKSPACE / path).resolve()

    if not target.is_relative_to(WORKSPACE):
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
    target = (WORKSPACE / path).resolve()

    if not target.is_relative_to(WORKSPACE):
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
    target = (WORKSPACE / path).resolve()

    if not target.is_relative_to(WORKSPACE):
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
    try:
        target.parent.mkdir(parents=True, exist_ok=True)

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