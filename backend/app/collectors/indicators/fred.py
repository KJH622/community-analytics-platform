from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import datetime
from io import StringIO

from app.collectors.base.base import BaseCollector
from app.collectors.base.types import NormalizedIndicator, NormalizedIndicatorRelease
from app.core.config import get_settings


FRED_SERIES = [
    {
        "series_id": "VIXCLS",
        "code": "US_VIX",
        "name": "CBOE Volatility Index",
        "country": "US",
        "category": "volatility",
        "unit": "index",
        "frequency": "daily",
        "description": "VIX daily close from FRED",
    },
    {
        "series_id": "DGS10",
        "code": "US_10Y_TREASURY",
        "name": "10-Year Treasury Constant Maturity Rate",
        "country": "US",
        "category": "rates",
        "unit": "%",
        "frequency": "daily",
        "description": "10-Year Treasury yield from FRED",
    },
]


class FredMarketSeriesCollector(BaseCollector):
    collector_name = "fred-market-series"

    def fetch(self) -> Iterable[NormalizedIndicatorRelease]:
        settings = get_settings()
        normalized: list[NormalizedIndicatorRelease] = []
        for series in FRED_SERIES:
            csv_text = self.get_text(
                settings.fred_series_base_url,
                params={"id": series["series_id"], "cosd": "2024-01-01"},
            )
            normalized.extend(self._parse_csv(series, csv_text))
        return normalized

    def _parse_csv(
        self, series: dict[str, str], csv_text: str
    ) -> list[NormalizedIndicatorRelease]:
        indicator = NormalizedIndicator(
            code=series["code"],
            name=series["name"],
            country=series["country"],
            category=series["category"],
            unit=series["unit"],
            frequency=series["frequency"],
            description=series["description"],
            source_url=f"https://fred.stlouisfed.org/series/{series['series_id']}",
        )
        rows = csv.DictReader(StringIO(csv_text))
        releases: list[NormalizedIndicatorRelease] = []
        previous_value: float | None = None
        for row in rows:
            value = row.get(series["series_id"])
            if not value or value == ".":
                continue
            release_date = datetime.strptime(row["DATE"], "%Y-%m-%d").date()
            actual_value = float(value)
            releases.append(
                NormalizedIndicatorRelease(
                    indicator=indicator,
                    release_date=release_date,
                    release_time=None,
                    actual_value=actual_value,
                    forecast_value=None,
                    previous_value=previous_value,
                    unit=series["unit"],
                    importance=3,
                    country=series["country"],
                    source_url=indicator.source_url,
                )
            )
            previous_value = actual_value
        return releases
