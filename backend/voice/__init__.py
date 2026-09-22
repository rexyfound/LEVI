from typing import Optional
import atexit
from voice.states import VoiceState
from voice.voice_manager import VoiceManager

# Global singleton voice manager instance
voice_manager = VoiceManager()
atexit.register(voice_manager.cleanup)


def speak(text: str, *, spoken_text: Optional[str] = None, request_id: Optional[str] = None, voice: Optional[str] = None) -> Optional[str]:
    """
    Public non-blocking API to speak agent responses through the system speakers.
    """
    return voice_manager.speak(text, spoken_text=spoken_text, request_id=request_id, voice=voice)


def stop_speaking() -> None:
    """
    Public safe API to stop speaking immediately.
    """
    voice_manager.stop_speaking()


def is_speaking() -> bool:
    """
    Check if the voice engine is currently preparing or speaking.
    """
    return voice_manager.is_speaking()


def get_voice_state() -> VoiceState:
    """
    Get current voice engine state.
    """
    return voice_manager.get_state()


__all__ = [
    "VoiceState",
    "VoiceManager",
    "voice_manager",
    "speak",
    "stop_speaking",
    "is_speaking",
    "get_voice_state",
]
