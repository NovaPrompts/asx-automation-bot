from abc import ABC, abstractmethod

class BaseAudioProvider(ABC):
    @abstractmethod
    async def generate_audio(self, text: str, voice_id: str) -> bytes:
        """
        Converts text to audio bytes using the specified voice_id.
        """
        pass
