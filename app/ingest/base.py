from abc import ABC, abstractmethod
from typing import List
from app.models.base import NewsItem

class BaseSource(ABC):
    @abstractmethod
    async def fetch(self) -> List[NewsItem]:
        """
        Fetches news items from the source.
        Must return a list of NewsItem objects.
        """
        pass