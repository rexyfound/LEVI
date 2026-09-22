import os
import asyncio
from typing import Optional
from voice.base_provider import BaseTTSProvider


class FakeTTSProvider(BaseTTSProvider):
    """
    Mock TTS Provider for automated unit and integration tests.
    Does not require network access, API keys, or speakers.
    """

    def __init__(self, should_fail: bool = False, delay_seconds: float = 0.05):
        self.should_fail = should_fail
        self.delay_seconds = delay_seconds
        self.synthesize_calls = []

    def is_available(self) -> bool:
        return True

    async def synthesize(self, text: str, output_file_path: str, voice: Optional[str] = None) -> str:
        self.synthesize_calls.append({"text": text, "output_path": output_file_path, "voice": voice})

        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.should_fail:
            raise RuntimeError("FakeTTSProvider simulated synthesis error.")

        # Create a dummy file with minimal dummy audio header
        os.makedirs(os.path.dirname(os.path.abspath(output_file_path)), exist_ok=True)
        with open(output_file_path, "wb") as f:
            f.write(b"DUMMY_AUDIO_DATA_FOR_TESTING")

        return output_file_path
