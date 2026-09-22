import os
import logging
import httpx
from typing import Optional
from voice.base_provider import BaseTTSProvider

logger = logging.getLogger("LEVI.ElevenLabsProvider")

DEFAULT_ELEVENLABS_VOICE_ID = "cPoqAvGWCPfCfyPMwe4z"
DEFAULT_ELEVENLABS_MODEL_ID = "eleven_turbo_v2_5"  # Low latency, high quality neural model


class ElevenLabsTTSProvider(BaseTTSProvider):
    """
    ElevenLabs Text-to-Speech provider with streaming/direct audio synthesis.
    Supports custom voice IDs (including library voice cPoqAvGWCPfCfyPMwe4z).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY") or os.getenv("TTS_API_KEY")
        self.voice_id = voice_id or os.getenv("TTS_VOICE", DEFAULT_ELEVENLABS_VOICE_ID)
        self.model_id = model_id or os.getenv("TTS_MODEL", DEFAULT_ELEVENLABS_MODEL_ID)

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def synthesize(
        self,
        text: str,
        output_file_path: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        stability: float = 0.5,
        similarity_boost: float = 0.8,
    ) -> str:
        if not self.is_available():
            raise ValueError(
                "ElevenLabs API Key is missing. Please set ELEVENLABS_API_KEY or TTS_API_KEY in your .env file."
            )

        active_voice_id = voice or self.voice_id or DEFAULT_ELEVENLABS_VOICE_ID
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{active_voice_id}"

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "speed": max(0.7, min(1.3, speed)),
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                error_detail = response.text
                raise RuntimeError(
                    f"ElevenLabs TTS API error ({response.status_code}): {error_detail}"
                )

            os.makedirs(os.path.dirname(os.path.abspath(output_file_path)), exist_ok=True)
            with open(output_file_path, "wb") as f:
                f.write(response.content)

        return output_file_path
