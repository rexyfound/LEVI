"""Bounded, safety-first concurrent workers for independent read-oriented goals."""
from __future__ import annotations

import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

from event_bus import event_bus


@dataclass(frozen=True)
class SwarmTask:
    task_id: str
    role: str
    instruction: str


_RISKY = re.compile(
    r"\b(write|edit|delete|remove|send|submit|purchase|buy|pay|launch|open|click|type|download|install|change|lock|sleep)\b",
    re.I,
)
_CONJUNCTION = re.compile(r"\b(and|also|then|while|plus)\b", re.I)


def _tasks_for(request: str) -> list[SwarmTask]:
    tasks: list[SwarmTask] = []
    lower = request.lower()
    if re.search(r"\b(research|latest|current|news|compare|summari[sz]e|find|pricing|prices|sources?)\b", lower):
        tasks.append(SwarmTask("research", "researcher", f"Research only the information portion of this request and return concise sourced findings: {request}"))
    if re.search(r"\b(server|backend|process|running|status|health|terminal)\b", lower):
        tasks.append(SwarmTask("system", "sysadmin", f"Check only the local system/server status requested here. Do not modify anything: {request}"))
    if re.search(r"\b(code|repository|repo|test|debug|build|implement)\b", lower):
        tasks.append(SwarmTask("engineering", "developer", f"Inspect or test only the engineering portion of this request. Do not edit files: {request}"))
    return tasks


def should_use_swarm(request: str) -> bool:
    """Use swarm only for clearly independent, read-only multi-domain requests."""
    if os.getenv("LEVI_SWARM_ENABLED", "1").lower() in {"0", "false", "no"}:
        return False
    return bool(_CONJUNCTION.search(request) and not _RISKY.search(request) and len(_tasks_for(request)) >= 2)


def _run_worker(run_id: str, task: SwarmTask, request: str) -> dict[str, Any]:
    event_bus.emit_sync("swarm_task_started", {"run_id": run_id, "task_id": task.task_id, "role": task.role})
    try:
        from agent import run_agent
        with event_bus.suppress_thread_events():
            result = run_agent(task.instruction, speak_response=False)
        result = result if isinstance(result, dict) else {"response": str(result)}
        event_bus.emit_sync("swarm_task_completed", {
            "run_id": run_id, "task_id": task.task_id, "role": task.role,
            "status": result.get("status", "complete"),
        })
        return {"task_id": task.task_id, "role": task.role, **result}
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        event_bus.emit_sync("swarm_task_failed", {"run_id": run_id, "task_id": task.task_id, "role": task.role, "error": message})
        return {"task_id": task.task_id, "role": task.role, "status": "error", "error": message}


def run_swarm(request: str) -> dict[str, Any]:
    tasks = _tasks_for(request)
    run_id = uuid.uuid4().hex
    event_bus.emit_sync("swarm_started", {"run_id": run_id, "task_count": len(tasks)})
    max_workers = max(2, min(len(tasks), int(os.getenv("LEVI_SWARM_MAX_WORKERS", "3"))))
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="levi-swarm") as pool:
        futures = [pool.submit(_run_worker, run_id, task, request) for task in tasks]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item["task_id"])
    sections = []
    for result in results:
        heading = result["role"].capitalize()
        body = result.get("response") or result.get("error") or "No result returned."
        sections.append(f"{heading}: {body}")
    response = "\n".join(sections)
    success = all(item.get("status") not in {"error", "stopped"} for item in results)
    event_bus.emit_sync("swarm_completed", {"run_id": run_id, "status": "complete" if success else "partial"})
    try:
        from voice import speak
        speak(response)
    except Exception:
        pass
    event_bus.emit_sync("message", {"role": "assistant", "content": response})
    event_bus.emit_sync("task_completed", {"success": success, "response": response, "run_id": run_id})
    return {"status": "complete" if success else "error", "response": response, "run_id": run_id, "swarm": True, "results": results}


__all__ = ["run_swarm", "should_use_swarm"]
