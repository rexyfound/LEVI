"""Lightweight task-role routing for LEVI.

This module deliberately contains no framework code. It gives the model router a
small, deterministic role signal so provider selection is based on the job rather
than on one global model order.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class AgentRole:
    name: str
    description: str
    preferred_providers: tuple[str, ...]
    max_steps: int = 6
    execution_mode: str = "action"  # "research" or "action"


ROLES = {
    "coding": AgentRole(
        name="coding",
        description="Software engineering, debugging, repository changes, tests, and terminal work.",
        preferred_providers=("groq", "openrouter", "anthropic", "manus", "ollama"),
        max_steps=10,
    ),
    "design": AgentRole(
        name="design",
        description="Visual design, UI/UX, image understanding, creative direction, and frontend styling.",
        preferred_providers=("groq", "openrouter", "gemini", "ollama"),
        max_steps=6,
    ),
    "research": AgentRole(
        name="research",
        description="AI-side research, product discovery, comparison, explanation, summarization, and current-information tasks.",
        preferred_providers=("groq", "openrouter", "gemini", "ollama"),
        max_steps=3,
        execution_mode="research",
    ),
    "automation": AgentRole(
        name="automation",
        description="Browser, desktop, application, filesystem, and personal workflow actions.",
        preferred_providers=("groq", "openrouter", "anthropic", "ollama"),
        max_steps=10,
    ),
    "general": AgentRole(
        name="general",
        description="Conversation, planning, personal-assistant requests, and everyday questions.",
        preferred_providers=("groq", "openrouter", "gemini", "ollama"),
        max_steps=6,
    ),
}


_RESEARCH_INTENT = re.compile(
    r"\b(research|compare|comparison|latest|current|news|summarize|explain|find out|find|search|recommend|suggest|best|which|buy|price|specs|specification|specifications|review|option|options|alternative|alternatives)\b",
    re.I,
)


_KEYWORDS = {
    "coding": re.compile(
        r"\b(code|coding|debug|bug|error|exception|python|javascript|typescript|react|api|backend|frontend|repository|repo|git|test|build|implement|refactor|function|class|sql|terminal)\b",
        re.I,
    ),
    "design": re.compile(
        r"\b(design|designer|ui|ux|layout|style|visual|image|logo|color|wireframe|mockup|frontend design)\b",
        re.I,
    ),
    "research": re.compile(
        r"\b(research|compare|comparison|latest|current|news|summarize|explain|find out|find|sources|report|search|recommend|suggest|best|which|buy|price|specs|specification|specifications|review|option|options|alternative|alternatives|product|products|keyboard|laptop|phone|monitor|headphones|gear)\b",
        re.I,
    ),
    "automation": re.compile(
        r"\b(open|launch|click|type|browse|browser|website|download|send|schedule|remind|monitor|screen|desktop|clipboard|volume|lock|sleep)\b",
        re.I,
    ),
}


def classify_task(text: str) -> AgentRole:
    """Return the highest-signal role for a user request.

    Coding wins over design because repository/UI implementation requests often
    contain both words. Automation wins over general conversation when an action
    is explicitly requested.
    """
    text = (text or "").strip()
    if not text:
        return ROLES["general"]

    # Explicit computer-control verbs take precedence when combined with a
    # research object, e.g. "open a browser and find a keyboard".
    if _KEYWORDS["automation"].search(text):
        return ROLES["automation"]

    # Recommendation/research intent wins over incidental domain words such as
    # "coding" in "best laptop for coding".
    if _RESEARCH_INTENT.search(text):
        return ROLES["research"]

    for role_name in ("coding", "design", "research"):
        if _KEYWORDS[role_name].search(text):
            return ROLES[role_name]

    return ROLES["general"]


def provider_order(role: AgentRole, configured: str | None = None) -> list[str]:
    """Return role preferences, optionally honoring a comma-separated override."""
    if configured:
        requested = [item.strip().lower() for item in configured.split(",") if item.strip()]
        if requested:
            return requested
    return list(role.preferred_providers)


__all__ = ["AgentRole", "ROLES", "classify_task", "provider_order"]

