from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.analytics import KeywordTrendPoint, TopicBreakdownPoint
from app.schemas.common import DailySnapshotResponse
from app.services.query import get_daily_sentiment, get_keyword_trends, get_topic_breakdown

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/daily-sentiment", response_model=list[DailySnapshotResponse])
def daily_sentiment(db: Session = Depends(get_db), limit: int = Query(default=30, ge=1, le=365)):
    snapshots = get_daily_sentiment(db, limit=limit)
    return [
        DailySnapshotResponse(
            snapshot_date=item.snapshot_date,
            country=item.country,
            sentiment_score=item.sentiment_score,
            fear_greed_score=item.fear_greed_score,
            hate_index=item.hate_index,
            uncertainty_score=item.uncertainty_score,
            bullish_ratio=item.bullish_ratio,
            bearish_ratio=item.bearish_ratio,
            neutral_ratio=item.neutral_ratio,
            top_keywords=item.top_keywords_json,
        )
        for item in snapshots
    ]


@router.get("/keyword-trends", response_model=list[KeywordTrendPoint])
def keyword_trends(db: Session = Depends(get_db), limit: int = Query(default=10, ge=1, le=50)):
    return [KeywordTrendPoint(**item) for item in get_keyword_trends(db, limit=limit)]


@router.get("/topic-breakdown", response_model=list[TopicBreakdownPoint])
def topic_breakdown(db: Session = Depends(get_db)):
    return [TopicBreakdownPoint(**item) for item in get_topic_breakdown(db)]
