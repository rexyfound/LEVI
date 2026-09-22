"""Optional Manus API delegate.

This provider is intentionally advisory: Manus receives a coding prompt and
returns guidance or a proposed implementation. Local file changes still stay
behind LEVI's own tools and approval flow.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests
try:
    from dotenv import load_dotenv
except ImportError:  # Optional for test environments; os.environ still works.
    def load_dotenv(*args, **kwargs):
        return False

load_dotenv()


BASE_URL = os.getenv("MANUS_API_BASE", "https://api.manus.ai").rstrip("/")


def _headers() -> dict[str, str]:
    key = os.getenv("MANUS_API_KEY")
    if not key:
        raise RuntimeError("MANUS_API_KEY is not configured")
    return {
        "x-manus-api-key": key,
        "content-type": "application/json",
    }


def _prompt_from_messages(messages: list[dict[str, Any]]) -> str:
    parts = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if isinstance(content, str) and content.strip():
            parts.append(f"{role.upper()}: {content}")
    return "\n\n".join(parts)[-24000:]


def _event_text(event: dict[str, Any]) -> str:
    for key in ("content", "text", "message", "output"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = _event_text(value)
            if nested:
                return nested
        if isinstance(value, list):
            pieces = [_event_text(item) for item in value if isinstance(item, dict)]
            if any(pieces):
                return "\n".join(piece for piece in pieces if piece)
    return ""


def _final_text(messages: list[dict[str, Any]]) -> str:
    for event in reversed(messages):
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type", event.get("event_type", ""))).lower()
        if "status" in event_type or "tool" in event_type:
            continue
        text = _event_text(event)
        if text:
            return text
    return ""


def chat_with_manus(messages, tools=None):
    del tools  # Manus delegation does not expose LEVI's local tools directly.
    prompt = _prompt_from_messages(messages)
    response = requests.post(
        f"{BASE_URL}/v2/task.create",
        headers=_headers(),
        json={
            "message": {"content": prompt},
            "agent_profile": os.getenv("MANUS_AGENT_PROFILE", "manus-1.6-lite"),
            "interactive_mode": False,
            "hide_in_task_list": True,
            "share_visibility": "private",
            "title": "LEVI coding delegate",
        },
        timeout=int(os.getenv("MANUS_CREATE_TIMEOUT", "30")),
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Manus API {response.status_code}: {response.text[:500]}")

    created = response.json()
    task_id = created.get("task_id")
    if not task_id:
        raise RuntimeError("Manus did not return a task_id")

    deadline = time.monotonic() + float(os.getenv("MANUS_POLL_TIMEOUT", "120"))
    poll_seconds = float(os.getenv("MANUS_POLL_SECONDS", "2"))
    last_messages = []

    while time.monotonic() < deadline:
        current = requests.get(
            f"{BASE_URL}/v2/task.listMessages",
            headers=_headers(),
            params={"task_id": task_id},
            timeout=20,
        )
        if current.status_code >= 400:
            raise RuntimeError(f"Manus polling {current.status_code}: {current.text[:500]}")
        payload = current.json()
        last_messages = payload.get("messages", []) or []

        status = ""
        for event in reversed(last_messages):
            if not isinstance(event, dict):
                continue
            event_type = str(event.get("type", event.get("event_type", ""))).lower()
            if "status_update" in event_type or event.get("status"):
                status = str(event.get("status", event.get("state", ""))).lower()
                break

        if status in {"stopped", "completed", "done"}:
            break
        if status in {"error", "failed"}:
            raise RuntimeError(_final_text(last_messages) or "Manus task failed")
        time.sleep(poll_seconds)

    text = _final_text(last_messages)
    if not text:
        raise RuntimeError("Manus task timed out or returned no text")
    return {"role": "assistant", "content": text}


__all__ = ["chat_with_manus"]

