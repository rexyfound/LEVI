"""Small Claude adapter using the official Anthropic HTTP API.

The adapter converts LEVI's OpenAI-shaped messages/tools into Anthropic's
content-block format and converts the response back to the shape expected by
agent.py. It is optional: without ANTHROPIC_API_KEY the router skips it.
"""
from __future__ import annotations

import json
import os
from typing import Any

import requests
try:
    from dotenv import load_dotenv
except ImportError:  # Optional for test environments; os.environ still works.
    def load_dotenv(*args, **kwargs):
        return False

load_dotenv()


API_URL = "https://api.anthropic.com/v1/messages"


def _to_anthropic_tools(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    converted = []
    for tool in tools or []:
        fn = tool.get("function", tool)
        if not fn.get("name"):
            continue
        converted.append(
            {
                "name": fn["name"],
                "description": fn.get("description", ""),
                "input_schema": fn.get(
                    "parameters",
                    {"type": "object", "properties": {}},
                ),
            }
        )
    return converted


def _to_anthropic_messages(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    system_parts = []
    converted = []

    for message in messages:
        role = message.get("role")
        content = message.get("content")

        if role == "system":
            if isinstance(content, str) and content.strip():
                system_parts.append(content)
            continue

        if role == "tool":
            converted.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": message.get("tool_call_id", "unknown"),
                            "content": content if isinstance(content, str) else json.dumps(content),
                        }
                    ],
                }
            )
            continue

        if role == "assistant" and message.get("tool_calls"):
            blocks = []
            if isinstance(content, str) and content.strip():
                blocks.append({"type": "text", "text": content})
            for call in message.get("tool_calls", []):
                fn = call.get("function", {})
                raw_args = fn.get("arguments", {})
                if isinstance(raw_args, str):
                    try:
                        raw_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        raw_args = {}
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": call.get("id", "unknown"),
                        "name": fn.get("name", "unknown"),
                        "input": raw_args if isinstance(raw_args, dict) else {},
                    }
                )
            converted.append({"role": "assistant", "content": blocks})
            continue

        if role in {"user", "assistant"}:
            if not converted or converted[-1]["role"] != role:
                converted.append({"role": role, "content": content or ""})
            else:
                # Anthropic requires alternating user/assistant turns.
                previous = converted[-1]["content"]
                converted[-1]["content"] = f"{previous}\n{content or ''}" if isinstance(previous, str) else previous

    return "\n\n".join(system_parts), converted


def _from_anthropic(response: dict[str, Any]) -> dict[str, Any]:
    text_parts = []
    tool_calls = []

    for block in response.get("content", []):
        if block.get("type") == "text":
            text_parts.append(block.get("text", ""))
        elif block.get("type") == "tool_use":
            tool_calls.append(
                {
                    "id": block.get("id", "unknown"),
                    "type": "function",
                    "function": {
                        "name": block.get("name", "unknown"),
                        "arguments": json.dumps(block.get("input", {}), ensure_ascii=False),
                    },
                }
            )

    result = {"role": "assistant", "content": "\n".join(text_parts).strip()}
    if tool_calls:
        result["tool_calls"] = tool_calls
    return result


def chat_with_anthropic(messages, tools=None):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    system, converted_messages = _to_anthropic_messages(messages)
    payload = {
        "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        "max_tokens": int(os.getenv("CLAUDE_MAX_TOKENS", "4096")),
        "messages": converted_messages,
    }
    if system:
        payload["system"] = system
    anthropic_tools = _to_anthropic_tools(tools)
    if anthropic_tools:
        payload["tools"] = anthropic_tools

    response = requests.post(
        os.getenv("ANTHROPIC_API_URL", API_URL),
        headers={
            "x-api-key": api_key,
            "anthropic-version": os.getenv("ANTHROPIC_VERSION", "2023-06-01"),
            "content-type": "application/json",
        },
        json=payload,
        timeout=int(os.getenv("CLAUDE_TIMEOUT", "45")),
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Claude API {response.status_code}: {response.text[:500]}")
    return _from_anthropic(response.json())


__all__ = ["chat_with_anthropic"]

