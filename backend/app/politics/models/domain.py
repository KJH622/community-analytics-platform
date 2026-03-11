from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy import UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PoliticalParty(Base):
    __tablename__ = "political_parties"
    __table_args__ = (UniqueConstraint("name", "country", name="uq_political_party_name_country"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    country: Mapped[str] = mapped_column(String(50), index=True, default="KR")
    ideology: Mapped[str | None] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    official_color: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    politicians: Mapped[list["Politician"]] = relationship(back_populates="party_rel")


class Politician(Base):
    __tablename__ = "politicians"
    __table_args__ = (UniqueConstraint("name", "country", name="uq_politician_name_country"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    party: Mapped[str | None] = mapped_column(String(255), index=True)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("political_parties.id", ondelete="SET NULL"))
    position: Mapped[str | None] = mapped_column(String(255), index=True)
    ideology: Mapped[str | None] = mapped_column(String(100), index=True)
    country: Mapped[str] = mapped_column(String(50), index=True, default="KR")
    start_term: Mapped[date | None] = mapped_column(Date)
    end_term: Mapped[date | None] = mapped_column(Date)
    aliases_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    party_rel: Mapped[PoliticalParty | None] = relationship(back_populates="politicians")


class PoliticalIndicator(Base):
    __tablename__ = "political_indicators"
    __table_args__ = (UniqueConstraint("code", "country", name="uq_political_indicator_code_country"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(100), index=True)
    indicator_name: Mapped[str] = mapped_column(String(255), index=True)
    country: Mapped[str] = mapped_column(String(50), index=True, default="KR")
    description: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str | None] = mapped_column(String(255))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    values: Mapped[list["PoliticalIndicatorValue"]] = relationship(back_populates="indicator")


class PoliticalIndicatorValue(Base):
    __tablename__ = "political_indicator_values"
    __table_args__ = (
        UniqueConstraint("indicator_id", "date", "label", name="uq_political_indicator_value"),
        Index("ix_political_indicator_value_lookup", "indicator_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    indicator_id: Mapped[int] = mapped_column(
        ForeignKey("political_indicators.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)
    value: Mapped[float] = mapped_column(Float)
    label: Mapped[str | None] = mapped_column(String(255), index=True)
    source: Mapped[str | None] = mapped_column(String(255))
    unit: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    indicator: Mapped["PoliticalIndicator"] = relationship(back_populates="values")


class PoliticalTopic(Base):
    __tablename__ = "political_topics"
    __table_args__ = (UniqueConstraint("code", name="uq_political_topic_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    keywords_json: Mapped[list[str]] = mapped_column(JSON, default=list)


class PoliticalEntity(Base):
    __tablename__ = "political_entities"
    __table_args__ = (UniqueConstraint("name", "entity_type", name="uq_political_entity_name_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    aliases_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class PoliticalCommunitySource(Base):
    __tablename__ = "political_community_sources"
    __table_args__ = (UniqueConstraint("code", name="uq_political_community_source_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    leaning: Mapped[str | None] = mapped_column(String(100), index=True)
    link: Mapped[str] = mapped_column(String(500))
    board_name: Mapped[str | None] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True, default="disabled")
    compliance_notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class PoliticalPost(Base):
    __tablename__ = "political_posts"
    __table_args__ = (
        UniqueConstraint("source_code", "external_post_id", name="uq_political_post_source_external"),
        Index("ix_political_posts_lookup", "community_name", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_code: Mapped[str] = mapped_column(String(100), index=True)
    community_name: Mapped[str] = mapped_column(String(255), index=True)
    board_name: Mapped[str | None] = mapped_column(String(255), index=True)
    external_post_id: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500), index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    view_count: Mapped[int | None] = mapped_column(Integer)
    upvotes: Mapped[int | None] = mapped_column(Integer)
    comment_count: Mapped[int | None] = mapped_column(Integer)
    original_url: Mapped[str] = mapped_column(String(1000))
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)


class PoliticalSentiment(Base):
    __tablename__ = "political_sentiment"
    __table_args__ = (
        UniqueConstraint("post_id", name="uq_political_sentiment_post"),
        Index("ix_political_sentiment_scores", "political_polarization_index", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("political_posts.id", ondelete="CASCADE"), index=True)
    political_sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    support_score: Mapped[float] = mapped_column(Float, default=0.0)
    opposition_score: Mapped[float] = mapped_column(Float, default=0.0)
    anger_score: Mapped[float] = mapped_column(Float, default=0.0)
    mockery_score: Mapped[float] = mapped_column(Float, default=0.0)
    political_hate_score: Mapped[float] = mapped_column(Float, default=0.0)
    apathy_score: Mapped[float] = mapped_column(Float, default=0.0)
    enthusiasm_score: Mapped[float] = mapped_column(Float, default=0.0)
    political_polarization_index: Mapped[float] = mapped_column(Float, default=0.0)
    election_heat_index: Mapped[float] = mapped_column(Float, default=0.0)
    politician_mentions_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    keywords_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    labels_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PoliticalDailySnapshot(Base):
    __tablename__ = "political_daily_snapshot"
    __table_args__ = (
        UniqueConstraint("snapshot_date", "country", name="uq_political_snapshot_date_country"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    country: Mapped[str] = mapped_column(String(50), index=True, default="KR")
    political_sentiment_score: Mapped[float] = mapped_column(Float)
    political_polarization_index: Mapped[float] = mapped_column(Float)
    election_heat_index: Mapped[float] = mapped_column(Float)
    top_keywords_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    top_politicians_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_counts_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
