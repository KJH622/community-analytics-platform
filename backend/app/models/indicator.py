from __future__ import annotations

from datetime import date, time

from sqlalchemy import Date, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class EconomicIndicator(TimestampMixin, Base):
    __tablename__ = "economic_indicators"
    __table_args__ = (UniqueConstraint("code", name="uq_economic_indicators_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(8), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    unit: Mapped[str | None] = mapped_column(String(64))
    frequency: Mapped[str | None] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(500))
    next_release_at: Mapped[str | None] = mapped_column(String(64))

    source: Mapped["Source | None"] = relationship(back_populates="indicators")
    releases: Mapped[list["IndicatorRelease"]] = relationship(back_populates="indicator")


class IndicatorRelease(TimestampMixin, Base):
    __tablename__ = "indicator_releases"
    __table_args__ = (
        UniqueConstraint("indicator_id", "release_date", name="uq_indicator_release_date"),
        Index("ix_indicator_releases_indicator_date", "indicator_id", "release_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    indicator_id: Mapped[int] = mapped_column(ForeignKey("economic_indicators.id"), index=True)
    country: Mapped[str] = mapped_column(String(8), index=True)
    release_date: Mapped[date] = mapped_column(Date, nullable=False)
    release_time: Mapped[time | None]
    actual_value: Mapped[float | None] = mapped_column(Float)
    forecast_value: Mapped[float | None] = mapped_column(Float)
    previous_value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(64))
    importance: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500))

    indicator: Mapped["EconomicIndicator"] = relationship(back_populates="releases")
