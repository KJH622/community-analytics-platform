from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.community import CommunityPost
from app.models.reference import DocumentTag
from app.models.sentiment import DailyMarketSentimentSnapshot, Sentiment
from app.services.content_filters import classify_market_emotional_signal, classify_market_post


@dataclass(slots=True)
class SnapshotMetrics:
    sentiment_avg: float
    fear_greed_avg: float
    hate_index_avg: float
    uncertainty_avg: float
    bullish_ratio: float
    bearish_ratio: float
    neutral_ratio: float
    article_count: int
    community_post_count: int
    top_keywords: list[str]


def compute_snapshot_for_date(
    db: Session,
    snapshot_date: date,
    *,
    source_kind: str = "all",
) -> SnapshotMetrics:
    article_pairs: list[tuple[Article, Sentiment]] = []
    if source_kind in {"all", "news"}:
        articles = db.scalars(
            select(Article).where(Article.published_at.is_not(None))
        ).all()
        article_ids = [article.id for article in articles if article.published_at and article.published_at.date() == snapshot_date]
        if article_ids:
            sentiments = db.scalars(
                select(Sentiment).where(
                    Sentiment.document_type == "article",
                    Sentiment.document_id.in_(article_ids),
                )
            ).all()
            sentiment_map = {item.document_id: item for item in sentiments}
            article_pairs = [
                (article, sentiment_map[article.id])
                for article in articles
                if article.id in sentiment_map and article.published_at and article.published_at.date() == snapshot_date
            ]

    community_posts = db.scalars(
        select(CommunityPost).where(CommunityPost.published_at.is_not(None))
    ).all()
    community_for_day = [
        post
        for post in community_posts
        if post.published_at and post.published_at.date() == snapshot_date
    ]
    post_ids = [post.id for post in community_for_day]
    post_sentiments = db.scalars(
        select(Sentiment).where(
            Sentiment.document_type == "community_post",
            Sentiment.document_id.in_(post_ids) if post_ids else False,
        )
    ).all() if post_ids else []
    post_sentiment_map = {item.document_id: item for item in post_sentiments}
    filtered_post_pairs = [
        (post, post_sentiment_map[post.id])
        for post in community_for_day
        if post.id in post_sentiment_map
        and not classify_market_post(post.title, post.body).excluded
        and classify_market_emotional_signal(
            title=post.title,
            body=post.body,
            sentiment=post_sentiment_map[post.id],
        ).included
    ]

    selected_sentiments: list[Sentiment] = []
    if source_kind in {"all", "news"}:
        selected_sentiments.extend(sentiment for _, sentiment in article_pairs)
    if source_kind in {"all", "community"}:
        selected_sentiments.extend(sentiment for _, sentiment in filtered_post_pairs)

    total = len(selected_sentiments)
    if total == 0:
        return SnapshotMetrics(
            sentiment_avg=0.0,
            fear_greed_avg=0.0,
            hate_index_avg=0.0,
            uncertainty_avg=0.0,
            bullish_ratio=0.0,
            bearish_ratio=0.0,
            neutral_ratio=0.0,
            article_count=len(article_pairs) if source_kind != "community" else 0,
            community_post_count=len(filtered_post_pairs) if source_kind != "news" else 0,
            top_keywords=[],
        )

    bullish = sum(1 for sentiment in selected_sentiments if sentiment.market_bias == "bullish")
    bearish = sum(1 for sentiment in selected_sentiments if sentiment.market_bias == "bearish")
    neutral = total - bullish - bearish

    keyword_counter = Counter()
    if source_kind in {"all", "news"}:
        for article, _ in article_pairs:
            tags = db.scalars(
                select(DocumentTag).where(
                    DocumentTag.document_type == "article",
                    DocumentTag.document_id == article.id,
                    DocumentTag.tag_type == "keyword",
                )
            ).all()
            keyword_counter.update(tag.tag_value for tag in tags)
    if source_kind in {"all", "community"}:
        for post, _ in filtered_post_pairs:
            tags = db.scalars(
                select(DocumentTag).where(
                    DocumentTag.document_type == "community_post",
                    DocumentTag.document_id == post.id,
                    DocumentTag.tag_type == "keyword",
                )
            ).all()
            keyword_counter.update(tag.tag_value for tag in tags)

    return SnapshotMetrics(
        sentiment_avg=round(sum(item.sentiment_score for item in selected_sentiments) / total, 2),
        fear_greed_avg=round(sum(item.fear_greed_score for item in selected_sentiments) / total, 2),
        hate_index_avg=round(sum(item.hate_index for item in selected_sentiments) / total, 2),
        uncertainty_avg=round(sum(item.uncertainty_score for item in selected_sentiments) / total, 2),
        bullish_ratio=round(bullish / total, 4),
        bearish_ratio=round(bearish / total, 4),
        neutral_ratio=round(neutral / total, 4),
        article_count=len(article_pairs) if source_kind != "community" else 0,
        community_post_count=len(filtered_post_pairs) if source_kind != "news" else 0,
        top_keywords=[keyword for keyword, _ in keyword_counter.most_common(8)],
    )


def upsert_daily_snapshot(db: Session, snapshot_date: date, source_kind: str = "all") -> None:
    metrics = compute_snapshot_for_date(db, snapshot_date, source_kind=source_kind)
    snapshot_key = f"{snapshot_date.isoformat()}::{source_kind}::all::all"
    existing = db.scalar(
        select(DailyMarketSentimentSnapshot).where(
            DailyMarketSentimentSnapshot.snapshot_key == snapshot_key
        )
    )
    if existing:
        existing.sentiment_avg = metrics.sentiment_avg
        existing.fear_greed_avg = metrics.fear_greed_avg
        existing.hate_index_avg = metrics.hate_index_avg
        existing.uncertainty_avg = metrics.uncertainty_avg
        existing.bullish_ratio = metrics.bullish_ratio
        existing.bearish_ratio = metrics.bearish_ratio
        existing.neutral_ratio = metrics.neutral_ratio
        existing.article_count = metrics.article_count
        existing.community_post_count = metrics.community_post_count
        existing.top_keywords = metrics.top_keywords
        return

    db.add(
        DailyMarketSentimentSnapshot(
            snapshot_key=snapshot_key,
            snapshot_date=snapshot_date,
            source_kind=source_kind,
            country="all",
            topic_code="all",
            sentiment_avg=metrics.sentiment_avg,
            fear_greed_avg=metrics.fear_greed_avg,
            hate_index_avg=metrics.hate_index_avg,
            uncertainty_avg=metrics.uncertainty_avg,
            bullish_ratio=metrics.bullish_ratio,
            bearish_ratio=metrics.bearish_ratio,
            neutral_ratio=metrics.neutral_ratio,
            article_count=metrics.article_count,
            community_post_count=metrics.community_post_count,
            top_keywords=metrics.top_keywords,
        )
    )
