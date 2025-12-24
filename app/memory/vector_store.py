import chromadb
from chromadb.utils import embedding_functions
from app.core.config import settings
from app.models.base import NewsItem
from typing import List

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.OPENAI_API_KEY,
            model_name="text-embedding-3-small"
        )
        self.collection = self.client.get_or_create_collection(
            name="financial_news",
            embedding_function=self.openai_ef
        )

    def add_news_items(self, items: List[NewsItem]):
        ids = [f"{item.source_id}_{item.published_at.timestamp()}" for item in items]
        documents = [item.content_summary for item in items]
        metadatas = [
            {
                "source_id": item.source_id,
                "title": item.title,
                "url": item.url,
                "published_at": item.published_at.isoformat()
            }
            for item in items
        ]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search(self, query: str, n_results: int = 3):
        return self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
