from datetime import date, datetime

from pydantic import BaseModel


class PoliticalIndicatorValueRead(BaseModel):
    indicator_name: str
    code: str
    date: date
    value: float
    label: str | None
    source: str | None
    unit: str | None


class PoliticianRead(BaseModel):
    name: str
    party: str | None
    position: str | None
    ideology: str | None
    country: str
    start_term: date | None
    end_term: date | None
    aliases: list[str]


class PoliticalPostRead(BaseModel):
    id: int
    community_name: str
    board_name: str | None
    title: str
    body: str
    created_at: datetime
    view_count: int | None
    upvotes: int | None
    comment_count: int | None
    original_url: str

    model_config = {"from_attributes": True}


class PoliticalCommunitySourceRead(BaseModel):
    name: str
    description: str | None
    leaning: str | None
    link: str
    status: str


class PoliticalSentimentRead(BaseModel):
    political_sentiment_score: float
    political_polarization_index: float
    election_heat_index: float
    keywords: list[str]
    labels: list[str]


class PoliticsDashboardResponse(BaseModel):
    indicator_cards: list[PoliticalIndicatorValueRead]
    approval_trend: list[PoliticalIndicatorValueRead]
    party_support_comparison: list[PoliticalIndicatorValueRead]
    politician_mentions_top10: list[dict]
    keyword_trends: list[dict]
    political_sentiment_index: list[dict]
    polarization_index: list[dict]
    election_heat_index: list[dict]
    community_posts: list[PoliticalPostRead]
    reference_communities: list[PoliticalCommunitySourceRead]
