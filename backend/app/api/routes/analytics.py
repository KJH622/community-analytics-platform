from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.reference import DocumentTag
from app.models.sentiment import DailyMarketSentimentSnapshot
from app.schemas.analytics import DailySnapshotRead, KeywordTrendPoint, TopicBreakdownPoint


router = APIRouter()


@router.get("/daily-sentiment", response_model=list[DailySnapshotRead])
def daily_sentiment(
    limit: int = Query(default=30, le=180),
    source_kind: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[DailySnapshotRead]:
    query = select(DailyMarketSentimentSnapshot)
    if source_kind:
        query = query.where(DailyMarketSentimentSnapshot.source_kind == source_kind)
    rows = db.scalars(
        query.order_by(DailyMarketSentimentSnapshot.snapshot_date.desc()).limit(limit)
    ).all()
    return [DailySnapshotRead.model_validate(row) for row in rows]


@router.get("/keyword-trends", response_model=list[KeywordTrendPoint])
def keyword_trends(
    date_from: date | None = None,
    date_to: date | None = None,
    keyword: str | None = None,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
) -> list[KeywordTrendPoint]:
    query = (
        select(
            func.date(DocumentTag.created_at).label("date"),
            DocumentTag.tag_value.label("keyword"),
            func.count(DocumentTag.id).label("count"),
        )
        .where(DocumentTag.tag_type == "keyword")
        .group_by(func.date(DocumentTag.created_at), DocumentTag.tag_value)
        .order_by(func.date(DocumentTag.created_at).desc(), func.count(DocumentTag.id).desc())
    )
    if date_from:
        query = query.where(func.date(DocumentTag.created_at) >= date_from)
    if date_to:
        query = query.where(func.date(DocumentTag.created_at) <= date_to)
    if keyword:
        query = query.where(DocumentTag.tag_value == keyword)

    rows = db.execute(query.limit(limit)).all()
    return [
        KeywordTrendPoint(date=row.date, keyword=row.keyword, count=row.count)
        for row in rows
    ]


@router.get("/topic-breakdown", response_model=list[TopicBreakdownPoint])
def topic_breakdown(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
) -> list[TopicBreakdownPoint]:
    query = (
        select(
            DocumentTag.tag_value.label("topic"),
            func.count(DocumentTag.id).label("count"),
        )
        .where(DocumentTag.tag_type == "topic")
        .group_by(DocumentTag.tag_value)
        .order_by(func.count(DocumentTag.id).desc())
    )
    if date_from:
        query = query.where(func.date(DocumentTag.created_at) >= date_from)
    if date_to:
        query = query.where(func.date(DocumentTag.created_at) <= date_to)
    rows = db.execute(query).all()
    return [TopicBreakdownPoint(topic=row.topic, count=row.count) for row in rows]
