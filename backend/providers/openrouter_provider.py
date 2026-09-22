import os
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False
from providers.provider_utils import openai_compatible_chat

load_dotenv()

def chat_with_openrouter(messages, tools=None):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured in environment")
    
    model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
    
    return openai_compatible_chat(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        model=model,
        messages=messages,
        tools=tools,
        max_tokens=int(os.getenv("LEVI_MAX_OUTPUT_TOKENS", "2048")),
        temperature=0.1
    )
