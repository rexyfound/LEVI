"""Lightweight role-aware provider router with health-aware fallbacks."""
from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from event_bus import event_bus
from providers.provider_registry import PROVIDER_REGISTRY, provider_is_configured, provider_supports
from agent_roles import AgentRole, provider_order


executor = ThreadPoolExecutor(max_workers=4)
DECAY_INTERVAL_SECONDS = 300
COOLDOWN_SECONDS = max(1.0, float(os.getenv("LEVI_PROVIDER_COOLDOWN", "20")))
MAX_COOLDOWN_SECONDS = max(COOLDOWN_SECONDS, float(os.getenv("LEVI_PROVIDER_MAX_COOLDOWN", "180")))

provider_stats = {
    provider["name"]: {
        "healthy": True,
        "latency": None,
        "failures": 0,
        "last_failure_time": None,
        "cooldown_until": 0.0,
    }
    for provider in PROVIDER_REGISTRY
}


def _decayed_failures(stats):
    failures = stats.get("failures", 0)
    last_failure = stats.get("last_failure_time")
    if failures == 0 or last_failure is None:
        return 0
    periods = int((time.time() - last_failure) / DECAY_INTERVAL_SECONDS)
    return max(0, failures >> periods) if periods else failures


def _stats_for(name):
    return provider_stats.setdefault(
        name,
        {
            "healthy": True,
            "latency": None,
            "failures": 0,
            "last_failure_time": None,
            "cooldown_until": 0.0,
        },
    )


def _cooldown_remaining(stats):
    return max(0.0, float(stats.get("cooldown_until", 0.0)) - time.time())


def _mark_failure(name, latency):
    stats = _stats_for(name)
    stats.update({"healthy": False, "latency": latency, "last_failure_time": time.time()})
    stats["failures"] = stats.get("failures", 0) + 1
    cooldown = min(COOLDOWN_SECONDS * (2 ** (stats["failures"] - 1)), MAX_COOLDOWN_SECONDS)
    stats["cooldown_until"] = time.time() + cooldown
    return stats, cooldown


def get_provider(name):
    return next((provider for provider in PROVIDER_REGISTRY if provider["name"] == name), None)


def provider_score(provider, role_order=None):
    stats = _stats_for(provider["name"])
    latency = stats["latency"] if stats["latency"] is not None else 1.0
    failure_penalty = _decayed_failures(stats) * 3
    role_rank = role_order.index(provider["name"]) if role_order and provider["name"] in role_order else 50
    local_penalty = 1000 if provider.get("local") else 0
    return role_rank * 10 + provider["priority"] + latency + failure_penalty + local_penalty


def _role_name(role):
    if isinstance(role, AgentRole):
        return role.name
    if isinstance(role, str) and role:
        return role
    return "general"


def chat_with_router(messages, tools=None, preferred_provider=None, role=None):
    role_name = _role_name(role)
    configured_order = os.getenv("LEVI_PROVIDER_ORDER")
    role_order = provider_order(role, configured_order) if isinstance(role, AgentRole) else []

    available = []
    cooling_down = []
    skipped: list[str] = []
    for provider in PROVIDER_REGISTRY:
        name = provider["name"]
        if not provider_is_configured(provider):
            skipped.append(f"{name}: not configured")
            continue
        if tools and not provider_supports(provider, "tools"):
            reason = "tools unsupported"
            skipped.append(f"{name}: {reason}")
            event_bus.emit_sync("provider_skipped", {"provider": name, "role": role_name, "reason": reason})
            continue
        remaining = _cooldown_remaining(_stats_for(name))
        if remaining > 0:
            reason = f"cooldown {remaining:.1f}s"
            skipped.append(f"{name}: {reason}")
            cooling_down.append((remaining, provider))
            event_bus.emit_sync("provider_skipped", {"provider": name, "role": role_name, "reason": reason})
            continue
        available.append(provider)

    if not available:
        # A transient provider failure must not make LEVI unusable until the
        # entire cooldown window expires. Retry the provider with the shortest
        # cooldown when every configured candidate is temporarily cooling down.
        # This is still bounded by the provider's own request timeout and lets
        # the normal fallback loop try the next provider if it fails again.
        if cooling_down:
            remaining, retry_provider = min(cooling_down, key=lambda item: item[0])
            available = [retry_provider]
            event_bus.emit_sync("provider_retry_available", {
                "provider": retry_provider["name"],
                "role": role_name,
                "cooldown_remaining": round(remaining, 1),
            })
        else:
            detail = "; ".join(skipped) if skipped else "none configured"
            raise RuntimeError(f"No provider available for the {role_name} task ({detail}).")

    available.sort(key=lambda item: provider_score(item, role_order))

    if preferred_provider:
        preferred = get_provider(preferred_provider)
        if preferred and preferred in available:
            available.remove(preferred)
            available.insert(0, preferred)

    last_error = None
    for provider in available:
        name = provider["name"]
        timeout = provider["timeout"]
        event_bus.emit_sync("provider_started", {"provider": name, "role": role_name})
        start = time.perf_counter()

        try:
            future = executor.submit(provider["handler"], messages, tools)
            response = future.result(timeout=timeout)
            latency = time.perf_counter() - start
            stats = _stats_for(name)
            stats.update({"healthy": True, "latency": latency, "failures": 0, "last_failure_time": None, "cooldown_until": 0.0})
            event_bus.emit_sync(
                "provider_completed",
                {"provider": name, "role": role_name, "duration_ms": int(latency * 1000)},
            )
            return response, name
        except TimeoutError:
            future.cancel()
            latency = time.perf_counter() - start
            _stats, cooldown = _mark_failure(name, latency)
            last_error = TimeoutError(f"{name} timed out")
            event_bus.emit_sync("provider_failed", {"provider": name, "role": role_name, "error": "timeout", "cooldown_seconds": cooldown})
        except Exception as exc:
            latency = time.perf_counter() - start
            _stats, cooldown = _mark_failure(name, latency)
            last_error = exc
            event_bus.emit_sync("provider_failed", {"provider": name, "role": role_name, "error": str(exc), "cooldown_seconds": cooldown})

    raise RuntimeError(f"All available providers failed for the {role_name} task: {last_error}") from last_error


def chat_with_router_with_backoff(messages, tools=None, preferred_provider=None, role=None, max_retries=2):
    last_exc = None
    for attempt in range(max(1, max_retries)):
        try:
            return chat_with_router(messages, tools, preferred_provider, role=role)
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                time.sleep(0.5 * (2 ** attempt))
    raise last_exc


__all__ = ["chat_with_router", "chat_with_router_with_backoff", "provider_stats", "get_provider"]
