from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class CommunityPost(TimestampMixin, Base):
    __tablename__ = "community_posts"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_community_posts_source_external"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    board_name: Mapped[str] = mapped_column(String(255), index=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    author_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    view_count: Mapped[int | None] = mapped_column(Integer)
    upvotes: Mapped[int | None] = mapped_column(Integer)
    downvotes: Mapped[int | None] = mapped_column(Integer)
    comment_count: Mapped[int | None] = mapped_column(Integer)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    source: Mapped["Source"] = relationship(back_populates="community_posts")
    comments: Mapped[list["CommunityComment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class CommunityComment(TimestampMixin, Base):
    __tablename__ = "community_comments"
    __table_args__ = (
        UniqueConstraint("post_id", "external_id", name="uq_community_comments_post_external"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    author_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    upvotes: Mapped[int | None] = mapped_column(Integer)
    downvotes: Mapped[int | None] = mapped_column(Integer)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    post: Mapped["CommunityPost"] = relationship(back_populates="comments")
