from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.politics.models import (
    PoliticalCommunitySource,
    PoliticalDailySnapshot,
    PoliticalIndicator,
    PoliticalIndicatorValue,
    PoliticalPost,
    PoliticalSentiment,
    Politician,
)


def get_dashboard_payload(db: Session) -> dict:
    indicators = db.execute(select(PoliticalIndicator)).scalars().all()
    posts = db.execute(select(PoliticalPost).order_by(PoliticalPost.created_at.desc()).limit(5)).scalars().all()
    sources = db.execute(select(PoliticalCommunitySource).order_by(PoliticalCommunitySource.name)).scalars().all()
    snapshots = db.execute(
        select(PoliticalDailySnapshot).order_by(PoliticalDailySnapshot.snapshot_date.desc()).limit(14)
    ).scalars().all()
    sentiments = db.execute(select(PoliticalSentiment)).scalars().all()

    latest_cards = []
    approval_trend = []
    party_support = []
    for indicator in indicators:
        values = db.execute(
            select(PoliticalIndicatorValue)
            .where(PoliticalIndicatorValue.indicator_id == indicator.id)
            .order_by(PoliticalIndicatorValue.date.desc())
        ).scalars().all()
        if values:
            latest = values[0]
            latest_cards.append(
                {
                    "indicator_name": indicator.indicator_name,
                    "code": indicator.code,
                    "date": latest.date,
                    "value": latest.value,
                    "label": latest.label,
                    "source": latest.source,
                    "unit": latest.unit,
                }
            )
        if indicator.code == "president_approval":
            approval_trend = [
                {
                    "indicator_name": indicator.indicator_name,
                    "code": indicator.code,
                    "date": value.date,
                    "value": value.value,
                    "label": value.label,
                    "source": value.source,
                    "unit": value.unit,
                }
                for value in reversed(values[:12])
            ]
        if indicator.code == "party_support":
            party_support.extend(
                [
                    {
                        "indicator_name": indicator.indicator_name,
                        "code": indicator.code,
                        "date": value.date,
                        "value": value.value,
                        "label": value.label,
                        "source": value.source,
                        "unit": value.unit,
                    }
                    for value in reversed(values[:20])
                ]
            )

    keyword_counter = Counter(keyword for sentiment in sentiments for keyword in sentiment.keywords_json)
    politician_counter = Counter(name for sentiment in sentiments for name in sentiment.politician_mentions_json)

    return {
        "indicator_cards": latest_cards,
        "approval_trend": approval_trend,
        "party_support_comparison": party_support,
        "politician_mentions_top10": [{"name": name, "mentions": count} for name, count in politician_counter.most_common(10)],
        "keyword_trends": [{"keyword": word, "mentions": count} for word, count in keyword_counter.most_common(10)],
        "political_sentiment_index": [
            {"date": snapshot.snapshot_date.isoformat(), "value": snapshot.political_sentiment_score}
            for snapshot in reversed(snapshots)
        ],
        "polarization_index": [
            {"date": snapshot.snapshot_date.isoformat(), "value": snapshot.political_polarization_index}
            for snapshot in reversed(snapshots)
        ],
        "election_heat_index": [
            {"date": snapshot.snapshot_date.isoformat(), "value": snapshot.election_heat_index}
            for snapshot in reversed(snapshots)
        ],
        "community_posts": posts,
        "reference_communities": sources,
    }


def get_politicians(db: Session):
    return db.execute(select(Politician).order_by(Politician.name)).scalars().all()


def get_politician_by_name(db: Session, name: str):
    return db.execute(select(Politician).where(Politician.name == name)).scalar_one_or_none()


def get_political_indicators(db: Session):
    return db.execute(
        select(PoliticalIndicatorValue, PoliticalIndicator)
        .join(PoliticalIndicator, PoliticalIndicator.id == PoliticalIndicatorValue.indicator_id)
        .order_by(PoliticalIndicatorValue.date.desc())
    ).all()


def get_political_keywords(db: Session):
    sentiments = db.execute(select(PoliticalSentiment)).scalars().all()
    counter = Counter(keyword for item in sentiments for keyword in item.keywords_json)
    return [{"keyword": keyword, "mentions": mentions} for keyword, mentions in counter.most_common(20)]


def get_political_posts(db: Session):
    return db.execute(select(PoliticalPost).order_by(PoliticalPost.created_at.desc())).scalars().all()


def get_political_sentiments(db: Session):
    return db.execute(select(PoliticalSentiment).order_by(PoliticalSentiment.created_at.desc())).scalars().all()


def get_political_polarization(db: Session):
    snapshots = db.execute(
        select(PoliticalDailySnapshot).order_by(PoliticalDailySnapshot.snapshot_date.desc()).limit(30)
    ).scalars().all()
    return [{"date": item.snapshot_date, "value": item.political_polarization_index} for item in snapshots]
