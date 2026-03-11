from datetime import date

from pydantic import BaseModel


class MarketComparisonLatestRead(BaseModel):
    kospi_close: float | None
    kosdaq_close: float | None
    kospi_change_pct: float | None
    kosdaq_change_pct: float | None
    hate_index: float | None
    hate_change: float | None


class MarketComparisonPointRead(BaseModel):
    date: date
    kospi_close: float | None
    kosdaq_close: float | None
    hate_index: float
    kospi_scaled: float
    kosdaq_scaled: float
    hate_scaled: float


class MarketComparisonResponse(BaseModel):
    reference_date: date | None
    comparison_basis: str
    latest: MarketComparisonLatestRead
    points: list[MarketComparisonPointRead]
