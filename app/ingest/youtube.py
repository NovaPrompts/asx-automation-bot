import os
import glob
import logging
import asyncio
from datetime import datetime
from typing import List
import yt_dlp
from app.ingest.base import BaseSource
from app.ingest.transcriber import DeepgramTranscriber
from app.models.base import NewsItem

logger = logging.getLogger(__name__)

class YouTubeSource(BaseSource):
    def __init__(self, channel_urls: List[str], transcriber: DeepgramTranscriber):
        self.channel_urls = channel_urls
        self.transcriber = transcriber
        self.download_path = "./downloads"
        
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    async def fetch(self) -> List[NewsItem]:
        items: List[NewsItem] = []

        for url in self.channel_urls:
            try:
                # 1. Download Audio
                audio_file, info = await self._download_latest_audio(url)
                if not audio_file:
                    continue

                # 2. Transcribe
                logger.info(f"Transcribing {audio_file}...")
                transcript = await self.transcriber.transcribe(audio_file)

                # 3. Create NewsItem
                item = NewsItem(
                    source_id=f"youtube_{info['channel_id']}",
                    title=info.get('title', 'Unknown Title'),
                    url=info.get('webpage_url', url),
                    published_at=datetime.now(), # yt-dlp upload_date is string, using now for simplicity
                    content_summary=transcript
                )
                items.append(item)

                # 4. Cleanup
                self._cleanup(audio_file)

            except Exception as e:
                logger.error(f"Error processing channel {url}: {e}")
                
        return items

    async def _download_latest_audio(self, channel_url: str):
        """
        Downloads the latest video audio from the channel.
        Returns tuple (filepath, info_dict).
        """
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.download_path}/%(id)s.%(ext)s',
            'noplaylist': True,
            'playlist_items': '1', # Only the latest video
            'quiet': True,
            'overwrites': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        try:
            # yt_dlp is synchronous
            def run_yt_dlp():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Extract info first
                    info = ydl.extract_info(channel_url, download=True)
                    # Use 'entries' if it's a channel/playlist, otherwise info itself
                    if 'entries' in info:
                        video_info = info['entries'][0]
                    else:
                        video_info = info
                    
                    filename = ydl.prepare_filename(video_info)
                    # filename ext might differ after postprocessing (mp3)
                    final_filename = os.path.splitext(filename)[0] + ".mp3"
                    return final_filename, video_info

            return await asyncio.to_thread(run_yt_dlp)

        except Exception as e:
            logger.error(f"yt-dlp failed for {channel_url}: {e}")
            return None, None

    def _cleanup(self, file_path: str):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete {file_path}: {e}")
