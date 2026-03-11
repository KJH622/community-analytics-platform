from datetime import date, time

from pydantic import BaseModel


class IndicatorReleaseRead(BaseModel):
    release_date: date
    release_time: time | None
    actual_value: float | None
    forecast_value: float | None
    previous_value: float | None
    unit: str | None
    importance: int
    source_url: str | None

    model_config = {"from_attributes": True}


class IndicatorLatestRead(BaseModel):
    code: str
    name: str
    country: str
    category: str
    unit: str | None
    latest_release: IndicatorReleaseRead | None


class IndicatorHistoryRead(BaseModel):
    code: str
    name: str
    country: str
    releases: list[IndicatorReleaseRead]
