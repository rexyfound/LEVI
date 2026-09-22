import os
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False
from providers.provider_utils import openai_compatible_chat

load_dotenv()

def chat_with_groq(messages, tools=None):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured in environment")
    
    model = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
    
    return openai_compatible_chat(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
        model=model,
        messages=messages,
        tools=tools,
        max_tokens=int(os.getenv("LEVI_MAX_OUTPUT_TOKENS", "2048")),
        temperature=0.1
    )
