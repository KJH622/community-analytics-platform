from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Source(TimestampMixin, Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    country: Mapped[str | None] = mapped_column(String(8), index=True)
    base_url: Mapped[str | None] = mapped_column(String(500))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    robots_policy: Mapped[str | None] = mapped_column(Text)
    tos_notes: Mapped[str | None] = mapped_column(Text)
    source_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)

    connectors: Mapped[list["SourceConnector"]] = relationship(back_populates="source")
    indicators: Mapped[list["EconomicIndicator"]] = relationship(back_populates="source")
    articles: Mapped[list["Article"]] = relationship(back_populates="source")
    community_posts: Mapped[list["CommunityPost"]] = relationship(back_populates="source")


class SourceConnector(TimestampMixin, Base):
    __tablename__ = "source_connectors"
    __table_args__ = (UniqueConstraint("source_id", "connector_type", name="uq_source_connector"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    connector_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    schedule_hint: Mapped[str | None] = mapped_column(String(128))
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    connector_config: Mapped[dict[str, Any] | None] = mapped_column("config", JSON)
    legal_notes: Mapped[str | None] = mapped_column(Text)

    source: Mapped["Source"] = relationship(back_populates="connectors")


class Entity(TimestampMixin, Base):
    __tablename__ = "entities"
    __table_args__ = (Index("ix_entities_type_name", "entity_type", "canonical_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(32), index=True)
    entity_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)


class Topic(TimestampMixin, Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list[str] | None] = mapped_column(JSON)


class DocumentTag(TimestampMixin, Base):
    __tablename__ = "document_tags"
    __table_args__ = (
        Index("ix_document_tags_doc", "document_type", "document_id"),
        Index("ix_document_tags_type_value", "tag_type", "tag_value"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    document_id: Mapped[int] = mapped_column(Integer, nullable=False)
    tag_type: Mapped[str] = mapped_column(String(32), nullable=False)
    tag_value: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[float] = mapped_column(default=1.0, nullable=False)
