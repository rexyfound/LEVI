from abc import ABC, abstractmethod
from typing import Optional


class BaseTTSProvider(ABC):
    """
    Abstract base interface for all Text-to-Speech synthesis providers.
    """

    @abstractmethod
    async def synthesize(self, text: str, output_file_path: str, voice: Optional[str] = None) -> str:
        """
        Synthesize text into an audio file (typically MP3 or WAV).
        
        :param text: Clean text string to be spoken.
        :param output_file_path: Absolute destination path for the generated audio file.
        :param voice: Optional voice profile/identifier name override.
        :return: Path to the generated audio file.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check whether this provider has all required credentials, dependencies, and network access.
        """
        pass

    def cleanup(self) -> None:
        """Optional provider cleanup hook."""
        pass
