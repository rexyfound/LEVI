import re
import json
from openai import OpenAI

def openai_compatible_chat(base_url, api_key, model, messages, tools=None, **extra_kwargs):
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    clean_messages = []
    for msg in messages:
        clean = {
            k: v for k, v in msg.items()
            if k in {"role", "content", "name", "tool_call_id", "tool_calls"}
        }
        clean_messages.append(clean)

    kwargs = {
        "model": model,
        "messages": clean_messages,
    }
    kwargs.update(extra_kwargs)

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = client.chat.completions.create(**kwargs)
    message = response.choices[0].message
    content = message.content or ""

    content = re.sub(
        r"<think>.*?</think>",
        "",
        content,
        flags=re.DOTALL,
    ).strip()

    result = {
        "role": "assistant",
        "content": content,
    }

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
                    "arguments": arguments,
                },
            })

    return result
