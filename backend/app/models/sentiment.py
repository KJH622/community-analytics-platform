from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import JSON, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Sentiment(TimestampMixin, Base):
    __tablename__ = "sentiments"
    __table_args__ = (
        UniqueConstraint("document_type", "document_id", name="uq_sentiments_document"),
        Index("ix_sentiments_doc", "document_type", "document_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    document_id: Mapped[int] = mapped_column(Integer, nullable=False)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)
    fear_greed_score: Mapped[float] = mapped_column(Float, nullable=False)
    hate_index: Mapped[float] = mapped_column(Float, nullable=False)
    uncertainty_score: Mapped[float] = mapped_column(Float, nullable=False)
    market_bias: Mapped[str] = mapped_column(String(16), nullable=False)
    labels: Mapped[list[str] | None] = mapped_column(JSON)
    keywords: Mapped[list[str] | None] = mapped_column(JSON)
    analysis_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)


class DailyMarketSentimentSnapshot(TimestampMixin, Base):
    __tablename__ = "daily_market_sentiment_snapshots"
    __table_args__ = (
        UniqueConstraint("snapshot_key", name="uq_daily_market_sentiment_snapshots_snapshot_key"),
        Index("ix_daily_snapshots_date", "snapshot_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_key: Mapped[str] = mapped_column(String(255), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(nullable=False)
    source_kind: Mapped[str | None] = mapped_column(String(32), index=True)
    country: Mapped[str | None] = mapped_column(String(8), index=True)
    topic_code: Mapped[str | None] = mapped_column(String(64), index=True)
    sentiment_avg: Mapped[float] = mapped_column(Float, nullable=False)
    fear_greed_avg: Mapped[float] = mapped_column(Float, nullable=False)
    hate_index_avg: Mapped[float] = mapped_column(Float, nullable=False)
    uncertainty_avg: Mapped[float] = mapped_column(Float, nullable=False)
    bullish_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    bearish_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    neutral_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    article_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    community_post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    top_keywords: Mapped[list[str] | None] = mapped_column(JSON)
