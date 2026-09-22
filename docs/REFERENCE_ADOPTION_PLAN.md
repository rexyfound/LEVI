# LEVI Reference Adoption Plan

## Decision

LEVI will remain a lightweight backend-first personal assistant built around `backend/ui.py`, the existing agent loop, provider registry, event bus, memory bridge, voice manager, and optional MCP. The Mark XXXIX-OR repository is used as a source of reliability patterns, not as a codebase to copy or a replacement architecture.

## Target execution path

Every user request should follow one path:

1. `ui.py` or the API receives the request.
2. The assistant service classifies the task into a specialist role.
3. The role-aware provider router selects a configured, capable, healthy provider.
4. The agent executes tools through the existing approval boundary.
5. The agent returns a concise answer and optionally speaks it.
6. A bounded, sanitized memory update runs after completion without delaying the answer.
7. Events expose only useful lifecycle status to the lightweight UI.

## Prioritized changes

| Priority | Change | Files | Acceptance criterion |
|---:|---|---|---|
| 1 | Centralize request execution so `ui.py` and `/chat` use the same service | `backend/assistant_service.py`, `backend/ui.py`, `backend/main.py` | Both entry points produce the same role, provider, tool, voice, and memory behavior |
| 2 | Add provider cooldowns and capability-aware fallback diagnostics | `backend/model_router.py`, `backend/providers/provider_registry.py` | Failed or incompatible providers are skipped with a concise reason and bounded retry count |
| 3 | Add MCP status and per-server timeout controls | `backend/integrations/mcp_manager.py`, `backend/main.py`, `.env.example` | MCP remains optional; a broken server cannot block startup or hang a request |
| 4 | Bound and sanitize memory updates | `backend/integrations/openclaw_client.py`, `backend/memory/memory_manager.py` | Secrets, credentials, raw tool output, and oversized transient context are never persisted |
| 5 | Formalize specialist output contracts | `backend/agent_roles.py`, `backend/agent.py` | Coding, design, research, automation, and general answers stay focused and concise |
| 6 | Keep voice asynchronous and cancellable | `backend/voice/*` | Text response is not delayed by speech and shutdown leaves no pending tasks |
| 7 | Keep progress compact | `backend/ui.py`, `backend/event_bus.py` | The UI shows actionable status without exposing internal reasoning or a heavy dashboard |

## Explicit non-goals

LEVI will not adopt the reference repository's large PyQt HUD, GPU telemetry subsystem, monolithic tool declaration list, tracked JSON credentials, or second independent provider client. Those additions increase maintenance cost without improving the requested personal-assistant workflow.

## Implementation rule

Only modify files that directly support the priorities above. Existing working modules remain in place unless a smaller replacement removes duplicated behavior or fixes a reliability defect. All changes will be delivered as exact file replacement or edit instructions; no archive will be produced.
