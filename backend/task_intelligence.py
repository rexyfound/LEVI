"""Deterministic task requirements used to ground LEVI's agent loop."""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class TaskRequirements:
    requires_tools: bool = False
    required_tool_names: frozenset[str] = frozenset()
    grounding_rules: tuple[str, ...] = ()

    def missing_tools(self, completed_tools: set[str]) -> set[str]:
        return set(self.required_tool_names) - completed_tools


def analyze_task_requirements(request: str, conversation_context: str = "") -> TaskRequirements:
    """Identify claims that need direct observation before LEVI can make them.

    This is intentionally deterministic: a model must not decide that evidence
    is optional for an action, a current fact, or a file it was asked to save.
    """
    text = (request or "").lower()
    required: set[str] = set()
    rules: list[str] = []

    wants_file = bool(re.search(
        r"\b(create|make|write|save|generate|build)\b[\s\S]{0,80}\b(file|document|folder|directory)\b|\.(?:py|js|ts|json|txt|md)\b",
        text,
    ))
    if wants_file:
        required.update({"write_file", "read_file"})
        rules.append("The user asked for a saved file. Do not say it was created unless write_file succeeded and its read-back verification succeeded.")

    wants_terminal_check = bool(re.search(
        r"\b(check|test|inspect|status|running|run)\b[\s\S]{0,60}\b(server|backend|process|port|terminal)\b",
        text,
    ))
    if wants_terminal_check:
        required.add("run_terminal")
        rules.append("Report local server, process, or terminal status only from run_terminal output.")

    wants_launch = bool(re.search(
        r"\b(run|launch|open|start)\b[\s\S]{0,50}\b(calculator|file|app|application|program|script)\b",
        text,
    ))
    wants_verified_follow_up = bool(re.search(r"\b(run it|do it|execute it|open it|start it)\b", text)) and "Verified tool output: write_file succeeded for" in conversation_context
    if wants_launch or wants_verified_follow_up:
        required.add("launch_app")
        rules.append("The user asked to run an application or verified file. Do not say it launched unless launch_app was approved and confirmed.")

    wants_browser_action = bool(re.search(
        r"\b(browser|website|webpage|url|click|navigate|fill|form)\b",
        text,
    ))
    if wants_browser_action:
        required.add("browser_open")
        rules.append("Do not claim browser navigation or page results without browser tool evidence.")

    wants_screen_observation = bool(re.search(
        r"\b(my screen|on screen|what am i looking at|screenshot|visible)\b",
        text,
    ))
    if wants_screen_observation:
        required.add("vision_analyze")
        rules.append("Describe the desktop only from a fresh screenshot analysis.")

    wants_current_facts = bool(re.search(
        r"\b(latest|current|today|news|price|pricing|recent|live|this week)\b",
        text,
    ))
    if wants_current_facts:
        required.add("parallel_web_search")
        rules.append("Use web-search evidence for time-sensitive facts and state uncertainty when sources conflict or are unavailable.")

    if not rules:
        rules.append("Separate known information from assumptions. If a requested fact is unknown, say so instead of guessing.")

    return TaskRequirements(
        requires_tools=bool(required),
        required_tool_names=frozenset(required),
        grounding_rules=tuple(rules),
    )


__all__ = ["TaskRequirements", "analyze_task_requirements"]
