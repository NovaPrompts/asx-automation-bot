import asyncio
from app.ingest.mock_source import MockFinanceSource
from app.memory.vector_store import VectorStore

async def main():
    print("🚀 Starting mock ingestion...")
    
    # 1. Fetch data from source
    source = MockFinanceSource()
    news_items = await source.fetch()
    print(f"📥 Fetched {len(news_items)} items.")

    # 2. Store in Vector DB
    print("💾 Storing in ChromaDB...")
    store = VectorStore()
    store.add_news_items(news_items)
    print("✅ Storage complete.")

    # 3. Verify with a search
    print("🔍 Testing search...")
    results = store.search("lithium mining outlook")
    print(f"Result: {results['documents'][0][0]}")

if __name__ == "__main__":
    asyncio.run(main())
