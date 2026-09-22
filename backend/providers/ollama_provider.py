import json
import uuid
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"

def _normalize_response(message):
    """
    Normalize Ollama's native response to match the OpenAI-compatible
    format expected by agent.py:
      - Ensure tool_calls have an "id" field
      - Ensure arguments are JSON strings, not dicts
    """
    result = {
        "role": message.get("role", "assistant"),
        "content": message.get("content") or "",
    }

    raw_calls = message.get("tool_calls")
    if raw_calls:
        normalized = []
        for call in raw_calls:
            fn = call.get("function", {})
            arguments = fn.get("arguments", {})

            # Ollama returns arguments as a dict; agent.py expects a string
            if not isinstance(arguments, str):
                arguments = json.dumps(arguments)

            normalized.append({
                "id": call.get("id") or f"ollama-{uuid.uuid4().hex[:8]}",
                "type": "function",
                "function": {
                    "name": fn.get("name", ""),
                    "arguments": arguments,
                },
            })

        result["tool_calls"] = normalized

    return result

def chat_with_ollama(messages, tools=None):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }

    if tools:
        payload["tools"] = tools

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=35
    )

    response.raise_for_status()

    return _normalize_response(response.json()["message"])

def ask_ollama(messages):
    return chat_with_ollama(messages)["content"]
