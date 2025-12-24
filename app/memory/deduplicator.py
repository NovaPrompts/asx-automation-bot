import hashlib
import logging
import chromadb
from typing import List
from datetime import datetime
from openai import AsyncOpenAI
from app.core.config import settings
from app.models.base import NewsItem

logger = logging.getLogger(__name__)

class StoryMemory:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        self.collection = self.chroma_client.get_or_create_collection(
            name="news_stories",
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity space
        )
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def _get_embedding(self, text: str) -> List[float]:
        """
        Generates embedding for the given text using OpenAI's text-embedding-3-small.
        """
        try:
            response = await self.openai_client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise e

    async def is_duplicate(self, news_item: NewsItem, threshold: float = 0.85) -> bool:
        """
        Checks if the news item is semantically similar to an existing story.
        Returns True if a duplicate is found (similarity > threshold).
        """
        # 1. Generate embedding for the new item
        embedding = await self._get_embedding(news_item.content_summary)
        
        # Store embedding in the item for later use (avoid re-generating)
        news_item.embedding = embedding

        # 2. Query for nearest neighbor
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=1
        )

        if not results['documents'][0]:
            return False

        # ChromaDB returns 'distances'. For cosine space, distance = 1 - similarity.
        # So similarity = 1 - distance.
        distance = results['distances'][0][0]
        similarity = 1 - distance

        if similarity > threshold:
            existing_title = results['metadatas'][0][0].get('title', 'Unknown')
            logger.info(
                f"Duplicate detected: '{news_item.title}' is {similarity:.2%} similar "
                f"to existing story '{existing_title}'."
            )
            return True
        
        return False

    async def add_story(self, news_item: NewsItem):
        """
        Adds a non-duplicate story to the memory.
        """
        # Ensure we have an embedding
        if not news_item.embedding:
            news_item.embedding = await self._get_embedding(news_item.content_summary)

        # Create a deterministic ID
        story_id = hashlib.md5(news_item.url.encode('utf-8')).hexdigest()

        self.collection.add(
            ids=[story_id],
            embeddings=[news_item.embedding],
            documents=[news_item.content_summary],
            metadatas=[{
                "source_id": news_item.source_id,
                "title": news_item.title,
                "url": news_item.url,
                "published_at": news_item.published_at.isoformat()
            }]
        )
        logger.info(f"Added new story to memory: {news_item.title}")
