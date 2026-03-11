from __future__ import annotations

from collections import Counter
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DailyMarketSentimentSnapshot, Sentiment


def calculate_daily_snapshot(
    db: Session, snapshot_date: date, country: str = "GLOBAL"
) -> DailyMarketSentimentSnapshot:
    existing = db.execute(
        select(DailyMarketSentimentSnapshot).where(
            DailyMarketSentimentSnapshot.snapshot_date == snapshot_date,
            DailyMarketSentimentSnapshot.country == country,
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    sentiments = db.execute(
        select(Sentiment).where(func.date(Sentiment.created_at) == snapshot_date)
    ).scalars().all()

    if not sentiments:
        snapshot = DailyMarketSentimentSnapshot(
            snapshot_date=snapshot_date,
            country=country,
            sentiment_score=0.0,
            fear_greed_score=50.0,
            hate_index=0.0,
            uncertainty_score=0.0,
            bullish_ratio=0.0,
            bearish_ratio=0.0,
            neutral_ratio=1.0,
            top_keywords_json=[],
            source_counts_json={},
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    count = len(sentiments)
    keywords = Counter(keyword for item in sentiments for keyword in item.keywords_json)
    biases = Counter(item.market_bias for item in sentiments)
    snapshot = DailyMarketSentimentSnapshot(
        snapshot_date=snapshot_date,
        country=country,
        sentiment_score=sum(item.sentiment_score for item in sentiments) / count,
        fear_greed_score=sum(item.fear_greed_score for item in sentiments) / count,
        hate_index=sum(item.hate_index for item in sentiments) / count,
        uncertainty_score=sum(item.uncertainty_score for item in sentiments) / count,
        bullish_ratio=biases.get("bullish", 0) / count,
        bearish_ratio=biases.get("bearish", 0) / count,
        neutral_ratio=biases.get("neutral", 0) / count,
        top_keywords_json=[word for word, _ in keywords.most_common(10)],
        source_counts_json={"documents": count},
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot
