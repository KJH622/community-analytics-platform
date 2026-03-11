from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum as SqlEnum, Float, ForeignKey, Index
from sqlalchemy import Integer, Numeric, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SourceType(str, Enum):
    INDICATOR = "indicator"
    NEWS = "news"
    COMMUNITY = "community"


class ConnectorStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    MOCK = "mock"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[SourceType] = mapped_column(SqlEnum(SourceType), index=True)
    country: Mapped[str | None] = mapped_column(String(50), index=True)
    base_url: Mapped[str | None] = mapped_column(String(500))
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    compliance_notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    connectors: Mapped[list["SourceConnector"]] = relationship(back_populates="source")


class SourceConnector(Base):
    __tablename__ = "source_connectors"
    __table_args__ = (UniqueConstraint("source_id", "name", name="uq_source_connector_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    connector_type: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[ConnectorStatus] = mapped_column(SqlEnum(ConnectorStatus), default=ConnectorStatus.ACTIVE)
    schedule_cron: Mapped[str | None] = mapped_column(String(100))
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=30)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=20)
    robots_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped["Source"] = relationship(back_populates="connectors")


class EconomicIndicator(Base):
    __tablename__ = "economic_indicators"
    __table_args__ = (UniqueConstraint("code", "country", name="uq_indicator_code_country"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    country: Mapped[str] = mapped_column(String(50), index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    unit: Mapped[str | None] = mapped_column(String(50))
    frequency: Mapped[str | None] = mapped_column(String(50))
    importance: Mapped[int] = mapped_column(Integer, default=3)
    description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    releases: Mapped[list["IndicatorRelease"]] = relationship(back_populates="indicator")


class IndicatorRelease(Base):
    __tablename__ = "indicator_releases"
    __table_args__ = (
        UniqueConstraint("indicator_id", "country", "release_date", "release_time", name="uq_indicator_release"),
        Index("ix_indicator_release_lookup", "indicator_id", "release_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    indicator_id: Mapped[int] = mapped_column(
        ForeignKey("economic_indicators.id", ondelete="CASCADE"), index=True
    )
    country: Mapped[str] = mapped_column(String(50), index=True)
    release_date: Mapped[date] = mapped_column(Date, index=True)
    release_time: Mapped[time | None] = mapped_column(Time)
    actual_value: Mapped[float | None] = mapped_column(Numeric(18, 4))
    forecast_value: Mapped[float | None] = mapped_column(Numeric(18, 4))
    previous_value: Mapped[float | None] = mapped_column(Numeric(18, 4))
    unit: Mapped[str | None] = mapped_column(String(50))
    importance: Mapped[int] = mapped_column(Integer, default=3)
    source_url: Mapped[str | None] = mapped_column(String(500))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    indicator: Mapped["EconomicIndicator"] = relationship(back_populates="releases")


class ArticleCluster(Base):
    __tablename__ = "article_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    topic_label: Mapped[str | None] = mapped_column(String(255), index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    articles: Mapped[list["Article"]] = relationship(back_populates="cluster")


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("canonical_url", name="uq_article_canonical_url"),
        Index("ix_articles_search", "published_at", "source_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), index=True)
    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("article_clusters.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(500), index=True)
    body: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(255))
    publisher: Mapped[str | None] = mapped_column(String(255), index=True)
    canonical_url: Mapped[str] = mapped_column(String(1000))
    original_url: Mapped[str | None] = mapped_column(String(1000))
    language: Mapped[str] = mapped_column(String(10), default="ko")
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    tags_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    title_hash: Mapped[str] = mapped_column(String(64), index=True)
    body_hash: Mapped[str] = mapped_column(String(64), index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)

    cluster: Mapped[ArticleCluster | None] = relationship(back_populates="articles")


class CommunityPost(Base):
    __tablename__ = "community_posts"
    __table_args__ = (
        UniqueConstraint("source_id", "external_post_id", name="uq_community_external_post"),
        Index("ix_community_posts_lookup", "board_name", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), index=True)
    board_name: Mapped[str] = mapped_column(String(255), index=True)
    external_post_id: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500), index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    author_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    view_count: Mapped[int | None] = mapped_column(Integer)
    upvotes: Mapped[int | None] = mapped_column(Integer)
    downvotes: Mapped[int | None] = mapped_column(Integer)
    comment_count: Mapped[int | None] = mapped_column(Integer)
    original_url: Mapped[str] = mapped_column(String(1000))
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)

    comments: Mapped[list["CommunityComment"]] = relationship(back_populates="post")


class CommunityComment(Base):
    __tablename__ = "community_comments"
    __table_args__ = (
        UniqueConstraint("post_id", "external_comment_id", name="uq_community_external_comment"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id", ondelete="CASCADE"), index=True)
    external_comment_id: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    author_hash: Mapped[str | None] = mapped_column(String(128))
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)

    post: Mapped["CommunityPost"] = relationship(back_populates="comments")


class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (UniqueConstraint("name", "entity_type", name="uq_entity_name_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    aliases_json: Mapped[list[str]] = mapped_column(JSON, default=list)


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("code", name="uq_topic_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    keywords_json: Mapped[list[str]] = mapped_column(JSON, default=list)


class Sentiment(Base):
    __tablename__ = "sentiments"
    __table_args__ = (
        UniqueConstraint("document_type", "document_id", name="uq_sentiment_document"),
        Index("ix_sentiment_scores", "market_bias", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_type: Mapped[str] = mapped_column(String(50), index=True)
    document_id: Mapped[int] = mapped_column(Integer, index=True)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    fear_greed_score: Mapped[float] = mapped_column(Float, default=50.0)
    hate_index: Mapped[float] = mapped_column(Float, default=0.0)
    uncertainty_score: Mapped[float] = mapped_column(Float, default=0.0)
    market_bias: Mapped[str] = mapped_column(String(20), index=True)
    keywords_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    entities_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    topics_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentTag(Base):
    __tablename__ = "document_tags"
    __table_args__ = (
        UniqueConstraint("document_type", "document_id", "tag_type", "tag_value", name="uq_document_tag"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_type: Mapped[str] = mapped_column(String(50), index=True)
    document_id: Mapped[int] = mapped_column(Integer, index=True)
    tag_type: Mapped[str] = mapped_column(String(50), index=True)
    tag_value: Mapped[str] = mapped_column(String(255), index=True)
    score: Mapped[float | None] = mapped_column(Float)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (UniqueConstraint("name", name="uq_ingestion_job_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(50), index=True)
    schedule_cron: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[JobStatus] = mapped_column(SqlEnum(JobStatus), default=JobStatus.PENDING)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)

    logs: Mapped[list["IngestionLog"]] = relationship(back_populates="job")


class IngestionLog(Base):
    __tablename__ = "ingestion_logs"
    __table_args__ = (Index("ix_ingestion_logs_job_created", "job_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("ingestion_jobs.id", ondelete="CASCADE"), index=True)
    status: Mapped[JobStatus] = mapped_column(SqlEnum(JobStatus), index=True)
    message: Mapped[str] = mapped_column(Text)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)

    job: Mapped["IngestionJob"] = relationship(back_populates="logs")


class DailyMarketSentimentSnapshot(Base):
    __tablename__ = "daily_market_sentiment_snapshots"
    __table_args__ = (
        UniqueConstraint("snapshot_date", "country", name="uq_snapshot_date_country"),
        Index("ix_market_snapshots_lookup", "snapshot_date", "country"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    country: Mapped[str] = mapped_column(String(50), index=True)
    sentiment_score: Mapped[float] = mapped_column(Float)
    fear_greed_score: Mapped[float] = mapped_column(Float)
    hate_index: Mapped[float] = mapped_column(Float)
    uncertainty_score: Mapped[float] = mapped_column(Float)
    bullish_ratio: Mapped[float] = mapped_column(Float)
    bearish_ratio: Mapped[float] = mapped_column(Float)
    neutral_ratio: Mapped[float] = mapped_column(Float)
    top_keywords_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_counts_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
