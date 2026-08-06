import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"


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
        timeout=180
    )

    response.raise_for_status()

    return response.json()["message"]


def ask_ollama(messages):
    return chat_with_ollama(messages)["content"]