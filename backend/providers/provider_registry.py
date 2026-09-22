"""Provider registry with optional, environment-gated adapters."""
from __future__ import annotations

import os

from providers.groq_provider import chat_with_groq
from providers.gemini_provider import chat_with_gemini
from providers.openrouter_provider import chat_with_openrouter
from providers.ollama_provider import chat_with_ollama
from providers.anthropic_provider import chat_with_anthropic
from providers.manus_provider import chat_with_manus


def _configured(name: str) -> bool:
    return bool(os.getenv(name))


def _capabilities(*, tools: bool, vision: bool = False, streaming: bool = False) -> dict[str, bool]:
    return {
        "chat": True,
        "tools": tools,
        "vision": vision,
        "streaming": streaming,
    }


PROVIDER_REGISTRY = [
    {
        "name": "groq",
        "priority": 1,
        "supports_tools": True,
        "capabilities": _capabilities(tools=True),
        "handler": chat_with_groq,
        "local": False,
        "timeout": 6,
        "requires_env": "GROQ_API_KEY",
    },
    {
        "name": "openrouter",
        "priority": 2,
        "supports_tools": True,
        "capabilities": _capabilities(tools=True, vision=True),
        "handler": chat_with_openrouter,
        "local": False,
        "timeout": 10,
        "requires_env": "OPENROUTER_API_KEY",
    },
    {
        "name": "gemini",
        "priority": 3,
        "supports_tools": True,
        "capabilities": _capabilities(tools=True, vision=True),
        "handler": chat_with_gemini,
        "local": False,
        "timeout": 15,
        "requires_env": "GEMINI_API_KEY",
    },
    {
        "name": "anthropic",
        "priority": 4,
        "supports_tools": True,
        "capabilities": _capabilities(tools=True, vision=True),
        "handler": chat_with_anthropic,
        "local": False,
        "timeout": int(os.getenv("CLAUDE_TIMEOUT", "30")),
        "requires_env": "ANTHROPIC_API_KEY",
    },
    {
        "name": "manus",
        "priority": 5,
        "supports_tools": False,
        "capabilities": _capabilities(tools=False, vision=False),
        "handler": chat_with_manus,
        "local": False,
        "timeout": int(os.getenv("MANUS_POLL_TIMEOUT", "60")),
        "requires_env": "MANUS_API_KEY",
    },
    {
        "name": "ollama",
        "priority": 999,
        "supports_tools": True,
        "capabilities": _capabilities(tools=True),
        "handler": chat_with_ollama,
        "local": True,
        "timeout": 30,
        "requires_env": None,
    },
]


def provider_is_configured(provider: dict) -> bool:
    required = provider.get("requires_env")
    return not required or _configured(required)


def provider_supports(provider: dict, capability: str) -> bool:
    """Return whether a provider advertises a capability.

    ``supports_tools`` remains supported for compatibility with older custom
    registrations; new registrations should use the capabilities map.
    """
    capabilities = provider.get("capabilities") or {}
    if capability in capabilities:
        return bool(capabilities[capability])
    if capability == "tools":
        return bool(provider.get("supports_tools"))
    return False


def register_provider(
    name,
    handler,
    priority,
    timeout,
    local=False,
    supports_tools=True,
    requires_env=None,
    capabilities=None,
):
    PROVIDER_REGISTRY.append(
        {
            "name": name,
            "priority": priority,
            "supports_tools": supports_tools,
            "capabilities": capabilities or _capabilities(tools=supports_tools),
            "handler": handler,
            "local": local,
            "timeout": timeout,
            "requires_env": requires_env,
        }
    )


__all__ = ["PROVIDER_REGISTRY", "provider_is_configured", "provider_supports", "register_provider"]
