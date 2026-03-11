from __future__ import annotations

from collections import Counter

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
