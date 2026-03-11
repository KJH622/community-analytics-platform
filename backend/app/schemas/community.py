from datetime import datetime

from app.schemas.common import ORMModel


class CommunityPostRead(ORMModel):
    id: int
    source_id: int
    board_name: str
    external_id: str
    title: str
    body: str | None
    published_at: datetime | None
    author_hash: str | None
    view_count: int | None
    upvotes: int | None
    downvotes: int | None
    comment_count: int | None
    url: str
    sentiment_score: float | None = None
    fear_greed_score: float | None = None
    hate_index: float | None = None
    uncertainty_score: float | None = None
    market_bias: str | None = None
    analytics_excluded: bool = False
    exclusion_reasons: list[str] | None = None
    influence_score: float | None = None


class CommunityPostListResponse(ORMModel):
    items: list[CommunityPostRead]
    total: int
