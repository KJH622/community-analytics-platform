from datetime import datetime

from pydantic import BaseModel


class CommunityPostAnalysisRead(BaseModel):
    sentiment_score: float
    fear_greed_score: float
    hate_index: float
    uncertainty_score: float
    market_bias: str
    keywords: list[str]
    topics: list[str]
    entities: list[str]


class CommunityPostRead(BaseModel):
    id: int
    source_code: str | None = None
    source_name: str | None = None
    board_code: str | None = None
    board_name: str
    topic_category: str | None = None
    title: str
    body: str
    created_at: datetime
    author_hash: str | None = None
    view_count: int | None
    upvotes: int | None
    downvotes: int | None
    comment_count: int | None
    original_url: str
    analysis: CommunityPostAnalysisRead

    model_config = {"from_attributes": True}
