import asyncio
from typing import List
from datetime import datetime
from app.models.base import NewsItem, ScriptSegment
from app.ingest.transcriber import DeepgramTranscriber
from app.ingest.rss import RSSSource
from app.ingest.youtube import YouTubeSource
from app.memory.deduplicator import StoryMemory
from app.engine.script_writer import ScriptWriter
from app.audio.elevenlabs_client import ElevenLabsClient
from app.audio.mixer import AudioMixer
from app.distribution.publisher import PodcastPublisher
from main import run_pipeline

# --- THE MOCKS ---

async def mock_transcribe(self, audio_path: str) -> str:
    print(f"   [MOCK] Transcribing audio file: {audio_path}")
    return "This is a dummy transcript about the ASX market. BHP is up 2%."

async def mock_fetch_rss(self) -> List[NewsItem]:
    print("   [MOCK] Fetching RSS feed...")
    return [NewsItem(
        source_id="mock_rss", 
        title="Mock Market News", 
        url="http://google.com", 
        published_at=datetime(2025, 1, 1, 12, 0, 0), 
        content_summary="The market is doing great today."
    )]

async def mock_fetch_youtube(self) -> List[NewsItem]:
    print("   [MOCK] Processing YouTube video...")
    return [NewsItem(
        source_id="mock_yt", 
        title="Mock YouTube Video", 
        url="http://youtube.com", 
        published_at=datetime(2025, 1, 1, 12, 0, 0), 
        content_summary="Video transcript regarding interest rates."
    )]

async def mock_is_duplicate(self, news_item, threshold=0.85) -> bool:
    print(f"   [MOCK] Checking memory for: {news_item.title}")
    return False 

async def mock_add_story(self, news_item):
    print(f"   [MOCK] (Saved Money) Skipped adding story embedding to DB: {news_item.title}")

async def mock_generate_script(self, news_items, mode) -> List[ScriptSegment]:
    print("   [MOCK] Generating script with GPT-4o...")
    return [
        ScriptSegment(segment_type="intro", text="Welcome to the test podcast."),
        ScriptSegment(segment_type="market_wrap", text="The market is up today."),
        ScriptSegment(segment_type="outro", text="Thanks for listening.")
    ]

async def mock_generate_audio(self, text: str, voice_id: str) -> bytes:
    print(f"   [MOCK] Generating audio for: '{text[:20]}...'")
    return b'\xFF\xF3\x44\xC4' * 100 

def mock_update_feed(self, episode_title, episode_summary, mp3_path, duration_sec):
    print(f"   [MOCK] Uploading to Cloudflare: {episode_title}")
    return "https://r2.cloudflare.com/test-feed.xml"

def mock_transcriber_init(self):
    print("   [MOCK] Initializing DeepgramTranscriber (Skipping real client)")

def mock_mix_episode(self, segments, output_path):
    print(f"   [MOCK] Mixing {len(segments)} segments into {output_path}")
    # Create a dummy file so the next step (upload) finds it
    with open(output_path, "wb") as f:
        f.write(b"mock_mp3_content")
    return output_path

# --- APPLY THE PATCHES ---
DeepgramTranscriber.__init__ = mock_transcriber_init
DeepgramTranscriber.transcribe = mock_transcribe
AudioMixer.mix_episode = mock_mix_episode
RSSSource.fetch = mock_fetch_rss
YouTubeSource.fetch = mock_fetch_youtube
StoryMemory.is_duplicate = mock_is_duplicate
StoryMemory.add_story = mock_add_story # Added to prevent OpenAI call
ScriptWriter.generate_script = mock_generate_script
ElevenLabsClient.generate_audio = mock_generate_audio
PodcastPublisher.update_feed = mock_update_feed

# --- RUN THE PIPELINE ---
if __name__ == "__main__":
    print("--- STARTING DRY RUN (NO API COST) ---")
    asyncio.run(run_pipeline(mode="morning"))
    print("--- DRY RUN COMPLETE ---")
