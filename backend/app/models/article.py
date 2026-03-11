from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ArticleCluster(TimestampMixin, Base):
    __tablename__ = "article_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    topic: Mapped[str | None] = mapped_column(String(128), index=True)
    representative_title: Mapped[str] = mapped_column(String(500), nullable=False)
    centroid_terms: Mapped[list[str] | None] = mapped_column(JSON)

    articles: Mapped[list["Article"]] = relationship(back_populates="cluster")


class Article(TimestampMixin, Base):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("source_id", "canonical_url", name="uq_articles_source_canonical_url"),
        Index("ix_articles_source_published", "source_id", "published_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("article_clusters.id"), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    canonical_url: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128), index=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    language: Mapped[str | None] = mapped_column(String(16), default="ko")
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    source: Mapped["Source"] = relationship(back_populates="articles")
    cluster: Mapped["ArticleCluster | None"] = relationship(back_populates="articles")
