import json
import os
import time
import re

MEMORY_ROOT = os.getenv("LEVI_DATA_DIR", os.path.dirname(__file__))
MEMORY_FILE = os.path.join(MEMORY_ROOT, "long_term.json")

MAX_SESSION_SUMMARY_CHARS = 2000
MAX_SESSIONS = 100
MAX_ACTIVE_PROJECTS = 50
MAX_MONITORED_TOPICS = 50
_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_ -]?key|token|secret|password|authorization|bearer)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?i)\bAIza[A-Za-z0-9_-]{20,}"),
)


def sanitize_memory_text(text: str, limit: int = MAX_SESSION_SUMMARY_CHARS) -> str:
    """Trim transient text and redact common credential patterns before storage."""
    value = " ".join(str(text or "").split())[:limit]
    for pattern in _SECRET_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value.strip()


DEFAULT_MEMORY = {
    "user": {
        "name": "Sir",
        "preferences": {}
    },
    "assistant": {
        "name": "LEVI",
        "version": "Mark L Engine"
    },
    "active_projects": [],
    "sessions": [],
    "monitored_topics": []
}

def load_memory() -> dict:
    if not os.path.exists(MEMORY_FILE):
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[MEMORY_MANAGER] Error loading memory: {e}")
        return DEFAULT_MEMORY.copy()

def _bounded_memory(data: dict) -> dict:
    """Keep persistent memory small and sanitize session summaries."""
    if not isinstance(data, dict):
        return json.loads(json.dumps(DEFAULT_MEMORY))

    sessions = []
    for item in data.get("sessions", [])[-MAX_SESSIONS:]:
        if not isinstance(item, dict):
            continue
        copy = dict(item)
        copy["summary"] = sanitize_memory_text(copy.get("summary", ""))
        if copy["summary"]:
            sessions.append(copy)
    data["sessions"] = sessions[-MAX_SESSIONS:]
    data["active_projects"] = [str(item)[:200] for item in data.get("active_projects", []) if str(item).strip()][-MAX_ACTIVE_PROJECTS:]
    data["monitored_topics"] = [item for item in data.get("monitored_topics", []) if isinstance(item, dict)][-MAX_MONITORED_TOPICS:]
    return data


def save_memory(data: dict):
    try:
        data = _bounded_memory(data)
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[MEMORY_MANAGER] Error saving memory: {e}")

def add_session_summary(summary_text: str):
    clean_summary = sanitize_memory_text(summary_text)
    if not clean_summary:
        return {"success": False, "error": "Memory summary cannot be empty."}

    data = load_memory()
    for existing in reversed(data.get("sessions", [])):
        if sanitize_memory_text(existing.get("summary", "")) == clean_summary:
            return existing

    session_entry = {
        "id": f"sess_{int(time.time() * 1000)}",
        "timestamp": time.time(),
        "summary": clean_summary,
        "consumed": False,
    }
    data.setdefault("sessions", []).append(session_entry)
    save_memory(data)
    return session_entry

def get_latest_unconsumed_session() -> dict | None:
    data = load_memory()
    sessions = data.get("sessions", [])
    unconsumed = [s for s in sessions if not s.get("consumed", False)]
    if unconsumed:
        return unconsumed[-1]
    return None

def consume_session(session_id: str):
    data = load_memory()
    for s in data.get("sessions", []):
        if s.get("id") == session_id:
            s["consumed"] = True
            break
    save_memory(data)

def add_monitored_topic(topic: str) -> dict:
    topic_clean = " ".join(topic.strip().split())[:200]
    data = load_memory()
    monitors = data.setdefault("monitored_topics", [])
    
    # Check if exists
    for item in monitors:
        if item["topic"].lower() == topic_clean.lower():
            return {"success": False, "message": f"Topic '{topic_clean}' is already being monitored."}
            
    new_entry = {
        "topic": topic_clean,
        "last_headline": "",
        "last_checked": 0,
        "added_at": time.time()
    }
    monitors.append(new_entry)
    save_memory(data)
    return {"success": True, "message": f"Now monitoring topic: '{topic_clean}'"}

def remove_monitored_topic(topic: str) -> dict:
    topic_clean = topic.strip().lower()
    data = load_memory()
    monitors = data.get("monitored_topics", [])
    initial_len = len(monitors)
    data["monitored_topics"] = [m for m in monitors if m["topic"].lower() != topic_clean]
    
    if len(data["monitored_topics"]) < initial_len:
        save_memory(data)
        return {"success": True, "message": f"Stopped monitoring topic: '{topic}'"}
    return {"success": False, "message": f"Topic '{topic}' was not found in monitors."}

def get_monitored_topics() -> list:
    data = load_memory()
    return data.get("monitored_topics", [])

def update_topic_headline(topic: str, headline: str):
    data = load_memory()
    headline = sanitize_memory_text(headline, limit=500)
    for m in data.get("monitored_topics", []):
        if m["topic"].lower() == topic.lower():
            m["last_headline"] = headline
            m["last_checked"] = time.time()
            break
    save_memory(data)

def add_active_project(project_name: str):
    project_name = " ".join(str(project_name or "").strip().split())[:200]
    if not project_name:
        return
    data = load_memory()
    projects = data.setdefault("active_projects", [])
    if project_name not in projects:
        projects.append(project_name)
        save_memory(data)

def get_active_projects() -> list:
    data = load_memory()
    return data.get("active_projects", [])
