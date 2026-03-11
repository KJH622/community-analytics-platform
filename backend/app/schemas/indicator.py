from datetime import date, time

from pydantic import BaseModel

from app.schemas.common import ORMModel


class IndicatorReleaseRead(ORMModel):
    id: int
    release_date: date
    release_time: time | None
    actual_value: float | None
    forecast_value: float | None
    previous_value: float | None
    unit: str | None
    importance: int
    source_url: str | None


class IndicatorLatestRead(ORMModel):
    id: int
    code: str
    name: str
    country: str
    category: str
    unit: str | None
    frequency: str | None
    source_url: str | None
    latest_release: IndicatorReleaseRead | None = None


class IndicatorHistoryResponse(BaseModel):
    indicator_code: str
    releases: list[IndicatorReleaseRead]
