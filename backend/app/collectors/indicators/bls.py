from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from app.collectors.base.base import BaseCollector
from app.collectors.base.types import NormalizedIndicator, NormalizedIndicatorRelease
from app.core.config import get_settings


BLS_SERIES = [
    {
        "series_id": "CUUR0000SA0",
        "code": "US_CPI_ALL_ITEMS",
        "name": "US CPI All Items",
        "country": "US",
        "category": "inflation",
        "unit": "index",
        "frequency": "monthly",
        "description": "Consumer Price Index for All Urban Consumers: All Items",
        "source_url": "https://download.bls.gov/pub/time.series/cu/",
    },
    {
        "series_id": "LNS14000000",
        "code": "US_UNEMPLOYMENT_RATE",
        "name": "US Unemployment Rate",
        "country": "US",
        "category": "labor",
        "unit": "%",
        "frequency": "monthly",
        "description": "Employment status of the civilian population: unemployment rate",
        "source_url": "https://download.bls.gov/pub/time.series/ln/",
    },
]


class BlsIndicatorCollector(BaseCollector):
    collector_name = "bls-indicators"

    def fetch(self) -> Iterable[NormalizedIndicatorRelease]:
        settings = get_settings()
        series_ids = [series["series_id"] for series in BLS_SERIES]
        payload = {
            "seriesid": series_ids,
            "startyear": str(date.today().year - 2),
            "endyear": str(date.today().year),
            "catalog": False,
            "calculations": False,
            "annualaverage": False,
        }
        response = self.get_json(settings.bls_api_url, json=payload)
        series_lookup = {item["series_id"]: item for item in BLS_SERIES}
        normalized: list[NormalizedIndicatorRelease] = []
        for series in response.get("Results", {}).get("series", []):
            config = series_lookup.get(series["seriesID"])
            if not config:
                continue
            indicator = NormalizedIndicator(
                code=config["code"],
                name=config["name"],
                country=config["country"],
                category=config["category"],
                unit=config["unit"],
                frequency=config["frequency"],
                description=config["description"],
                source_url=config["source_url"],
            )
            previous_value: float | None = None
            ordered_points = sorted(
                (point for point in series.get("data", []) if point.get("period", "").startswith("M")),
                key=lambda item: (int(item["year"]), int(item["period"][1:])),
            )
            for point in ordered_points:
                period = point.get("period", "")
                month = int(period[1:])
                release_date = date(int(point["year"]), month, 1)
                actual_value = float(point["value"])
                normalized.append(
                    NormalizedIndicatorRelease(
                        indicator=indicator,
                        release_date=release_date,
                        release_time=None,
                        actual_value=actual_value,
                        forecast_value=None,
                        previous_value=previous_value,
                        unit=config["unit"],
                        importance=4 if config["category"] == "inflation" else 5,
                        country=config["country"],
                        source_url=config["source_url"],
                    )
                )
                previous_value = actual_value
        return normalized
