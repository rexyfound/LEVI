import os
import re
from openai import OpenAI
import json

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "qwen/qwen3.6-27b"


def chat_with_cloud(messages, tools=None):

    # Sanitize messages before sending them to Groq
    clean_messages = []

    for msg in messages:
        clean = {
            k: v for k, v in msg.items()
            if k in {
                "role",
                "content",
                "name",
                "tool_call_id",
                "tool_calls"
            }
        }

        clean_messages.append(clean)

    kwargs = {
        "model": MODEL,
        "messages": clean_messages,
        "temperature": 0.1,
    }

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = client.chat.completions.create(**kwargs)

    message = response.choices[0].message

    content = message.content or ""

    # Don't expose <think>...</think>
    content = re.sub(
        r"<think>.*?</think>",
        "",
        content,
        flags=re.DOTALL
    ).strip()

    result = {
    "role": "assistant",
    "content": content
}

    if message.tool_calls:
        result["tool_calls"] = []

    tool_calls = message.tool_calls or []

    if tool_calls:
        result["tool_calls"] = []

    for call in tool_calls:
        arguments = call.function.arguments

        if not isinstance(arguments, str):
            arguments = json.dumps(arguments)

        result["tool_calls"].append({
            "id": call.id,
            "type": "function",
            "function": {
                "name": call.function.name,
                "arguments": arguments
            }
        })

    return result
