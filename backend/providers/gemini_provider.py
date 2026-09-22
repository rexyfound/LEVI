import os
import json
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def _dump_extra_content(call):
    """
    Gemini 3 returns its thought signature inside the OpenAI-compatible
    tool call's extra_content.google.thought_signature.

    Preserve it exactly so the next Gemini request can validate the
    previous function call.
    """
    extra = getattr(call, "extra_content", None)

    if extra is None:
        return None

    if hasattr(extra, "model_dump"):
        extra = extra.model_dump(exclude_none=True)

    if isinstance(extra, dict):
        return extra

    return None


def chat_with_gemini(messages, tools=None):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    kwargs = {
        "model": "gemini-3-flash-preview",
        "messages": messages,
        # Keep Gemini 3 reasoning cheap/fast. Thought signatures are still
        # required for function calling even at minimal reasoning.
        "reasoning_effort": "minimal",
    }

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = client.chat.completions.create(**kwargs)
    message = response.choices[0].message

    result = {
        "role": "assistant",
        "content": message.content or "",
    }

    if message.tool_calls:
        result["tool_calls"] = []

        for call in message.tool_calls:
            arguments = call.function.arguments

            if not isinstance(arguments, str):
                arguments = json.dumps(arguments)

            tool_call = {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": arguments,
                },
            }

            # CRITICAL for Gemini 3 multi-step function calling.
            extra_content = _dump_extra_content(call)

            if extra_content:
                tool_call["extra_content"] = extra_content

            result["tool_calls"].append(tool_call)

    return result