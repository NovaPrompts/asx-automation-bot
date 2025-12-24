import os
import logging
from deepgram import DeepgramClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class DeepgramTranscriber:
    def __init__(self):
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)

    async def transcribe(self, audio_path: str) -> str:
        """
        Transcribes audio file at audio_path using Deepgram Nova-2 model.
        Returns the raw transcript string.
        """
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            raise FileNotFoundError(f"File not found: {audio_path}")

        try:
            with open(audio_path, "rb") as file:
                buffer_data = file.read()

            payload = {
                "buffer": buffer_data,
            }

            # Usage of dictionary for options is widely supported and safer across versions
            options = {
                "model": "nova-2",
                "smart_format": True,
                "punctuate": True
            }

            # Deepgram SDK v3+ usage
            response = self.client.listen.rest.v("1").transcribe_file(payload, options)
            
            # Extract transcript
            transcript = response.results.channels[0].alternatives[0].transcript
            return transcript

        except Exception as e:
            logger.error(f"Deepgram transcription failed: {e}")
            raise e