from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class NewsItem(BaseModel):
    source_id: str = Field(..., description="Unique identifier for the source, e.g., 'youtube_rask'")
    title: str
    url: str
    published_at: datetime
    content_summary: str = Field(..., description="The raw text or transcript")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding for the content")

class SegmentType(str, Enum):
    INTRO = "intro"
    MARKET_WRAP = "market_wrap"
    STOCK_DEEPDIVE = "stock_deepdive"
    OUTRO = "outro"

class ScriptSegment(BaseModel):
    segment_type: SegmentType
    text: str
    audio_path: Optional[str] = None
