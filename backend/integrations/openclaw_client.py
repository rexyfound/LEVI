import subprocess
import json
import os
import time
from unittest import result

def search_memory(query: str, max_results: int = 5):
    """
    Search OpenClaw's persistent memory.
    """

    try:
        command = [
            "openclaw",
            "memory",
            "search",
            "--query",
            query,
            "--max-results",
            str(max_results),
            "--json",
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15,
            shell=True,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr.strip()
                or result.stdout.strip()
                or "OpenClaw memory search failed",
            }

        output = result.stdout.strip()

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            data = output

        return {
            "success": True,
            "query": query,
            "results": data,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "OpenClaw memory search timed out",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
MEMORY_DIR = os.path.expanduser(
    "~/.openclaw/workspace/memory"
)

os.makedirs(
    MEMORY_DIR,
    exist_ok=True
)
def write_memory(text: str):

    timestamp = int(time.time())

    filename = os.path.join(
        MEMORY_DIR,
        f"memory_{timestamp}.md"
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(text)

    result = subprocess.run(
    [
        "openclaw",
        "memory",
        "index"
    ],
    capture_output=True,
    text=True
)

    print(result.stdout)
    print(result.stderr)
    print(result.returncode)

    return {
        "success": True,
        "memory": filename
    }