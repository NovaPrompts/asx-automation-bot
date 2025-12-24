import httpx
import logging
from app.audio.base import BaseAudioProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class ElevenLabsClient(BaseAudioProvider):
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
    
    async def generate_audio(self, text: str, voice_id: str) -> bytes:
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                
                if response.status_code == 200:
                    return response.content
                
                if response.status_code == 429:
                    logger.error("ElevenLabs API rate limit exceeded.")
                    raise Exception("Rate limit exceeded")
                
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                response.raise_for_status()
                
            except httpx.RequestError as e:
                logger.error(f"Network error communicating with ElevenLabs: {e}")
                raise e
            except Exception as e:
                logger.error(f"Unexpected error in audio generation: {e}")
                raise e
        return b""
