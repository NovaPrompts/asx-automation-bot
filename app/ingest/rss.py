import feedparser
import asyncio
from datetime import datetime
from typing import List
from app.ingest.base import BaseSource
from app.models.base import NewsItem
import logging

logger = logging.getLogger(__name__)

class RSSSource(BaseSource):
    def __init__(self, feed_urls: List[str]):
        self.feed_urls = feed_urls

    async def fetch(self) -> List[NewsItem]:
        items: List[NewsItem] = []
        
        # feedparser is synchronous, so we run it in a thread if strictly async needed,
        # but for simple fetching, straightforward iteration is often acceptable in scripts.
        # Ideally, use asyncio.to_thread for blocking IO.
        for url in self.feed_urls:
            try:
                # Run the blocking feedparser in a thread
                feed = await asyncio.to_thread(feedparser.parse, url)
                
                if feed.bozo:
                    logger.warning(f"Error parsing feed {url}: {feed.bozo_exception}")
                    continue

                for entry in feed.entries:
                    # Extract date or default to now
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    else:
                        published_at = datetime.now()

                    # Extract summary or fall back to title
                    summary = getattr(entry, 'summary', '')
                    if not summary:
                        summary = entry.title

                    item = NewsItem(
                        source_id=f"rss_{url}",
                        title=entry.title,
                        url=entry.link,
                        published_at=published_at,
                        content_summary=summary
                    )
                    items.append(item)
                    
            except Exception as e:
                logger.error(f"Failed to fetch RSS feed {url}: {e}")

        return items
