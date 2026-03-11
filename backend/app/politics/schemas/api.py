from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PoliticalORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PoliticianRead(PoliticalORMModel):
    id: int
    name: str
    party: str | None
    position: str | None
    ideology: str | None
    country: str
    start_term: date | None
    end_term: date | None
    profile_url: str | None


class PoliticalIndicatorValueRead(PoliticalORMModel):
    id: int
    date: date
    value: float
    label: str | None
    source: str | None
    unit: str | None


class PoliticalIndicatorRead(PoliticalORMModel):
    id: int
    code: str
    indicator_name: str
    country: str
    unit: str | None
    source: str | None
    description: str | None
    values: list[PoliticalIndicatorValueRead] | None = None


class PoliticalPostRead(PoliticalORMModel):
    id: int
    community_name: str
    board_name: str
    title: str
    body: str | None
    published_at: datetime | None
    view_count: int | None
    upvotes: int | None
    comment_count: int | None
    url: str
    political_sentiment_score: float | None = None
    political_polarization_index: float | None = None
    analytics_excluded: bool = False
    exclusion_reasons: list[str] | None = None
    influence_score: float | None = None


class PoliticalSentimentRead(PoliticalORMModel):
    id: int
    post_id: int
    political_sentiment_score: float
    support_score: float
    opposition_score: float
    anger_score: float
    sarcasm_score: float
    apathy_score: float
    enthusiasm_score: float
    political_polarization_index: float
    election_heat_index: float
    labels: list[str] | None
    keywords: list[str] | None


class PoliticalSnapshotRead(PoliticalORMModel):
    id: int
    snapshot_date: date
    political_sentiment_avg: float
    political_polarization_index: float
    election_heat_index: float
    top_keywords: list[str] | None
    top_politicians: list[str] | None
    post_count: int


class KeywordPoint(BaseModel):
    keyword: str
    count: int


class PolarizationPoint(BaseModel):
    date: date
    value: float
    election_heat: float | None = None


class PoliticsDashboardResponse(BaseModel):
    sentiment_snapshot: PoliticalSnapshotRead | None
    indicators: list[PoliticalIndicatorRead]
    top_politicians: list[KeywordPoint]
    keyword_trends: list[KeywordPoint]
    posts: list[PoliticalPostRead]
    community_references: list[dict[str, str | None]]
