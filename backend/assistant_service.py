"""Single request boundary shared by LEVI's API and native desktop UI."""
from __future__ import annotations

from typing import Any

from agent import run_agent
from conversation_manager import conversation_manager


def run_assistant(user_message: str, session_id: str | None = None) -> dict[str, Any]:
    """Execute one user request through LEVI's canonical agent pipeline."""
    if not isinstance(user_message, str) or not user_message.strip():
        return {"status": "error", "response": "Enter a request."}
    normalized = user_message.strip()
    active_session_id = (session_id or "native-desktop").strip()[:128] or "native-desktop"
    conversation_context = conversation_manager.context_for(active_session_id)
    # Keep ordinary requests on the canonical agent path. Swarm is deliberately
    # limited to independent, read-only multi-domain requests.
    from swarm import should_use_swarm, run_swarm
    if should_use_swarm(normalized):
        result = run_swarm(normalized)
    else:
        result = run_agent(normalized, conversation_context=conversation_context)

    conversation_manager.add_turn(
        active_session_id,
        normalized,
        str(result.get("response") or ""),
        actions=result.get("completed_actions") or [],
    )
    return result


__all__ = ["run_assistant"]
