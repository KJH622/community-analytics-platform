from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class IngestionJob(TimestampMixin, Base):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (Index("ix_ingestion_jobs_job_name", "job_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    triggered_by: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduler")
    items_seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_written: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text)
    job_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)

    logs: Mapped[list["IngestionLog"]] = relationship(back_populates="job")


class IngestionLog(TimestampMixin, Base):
    __tablename__ = "ingestion_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("ingestion_jobs.id"), index=True)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    job: Mapped["IngestionJob"] = relationship(back_populates="logs")
