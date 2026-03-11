from datetime import datetime

from pydantic import BaseModel, Field


class CommunityPostAnalysisRequest(BaseModel):
    title: str = Field(default="", max_length=500)
    body: str = Field(default="", max_length=20000)


class CommunityPostAnalysisRead(BaseModel):
    sentiment_score: float
    fear_greed_score: float
    hate_score: float
    hate_index: float
    uncertainty_score: float
    market_bias: str
    keywords: list[str]
    tags: list[str]
    topics: list[str]
    entities: list[str]


class MarketSummaryRequest(BaseModel):
    sentiment_score: float = 0
    fear_greed_score: float = 50
    hate_index: float = 0
    uncertainty_score: float = 0
    top_keywords: list[str] = Field(default_factory=list)
    kospi_value: float | None = None
    kospi_change_percent: float | None = None
    kospi_state: str | None = None
    nasdaq_value: float | None = None
    nasdaq_change_percent: float | None = None
    nasdaq_trade_date: str | None = None
    post_count: int = 0


class MarketSummaryRead(BaseModel):
    status_label: str
    summary_lines: list[str]
    analysis_note: str
    source: str


class CommunityPostRead(BaseModel):
    id: int
    board_name: str
    title: str
    body: str
    created_at: datetime
    view_count: int | None
    upvotes: int | None
    downvotes: int | None
    comment_count: int | None
    original_url: str
    analysis: CommunityPostAnalysisRead

    model_config = {"from_attributes": True}
