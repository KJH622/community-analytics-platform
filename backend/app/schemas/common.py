from datetime import date, datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    timestamp: datetime


class DailySnapshotResponse(BaseModel):
    snapshot_date: date
    country: str
    sentiment_score: float
    fear_greed_score: float
    hate_index: float
    uncertainty_score: float
    bullish_ratio: float
    bearish_ratio: float
    neutral_ratio: float
    top_keywords: list[str]
