from pydantic import BaseModel


class KeywordTrendPoint(BaseModel):
    keyword: str
    mentions: int


class TopicBreakdownPoint(BaseModel):
    topic: str
    documents: int


class HourlyComparisonPoint(BaseModel):
    timestamp: str
    label: str
    hate_index: float | None
    post_count: int
    kospi_value: float | None
    kospi_change_pct: float | None
    nasdaq_value: float | None
    nasdaq_change_pct: float | None


class HourlyComparisonResponse(BaseModel):
    timezone: str
    board_name: str | None
    points: list[HourlyComparisonPoint]


class CommunityOverviewResponse(BaseModel):
    board_name: str | None
    days: int
    post_count: int
    sentiment_score: float
    fear_greed_score: float
    hate_index: float
    uncertainty_score: float
    top_keywords: list[str]
