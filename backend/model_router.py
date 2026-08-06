import time
from providers.gemini_provider import chat_with_gemini
from cloud_client import chat_with_cloud
from ollama_client import chat_with_ollama


PROVIDERS = [
    {
        "name": "groq",
        "priority": 2,
        "supports_tools": True,
        "handler": chat_with_cloud,
        "local": False,
    },
    {
        "name": "gemini",
        "priority": 1,
        "supports_tools": True,
        "handler": chat_with_gemini,
        "local": False,
    },
    {
        "name": "ollama",
        "priority": 999,
        "supports_tools": True,
        "handler": chat_with_ollama,
        "local": True,
    }
    
]


provider_stats = {
    provider["name"]: {
        "healthy": True,
        "latency": None,
        "failures": 0
    }
    for provider in PROVIDERS
}


def provider_score(provider):
    stats = provider_stats[provider["name"]]

    # Local Ollama should remain final fallback
    if provider["local"]:
        return 10000

    latency = stats["latency"]

    if latency is None:
        latency = 1.0

    failure_penalty = stats["failures"] * 3

    return (
        provider["priority"]
        + latency
        + failure_penalty
    )


def chat_with_router(messages, tools=None, preferred_provider=None):

    available = []

    for provider in PROVIDERS:

        if tools and not provider["supports_tools"]:
            continue

        available.append(provider)

    available.sort(key=provider_score)

    # --------------------------------
    # Sticky provider
    # --------------------------------

    if preferred_provider:

        preferred = get_provider(preferred_provider)

        if preferred and preferred in available:
            available.remove(preferred)
            available.insert(0, preferred)

    last_error = None

    for provider in available:

        name = provider["name"]
        handler = provider["handler"]

        print(f"[ROUTER] Trying {name.upper()}...")

        start = time.perf_counter()

        try:
            response = handler(messages, tools)

            latency = time.perf_counter() - start

            provider_stats[name]["healthy"] = True
            provider_stats[name]["latency"] = latency
            provider_stats[name]["failures"] = 0

            print(
                f"[ROUTER] {name.upper()} success "
                f"({latency:.2f}s)"
            )

            # Important:
            # return provider name too
            return response, name

        except Exception as e:

            latency = time.perf_counter() - start

            provider_stats[name]["healthy"] = False
            provider_stats[name]["latency"] = latency
            provider_stats[name]["failures"] += 1

            last_error = e

            print(
                f"[ROUTER] {name.upper()} failed "
                f"after {latency:.2f}s: {repr(e)}"
            )

    raise RuntimeError(
        f"All LEVI model providers failed. "
        f"Last error: {repr(last_error)}"
    )
def get_provider(name):
    for provider in PROVIDERS:
        if provider["name"] == name:
            return provider

    return None