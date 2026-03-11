from __future__ import annotations

from collections import Counter
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.reference import Source
from app.politics.analytics.rule_based import analyze_political_text
from app.politics.collectors.base import NormalizedPoliticalIndicatorValue, NormalizedPoliticalPost
from app.politics.models.tables import (
    PoliticalDailySnapshot,
    PoliticalEntity,
    PoliticalIndicator,
    PoliticalIndicatorValue,
    PoliticalPost,
    PoliticalSentiment,
)
from app.services.storage import get_or_create_source
from app.services.text_cleaner import clean_text
from app.services.content_filters import classify_political_post
from app.utils.json import to_jsonable


def ensure_political_source(db: Session, code: str, name: str, base_url: str | None) -> Source:
    return get_or_create_source(
        db,
        code=code,
        name=name,
        kind="politics",
        country="KR",
        base_url=base_url,
        enabled=True,
        robots_policy="Must be reviewed per connector",
        tos_notes="Politics connectors stay disabled unless robots and TOS are reviewed.",
    )


def upsert_political_indicator_value(
    db: Session, payload: NormalizedPoliticalIndicatorValue
) -> PoliticalIndicatorValue:
    indicator = db.scalar(
        select(PoliticalIndicator).where(PoliticalIndicator.code == payload.indicator_code)
    )
    if indicator is None:
        indicator = PoliticalIndicator(
            code=payload.indicator_code,
            indicator_name=payload.indicator_name,
            country=payload.country,
            unit=payload.unit,
            source=payload.source,
            description=payload.description,
        )
        db.add(indicator)
        db.flush()
    existing = db.scalar(
        select(PoliticalIndicatorValue).where(
            PoliticalIndicatorValue.indicator_id == indicator.id,
            PoliticalIndicatorValue.date == payload.date,
            PoliticalIndicatorValue.label == payload.label,
        )
    )
    if existing:
        existing.value = payload.value
        existing.source = payload.source
        existing.unit = payload.unit
        return existing
    value = PoliticalIndicatorValue(
        indicator_id=indicator.id,
        date=payload.date,
        value=payload.value,
        label=payload.label,
        source=payload.source,
        unit=payload.unit,
    )
    db.add(value)
    db.flush()
    return value


def upsert_political_post(db: Session, source: Source, payload: NormalizedPoliticalPost) -> PoliticalPost:
    post = db.scalar(
        select(PoliticalPost).where(
            PoliticalPost.source_id == source.id,
            PoliticalPost.external_id == payload.external_id,
        )
    )
    if post is None:
        post = PoliticalPost(
            source_id=source.id,
            community_name=payload.community_name,
            board_name=payload.board_name,
            external_id=payload.external_id,
            title=payload.title,
            body=clean_text(payload.body) or None,
            published_at=payload.published_at,
            view_count=payload.view_count,
            upvotes=payload.upvotes,
            comment_count=payload.comment_count,
            url=payload.url,
            raw_payload=to_jsonable(payload.raw_payload),
        )
        db.add(post)
        db.flush()
    else:
        post.community_name = payload.community_name
        post.board_name = payload.board_name
        post.title = payload.title
        post.body = clean_text(payload.body) or None
        post.published_at = payload.published_at
        post.view_count = payload.view_count
        post.upvotes = payload.upvotes
        post.comment_count = payload.comment_count
        post.url = payload.url
        post.raw_payload = to_jsonable(payload.raw_payload)
    return post


def analyze_and_store_political_post(db: Session, post: PoliticalPost) -> PoliticalSentiment:
    result = analyze_political_text(post.title, post.body)
    sentiment = post.sentiment
    if sentiment is None:
        sentiment = PoliticalSentiment(
            post_id=post.id,
            political_sentiment_score=result.political_sentiment_score,
            support_score=result.support_score,
            opposition_score=result.opposition_score,
            anger_score=result.anger_score,
            sarcasm_score=result.sarcasm_score,
            apathy_score=result.apathy_score,
            enthusiasm_score=result.enthusiasm_score,
            political_polarization_index=result.political_polarization_index,
            election_heat_index=result.election_heat_index,
            labels=result.labels,
            keywords=result.keywords,
        )
        db.add(sentiment)
    else:
        sentiment.political_sentiment_score = result.political_sentiment_score
        sentiment.support_score = result.support_score
        sentiment.opposition_score = result.opposition_score
        sentiment.anger_score = result.anger_score
        sentiment.sarcasm_score = result.sarcasm_score
        sentiment.apathy_score = result.apathy_score
        sentiment.enthusiasm_score = result.enthusiasm_score
        sentiment.political_polarization_index = result.political_polarization_index
        sentiment.election_heat_index = result.election_heat_index
        sentiment.labels = result.labels
        sentiment.keywords = result.keywords

    post.entities.clear()
    db.flush()
    keyword_counter = Counter(result.keywords)
    for keyword, count in keyword_counter.items():
        entity_type = "politician" if keyword in result.politicians else "keyword"
        db.add(
            PoliticalEntity(
                post_id=post.id,
                entity_type=entity_type,
                name=keyword,
                canonical_name=keyword,
                mention_count=count,
                score=float(count),
            )
        )
    return sentiment


def update_political_daily_snapshot(db: Session, snapshot_date: date) -> None:
    posts = db.scalars(
        select(PoliticalPost).where(func.date(PoliticalPost.published_at) == snapshot_date)
    ).all()
    eligible_posts = [
        post for post in posts if not classify_political_post(post.title, post.body).excluded
    ]
    if not eligible_posts:
        eligible_posts = []

    post_ids = [post.id for post in eligible_posts]
    sentiments = db.scalars(
        select(PoliticalSentiment).where(PoliticalSentiment.post_id.in_(post_ids) if post_ids else False)
    ).all() if post_ids else []
    entities = db.scalars(
        select(PoliticalEntity).where(PoliticalEntity.post_id.in_(post_ids) if post_ids else False)
    ).all() if post_ids else []
    keyword_counter = Counter(row.name for row in entities if row.entity_type == "keyword")
    politician_counter = Counter(row.name for row in entities if row.entity_type == "politician")

    snapshot = db.scalar(
        select(PoliticalDailySnapshot).where(PoliticalDailySnapshot.snapshot_date == snapshot_date)
    )
    if snapshot is None:
        snapshot = PoliticalDailySnapshot(
            snapshot_date=snapshot_date,
            political_sentiment_avg=0.0,
            political_polarization_index=0.0,
            election_heat_index=0.0,
            top_keywords=[],
            top_politicians=[],
            post_count=0,
        )
        db.add(snapshot)
    if sentiments:
        snapshot.political_sentiment_avg = round(
            sum(item.political_sentiment_score for item in sentiments) / len(sentiments), 2
        )
        snapshot.political_polarization_index = round(
            sum(item.political_polarization_index for item in sentiments) / len(sentiments), 2
        )
        snapshot.election_heat_index = round(
            sum(item.election_heat_index for item in sentiments) / len(sentiments), 2
        )
    else:
        snapshot.political_sentiment_avg = 0.0
        snapshot.political_polarization_index = 0.0
        snapshot.election_heat_index = 0.0
    snapshot.top_keywords = [name for name, _ in keyword_counter.most_common(8)]
    snapshot.top_politicians = [name for name, _ in politician_counter.most_common(10)]
    snapshot.post_count = len(sentiments)
