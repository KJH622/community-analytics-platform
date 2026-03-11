from datetime import date

from pydantic import BaseModel

from app.schemas.common import ORMModel


class SentimentRead(ORMModel):
    id: int
    document_type: str
    document_id: int
    sentiment_score: float
    fear_greed_score: float
    hate_index: float
    uncertainty_score: float
    market_bias: str
    labels: list[str] | None
    keywords: list[str] | None


class DailySnapshotRead(ORMModel):
    id: int
    snapshot_key: str
    snapshot_date: date
    source_kind: str | None
    country: str | None
    topic_code: str | None
    sentiment_avg: float
    fear_greed_avg: float
    hate_index_avg: float
    uncertainty_avg: float
    bullish_ratio: float
    bearish_ratio: float
    neutral_ratio: float
    article_count: int
    community_post_count: int
    top_keywords: list[str] | None


class KeywordTrendPoint(BaseModel):
    date: date
    keyword: str
    count: int


class TopicBreakdownPoint(BaseModel):
    topic: str
    count: int
