import os
import asyncio
import logging
from typing import Optional
from voice.base_provider import BaseTTSProvider

logger = logging.getLogger("LEVI.EdgeTTSProvider")

DEFAULT_EDGE_VOICE = "en-US-ChristopherNeural"  # Natural, calm, intelligent, confident, professional


class EdgeTTSProvider(BaseTTSProvider):
    """
    Microsoft Edge Neural TTS provider.
    Zero cost, high-fidelity neural speech synthesis without API keys.
    """

    def __init__(self, default_voice: Optional[str] = None):
        self.default_voice = default_voice or os.getenv("TTS_VOICE", DEFAULT_EDGE_VOICE)

    def is_available(self) -> bool:
        try:
            import edge_tts
            return True
        except ImportError:
            return False

    async def synthesize(self, text: str, output_file_path: str, voice: Optional[str] = None) -> str:
        import edge_tts

        selected_voice = voice or self.default_voice or DEFAULT_EDGE_VOICE
        rate = os.getenv("TTS_RATE", "+0%")
        pitch = os.getenv("TTS_PITCH", "+0Hz")
        volume = os.getenv("TTS_VOLUME", "+0%")

        communicate = edge_tts.Communicate(
            text=text,
            voice=selected_voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
        )

        await communicate.save(output_file_path)
        return output_file_path
