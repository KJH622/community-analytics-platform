from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class PoliticalParty(TimestampMixin, Base):
    __tablename__ = "political_parties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    ideology: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str] = mapped_column(String(8), default="KR", index=True)
    description: Mapped[str | None] = mapped_column(Text)

    politicians: Mapped[list["Politician"]] = relationship(back_populates="party_ref")


class Politician(TimestampMixin, Base):
    __tablename__ = "politicians"
    __table_args__ = (Index("ix_politicians_name_country", "name", "country"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    party: Mapped[str | None] = mapped_column(String(255), index=True)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("political_parties.id"), index=True)
    position: Mapped[str | None] = mapped_column(String(255))
    ideology: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str] = mapped_column(String(8), default="KR", index=True)
    start_term: Mapped[date | None] = mapped_column(Date)
    end_term: Mapped[date | None] = mapped_column(Date)
    profile_url: Mapped[str | None] = mapped_column(String(500))

    party_ref: Mapped["PoliticalParty | None"] = relationship(back_populates="politicians")


class PoliticalIndicator(TimestampMixin, Base):
    __tablename__ = "political_indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    indicator_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(8), default="KR", index=True)
    unit: Mapped[str | None] = mapped_column(String(32))
    source: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    values: Mapped[list["PoliticalIndicatorValue"]] = relationship(back_populates="indicator")


class PoliticalIndicatorValue(TimestampMixin, Base):
    __tablename__ = "political_indicator_values"
    __table_args__ = (
        UniqueConstraint("indicator_id", "date", "label", name="uq_political_indicator_value"),
        Index("ix_political_indicator_values_indicator_date", "indicator_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    indicator_id: Mapped[int] = mapped_column(ForeignKey("political_indicators.id"), index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str | None] = mapped_column(String(255))
    unit: Mapped[str | None] = mapped_column(String(32))

    indicator: Mapped["PoliticalIndicator"] = relationship(back_populates="values")


class PoliticalTopic(TimestampMixin, Base):
    __tablename__ = "political_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list[str] | None] = mapped_column(JSON)


class PoliticalPost(TimestampMixin, Base):
    __tablename__ = "political_posts"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_political_posts_source_external"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), index=True)
    community_name: Mapped[str] = mapped_column(String(255), index=True)
    board_name: Mapped[str] = mapped_column(String(255), index=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    view_count: Mapped[int | None] = mapped_column(Integer)
    upvotes: Mapped[int | None] = mapped_column(Integer)
    comment_count: Mapped[int | None] = mapped_column(Integer)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    sentiment: Mapped["PoliticalSentiment | None"] = relationship(
        back_populates="post", cascade="all, delete-orphan", uselist=False
    )
    entities: Mapped[list["PoliticalEntity"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class PoliticalSentiment(TimestampMixin, Base):
    __tablename__ = "political_sentiment"
    __table_args__ = (
        UniqueConstraint("post_id", name="uq_political_sentiment_post_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("political_posts.id"), index=True)
    political_sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)
    support_score: Mapped[float] = mapped_column(Float, nullable=False)
    opposition_score: Mapped[float] = mapped_column(Float, nullable=False)
    anger_score: Mapped[float] = mapped_column(Float, nullable=False)
    sarcasm_score: Mapped[float] = mapped_column(Float, nullable=False)
    apathy_score: Mapped[float] = mapped_column(Float, nullable=False)
    enthusiasm_score: Mapped[float] = mapped_column(Float, nullable=False)
    political_polarization_index: Mapped[float] = mapped_column(Float, nullable=False)
    election_heat_index: Mapped[float] = mapped_column(Float, nullable=False)
    labels: Mapped[list[str] | None] = mapped_column(JSON)
    keywords: Mapped[list[str] | None] = mapped_column(JSON)

    post: Mapped["PoliticalPost"] = relationship(back_populates="sentiment")


class PoliticalEntity(TimestampMixin, Base):
    __tablename__ = "political_entities"
    __table_args__ = (
        Index("ix_political_entities_entity_type_name", "entity_type", "name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("political_posts.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_name: Mapped[str | None] = mapped_column(String(255))
    mention_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    post: Mapped["PoliticalPost"] = relationship(back_populates="entities")


class PoliticalDailySnapshot(TimestampMixin, Base):
    __tablename__ = "political_daily_snapshot"
    __table_args__ = (
        UniqueConstraint("snapshot_date", name="uq_political_daily_snapshot_date"),
        Index("ix_political_daily_snapshot_date", "snapshot_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    political_sentiment_avg: Mapped[float] = mapped_column(Float, nullable=False)
    political_polarization_index: Mapped[float] = mapped_column(Float, nullable=False)
    election_heat_index: Mapped[float] = mapped_column(Float, nullable=False)
    top_keywords: Mapped[list[str] | None] = mapped_column(JSON)
    top_politicians: Mapped[list[str] | None] = mapped_column(JSON)
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
