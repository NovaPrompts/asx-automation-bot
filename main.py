import asyncio
import argparse
import logging
import os
import sys
import shutil
from datetime import datetime
from typing import List

from app.ingest.rss import RSSSource
from app.ingest.youtube import YouTubeSource
from app.ingest.transcriber import DeepgramTranscriber
from app.memory.deduplicator import StoryMemory
from app.engine.script_writer import ScriptWriter
from app.audio.elevenlabs_client import ElevenLabsClient
from app.audio.mixer import AudioMixer
from app.distribution.publisher import PodcastPublisher
from app.models.base import NewsItem

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Orchestrator")

async def run_pipeline(mode: str):
    logger.info(f"🚀 Starting Podcast Automation Pipeline - Mode: {mode.upper()}")
    
    # --- Configuration ---
    # In a real app, these would come from config/env
    RSS_FEEDS = [
        "https://www.raskmedia.com.au/feed/",
        "https://www.fool.com.au/feed/"
    ]
    YOUTUBE_CHANNELS = [
        "https://www.youtube.com/@RaskAustralia" 
    ]
    TEMP_AUDIO_DIR = "temp_audio_segments"
    OUTPUT_FILENAME = f"episode_{datetime.now().strftime('%Y%m%d_%H%M')}.mp3"
    
    if not os.path.exists(TEMP_AUDIO_DIR):
        os.makedirs(TEMP_AUDIO_DIR)

    try:
        # --- Step 1: Ingest ---
        logger.info("--- Step 1: Ingestion ---")
        transcriber = DeepgramTranscriber()
        rss_source = RSSSource(RSS_FEEDS)
        yt_source = YouTubeSource(YOUTUBE_CHANNELS, transcriber)

        # Run fetchers concurrently
        results = await asyncio.gather(
            rss_source.fetch(),
            yt_source.fetch()
        )
        
        # Flatten results
        all_news: List[NewsItem] = [item for sublist in results for item in sublist]
        logger.info(f"📥 Ingested {len(all_news)} total items.")

        if not all_news:
            logger.warning("No news items found. Aborting.")
            return

        # --- Step 2: Deduplicate ---
        logger.info("--- Step 2: Deduplication ---")
        memory = StoryMemory()
        unique_news: List[NewsItem] = []
        
        for item in all_news:
            is_dup = await memory.is_duplicate(item)
            if not is_dup:
                unique_news.append(item)
                await memory.add_story(item) # Add to memory so it's not repeated tomorrow
            else:
                logger.info(f"Skipping duplicate: {item.title}")

        logger.info(f"📉 Reduced to {len(unique_news)} unique stories.")
        
        if not unique_news:
            logger.warning("No unique stories to report. Aborting.")
            return

        # --- Step 3: Script ---
        logger.info("--- Step 3: Script Generation ---")
        writer = ScriptWriter()
        segments = await writer.generate_script(unique_news, mode=mode)
        
        logger.info(f"📝 Generated {len(segments)} script segments.")
        for i, seg in enumerate(segments):
            logger.info(f"  [{i+1}] {seg.segment_type}: {seg.text[:50]}...")

        # --- Step 4: Audio Synthesis ---
        logger.info("--- Step 4: Audio Synthesis ---")
        tts_client = ElevenLabsClient()
        audio_paths = []
        
        # Hardcoded Voice ID (Replace with your preferred voice ID)
        # Example: "JBFqnCBsd6RMkjVDRZzb" (George)
        VOICE_ID = "JBFqnCBsd6RMkjVDRZzb" 

        for i, segment in enumerate(segments):
            logger.info(f"Synthesizing segment {i+1}/{len(segments)}...")
            audio_bytes = await tts_client.generate_audio(segment.text, VOICE_ID)
            
            filename = f"{TEMP_AUDIO_DIR}/seg_{i}_{segment.segment_type}.mp3"
            with open(filename, "wb") as f:
                f.write(audio_bytes)
            
            audio_paths.append(filename)
            segment.audio_path = filename # Update model

        # --- Step 5: Mixing ---
        logger.info("--- Step 5: Audio Mixing ---")
        mixer = AudioMixer()
        
        # Add intro/outro assets if they exist
        final_segments = []
        if os.path.exists("assets/intro.mp3"):
            final_segments.append("assets/intro.mp3")
        
        final_segments.extend(audio_paths)
        
        if os.path.exists("assets/outro.mp3"):
            final_segments.append("assets/outro.mp3")

        final_mp3_path = mixer.mix_episode(final_segments, OUTPUT_FILENAME)

        # --- Step 6: Distribution ---
        logger.info("--- Step 6: Distribution ---")
        publisher = PodcastPublisher()
        
        # Calculate approximate duration (optional, or use ffmpeg to get it)
        # For MVP we pass 0 or a dummy value if we don't probe the file
        feed_url = publisher.update_feed(
            episode_title=f"Market Update - {mode.title()} Edition",
            episode_summary=f"Automated market update covering {len(unique_news)} stories.",
            mp3_path=final_mp3_path,
            duration_sec=0 
        )
        
        logger.info(f"🎉 SUCCESS! Episode published at: {feed_url}")

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
    finally:
        # Cleanup temp audio
        if os.path.exists(TEMP_AUDIO_DIR):
            shutil.rmtree(TEMP_AUDIO_DIR)
            logger.info("Cleaned up temp files.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Voice AI Agent Pipeline")
    parser.add_argument("--mode", choices=["morning", "afternoon"], default="morning", help="Pipeline mode")
    args = parser.parse_args()

    asyncio.run(run_pipeline(args.mode))
