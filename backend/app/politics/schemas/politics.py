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


class PoliticsSummaryRead(BaseModel):
    reference_date: date | None
    post_count: int
    today_post_count: int
    community_count: int
    top_issue: str | None
    top_politician: str | None


class PoliticsPolarizationPointRead(BaseModel):
    date: date
    support_rate: float
    oppose_rate: float
    neutral_rate: float
    mentions: int


class PoliticsEmotionRead(BaseModel):
    date: date | None
    anger_pct: float
    positive_pct: float
    neutral_pct: float
    mentions: int


class PoliticsIssueSentimentRead(BaseModel):
    issue: str
    mentions: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float


class PoliticsIssueSourceReactionRead(BaseModel):
    source_code: str
    source_name: str
    mentions: int
    support_pct: float
    oppose_pct: float
    neutral_pct: float


class PoliticsIssueComparisonRead(BaseModel):
    issue: str
    sources: list[PoliticsIssueSourceReactionRead]


class PoliticsPoliticianRankingRead(BaseModel):
    name: str
    mentions: int


class PoliticsTimelineEventRead(BaseModel):
    date: date
    issue: str
    headline: str
    mentions: int


class PoliticsHotPostRead(BaseModel):
    id: int
    source_code: str
    source_name: str
    board_name: str
    title: str
    body: str
    created_at: datetime
    view_count: int | None
    upvotes: int | None
    comment_count: int | None
    original_url: str
    issue_labels: list[str]
    stance: str
    emotion: str
    influence_score: float


class PoliticsDashboardResponse(BaseModel):
    reference_date: date | None
    summary: PoliticsSummaryRead
    polarization_trend: list[PoliticsPolarizationPointRead]
    today_emotion: PoliticsEmotionRead
    issue_sentiments: list[PoliticsIssueSentimentRead]
    issue_source_comparisons: list[PoliticsIssueComparisonRead]
    politician_rankings: list[PoliticsPoliticianRankingRead]
    issue_timeline: list[PoliticsTimelineEventRead]
    hot_posts: list[PoliticsHotPostRead]
