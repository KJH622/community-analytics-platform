from __future__ import annotations

from collections import Counter
from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import Article, CommunityPost, DailyMarketSentimentSnapshot, Sentiment


def calculate_daily_snapshot(
    db: Session, snapshot_date: date, country: str = "GLOBAL"
) -> DailyMarketSentimentSnapshot:
    existing = db.execute(
        select(DailyMarketSentimentSnapshot).where(
            DailyMarketSentimentSnapshot.snapshot_date == snapshot_date,
            DailyMarketSentimentSnapshot.country == country,
        )
    ).scalar_one_or_none()

    article_sentiments = db.execute(
        select(Sentiment)
        .join(
            Article,
            and_(Sentiment.document_type == "article", Sentiment.document_id == Article.id),
        )
        .where(func.date(Article.published_at) == snapshot_date)
    ).scalars().all()
    community_sentiments = db.execute(
        select(Sentiment)
        .join(
            CommunityPost,
            and_(Sentiment.document_type == "community_post", Sentiment.document_id == CommunityPost.id),
        )
        .where(func.date(CommunityPost.created_at) == snapshot_date)
    ).scalars().all()
    sentiments = [*article_sentiments, *community_sentiments]

    if not sentiments:
        snapshot = existing or DailyMarketSentimentSnapshot(snapshot_date=snapshot_date, country=country)
        snapshot.sentiment_score = 0.0
        snapshot.fear_greed_score = 50.0
        snapshot.hate_index = 0.0
        snapshot.uncertainty_score = 0.0
        snapshot.bullish_ratio = 0.0
        snapshot.bearish_ratio = 0.0
        snapshot.neutral_ratio = 1.0
        snapshot.top_keywords_json = []
        snapshot.source_counts_json = {}
        if existing is None:
            db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    count = len(sentiments)
    keywords = Counter(keyword for item in sentiments for keyword in item.keywords_json)
    biases = Counter(item.market_bias for item in sentiments)
    snapshot = existing or DailyMarketSentimentSnapshot(snapshot_date=snapshot_date, country=country)
    snapshot.sentiment_score = sum(item.sentiment_score for item in sentiments) / count
    snapshot.fear_greed_score = sum(item.fear_greed_score for item in sentiments) / count
    snapshot.hate_index = sum(item.hate_index for item in sentiments) / count
    snapshot.uncertainty_score = sum(item.uncertainty_score for item in sentiments) / count
    snapshot.bullish_ratio = biases.get("bullish", 0) / count
    snapshot.bearish_ratio = biases.get("bearish", 0) / count
    snapshot.neutral_ratio = biases.get("neutral", 0) / count
    snapshot.top_keywords_json = [word for word, _ in keywords.most_common(10)]
    snapshot.source_counts_json = {"documents": count}
    if existing is None:
        db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot
