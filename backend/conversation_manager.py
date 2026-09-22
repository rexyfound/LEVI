"""Small, session-scoped working memory for natural follow-up requests."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import threading
import time


MAX_TURNS_PER_SESSION = 8
MAX_CONTEXT_CHARS = 6_000


@dataclass
class ConversationTurn:
    user: str
    assistant: str
    actions: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


class ConversationManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: dict[str, deque[ConversationTurn]] = {}

    def context_for(self, session_id: str) -> str:
        with self._lock:
            turns = list(self._sessions.get(session_id, ()))

        if not turns:
            return ""

        sections: list[str] = []
        for turn in turns:
            sections.append(f"User: {turn.user}")
            sections.append(f"LEVI: {turn.assistant}")
            for action in turn.actions:
                tool = action.get("tool")
                result = action.get("result") or {}
                path = result.get("path") if isinstance(result, dict) else None
                if tool and path:
                    sections.append(f"Verified tool output: {tool} succeeded for {path}")

        context = "\n".join(sections)
        return context[-MAX_CONTEXT_CHARS:]

    def add_turn(self, session_id: str, user: str, assistant: str, actions: list[dict] | None = None) -> None:
        if not user or not assistant:
            return
        with self._lock:
            history = self._sessions.setdefault(session_id, deque(maxlen=MAX_TURNS_PER_SESSION))
            history.append(ConversationTurn(user=user, assistant=assistant, actions=actions or []))


conversation_manager = ConversationManager()


__all__ = ["conversation_manager"]
