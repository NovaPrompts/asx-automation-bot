from datetime import datetime
from typing import List
from app.ingest.base import BaseSource
from app.models.base import NewsItem

class MockFinanceSource(BaseSource):
    async def fetch(self) -> List[NewsItem]:
        # Simulating data from a source like Rask or Motley Fool
        return [
            NewsItem(
                source_id="mock_rask",
                title="The Future of Lithium Mining in Australia",
                url="https://example.com/lithium",
                published_at=datetime.now(),
                content_summary="Lithium demand is expected to triple by 2030 as EV adoption accelerates. ASX miners like Pilbara Minerals are well positioned."
            ),
            NewsItem(
                source_id="mock_motley",
                title="3 Stocks to Watch this December",
                url="https://example.com/stocks",
                published_at=datetime.now(),
                content_summary="Focusing on defensive healthcare stocks and high-yield retail as market volatility increases."
            )
        ]
