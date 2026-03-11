from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Article,
    CommunityPost,
    DailyMarketSentimentSnapshot,
    EconomicIndicator,
    IndicatorRelease,
    Sentiment,
)

KST = ZoneInfo("Asia/Seoul")


def get_latest_indicators(db: Session):
    indicators = db.execute(select(EconomicIndicator)).scalars().all()
    results = []
    for indicator in indicators:
        latest_release = db.execute(
            select(IndicatorRelease)
            .where(IndicatorRelease.indicator_id == indicator.id)
            .order_by(IndicatorRelease.release_date.desc())
            .limit(1)
        ).scalar_one_or_none()
        results.append((indicator, latest_release))
    return results


def get_indicator_history(db: Session, code: str):
    indicator = db.execute(select(EconomicIndicator).where(EconomicIndicator.code == code)).scalar_one_or_none()
    if indicator is None:
        return None, []
    releases = db.execute(
        select(IndicatorRelease)
        .where(IndicatorRelease.indicator_id == indicator.id)
        .order_by(IndicatorRelease.release_date.desc())
        .limit(60)
    ).scalars().all()
    return indicator, releases


def get_keyword_trends(db: Session, limit: int = 10):
    sentiments = db.execute(select(Sentiment)).scalars().all()
    counter = Counter(keyword for sentiment in sentiments for keyword in sentiment.keywords_json)
    return [{"keyword": keyword, "mentions": mentions} for keyword, mentions in counter.most_common(limit)]


def get_topic_breakdown(db: Session):
    sentiments = db.execute(select(Sentiment)).scalars().all()
    counter = Counter(topic for sentiment in sentiments for topic in sentiment.topics_json)
    return [{"topic": topic, "documents": count} for topic, count in counter.most_common()]


def get_daily_sentiment(db: Session, limit: int = 30):
    return db.execute(
        select(DailyMarketSentimentSnapshot)
        .order_by(DailyMarketSentimentSnapshot.snapshot_date.desc())
        .limit(limit)
    ).scalars().all()


def get_hourly_hate_index(
    db: Session,
    *,
    hours: int = 24,
    board_name: str | None = None,
    now: datetime | None = None,
):
    now_kst = (now or datetime.now(tz=KST)).astimezone(KST).replace(minute=0, second=0, microsecond=0)
    window_start_kst = now_kst - timedelta(hours=hours - 1)
    window_start_utc = window_start_kst.astimezone(UTC)

    stmt = (
        select(CommunityPost.created_at, Sentiment.hate_index)
        .join(
            Sentiment,
            (Sentiment.document_type == "community_post") & (Sentiment.document_id == CommunityPost.id),
        )
        .where(CommunityPost.created_at >= window_start_utc)
    )
    if board_name:
        stmt = stmt.where(CommunityPost.board_name == board_name)

    rows = db.execute(stmt).all()
    buckets: dict[datetime, list[float]] = defaultdict(list)

    for created_at, hate_index in rows:
        if created_at is None or hate_index is None:
            continue
        observed_at = created_at
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=UTC)
        bucket = observed_at.astimezone(KST).replace(minute=0, second=0, microsecond=0)
        buckets[bucket].append(float(hate_index))

    points = []
    for offset in range(hours):
        bucket = window_start_kst + timedelta(hours=offset)
        values = buckets.get(bucket, [])
        points.append(
            {
                "timestamp": bucket.isoformat(),
                "label": bucket.strftime("%m-%d %H:00"),
                "hate_index": round(sum(values) / len(values), 2) if values else None,
                "post_count": len(values),
            }
        )

    return points


def get_community_overview(
    db: Session,
    *,
    days: int = 7,
    board_name: str | None = None,
    now: datetime | None = None,
):
    now_kst = (now or datetime.now(tz=KST)).astimezone(KST)
    window_start_utc = (now_kst - timedelta(days=days)).astimezone(UTC)

    stmt = (
        select(
            Sentiment.sentiment_score,
            Sentiment.fear_greed_score,
            Sentiment.hate_index,
            Sentiment.uncertainty_score,
            Sentiment.keywords_json,
        )
        .join(
            CommunityPost,
            (Sentiment.document_type == "community_post") & (Sentiment.document_id == CommunityPost.id),
        )
        .where(CommunityPost.created_at >= window_start_utc)
    )
    if board_name:
        stmt = stmt.where(CommunityPost.board_name == board_name)

    rows = db.execute(stmt).all()
    if not rows:
        return {
            "board_name": board_name,
            "days": days,
            "post_count": 0,
            "sentiment_score": 0.0,
            "fear_greed_score": 50.0,
            "hate_index": 0.0,
            "uncertainty_score": 0.0,
            "top_keywords": [],
        }

    keyword_counter = Counter(
        keyword
        for _, _, _, _, keywords in rows
        for keyword in (keywords or [])
        if isinstance(keyword, str) and keyword.strip()
    )
    count = len(rows)
    return {
        "board_name": board_name,
        "days": days,
        "post_count": count,
        "sentiment_score": round(sum(float(row[0]) for row in rows) / count, 2),
        "fear_greed_score": round(sum(float(row[1]) for row in rows) / count, 2),
        "hate_index": round(sum(float(row[2]) for row in rows) / count, 2),
        "uncertainty_score": round(sum(float(row[3]) for row in rows) / count, 2),
        "top_keywords": [keyword for keyword, _ in keyword_counter.most_common(5)],
    }


def get_news(db: Session, page: int, page_size: int, keyword: str | None = None):
    stmt = select(Article)
    if keyword:
        stmt = stmt.where(func.lower(Article.title).contains(keyword.lower()))
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(
        stmt.order_by(Article.published_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return items, total


def get_community_posts(
    db: Session,
    page: int,
    page_size: int,
    board_name: str | None = None,
    board_id: str | None = None,
):
    stmt = select(CommunityPost)
    if board_name:
        stmt = stmt.where(CommunityPost.board_name == board_name)
    if board_id:
        stmt = stmt.where(CommunityPost.external_post_id.like(f"{board_id}:%"))
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(
        stmt.order_by(CommunityPost.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return items, total
