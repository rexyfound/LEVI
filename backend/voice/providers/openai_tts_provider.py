import os
import asyncio
import logging
from typing import Optional
from voice.base_provider import BaseTTSProvider

logger = logging.getLogger("LEVI.OpenAITTSProvider")

DEFAULT_OPENAI_VOICE = "onyx"  # Calm, deep, professional


class OpenAITTSProvider(BaseTTSProvider):
    """
    OpenAI Text-to-Speech API provider (supports tts-1 / tts-1-hd).
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, default_voice: Optional[str] = None):
        self.api_key = api_key or os.getenv("TTS_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("TTS_MODEL", "tts-1")
        self.default_voice = default_voice or os.getenv("TTS_VOICE", DEFAULT_OPENAI_VOICE)

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def synthesize(self, text: str, output_file_path: str, voice: Optional[str] = None) -> str:
        if not self.is_available():
            raise ValueError("OpenAI TTS API Key is not configured (TTS_API_KEY or OPENAI_API_KEY missing).")

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        selected_voice = voice or self.default_voice or DEFAULT_OPENAI_VOICE

        response = await client.audio.speech.create(
            model=self.model,
            voice=selected_voice,
            input=text,
            response_format="mp3",
        )

        await response.astream_to_file(output_file_path)
        return output_file_path
