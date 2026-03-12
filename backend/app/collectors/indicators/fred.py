from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base.contracts import BaseCollector, CollectorResult
from app.models import EconomicIndicator, IndicatorRelease

FRED_SERIES = {
    "CPIAUCSL": {
        "name": "Consumer Price Index",
        "country": "US",
        "category": "inflation",
        "unit": "index",
        "frequency": "monthly",
        "importance": 5,
    },
    "UNRATE": {
        "name": "Unemployment Rate",
        "country": "US",
        "category": "labor",
        "unit": "%",
        "frequency": "monthly",
        "importance": 5,
    },
}


class FredIndicatorCollector(BaseCollector):
    base_url = "https://api.stlouisfed.org/fred/series/observations"

    def collect(self, db: Session) -> CollectorResult:
        if not self.settings.fred_api_key:
            return CollectorResult(
                name="fred_indicators",
                message="FRED API key is not configured. Collector skipped.",
            )

        processed = 0
        for series_id, meta in FRED_SERIES.items():
            indicator = db.execute(
                select(EconomicIndicator).where(
                    EconomicIndicator.code == series_id,
                    EconomicIndicator.country == meta["country"],
                )
            ).scalar_one_or_none()
            if indicator is None:
                indicator = EconomicIndicator(code=series_id, **meta)
                db.add(indicator)
                db.flush()

            response = self.get(
                self.base_url,
                params={
                    "series_id": series_id,
                    "api_key": self.settings.fred_api_key,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 12,
                },
            )
            payload = response.json()
            for obs in payload.get("observations", []):
                if obs.get("value") in {".", None}:
                    continue
                release_date = datetime.strptime(obs["date"], "%Y-%m-%d").date()
                exists = db.execute(
                    select(IndicatorRelease).where(
                        IndicatorRelease.indicator_id == indicator.id,
                        IndicatorRelease.country == meta["country"],
                        IndicatorRelease.release_date == release_date,
                    )
                ).scalar_one_or_none()
                if exists:
                    continue
                db.add(
                    IndicatorRelease(
                        indicator_id=indicator.id,
                        country=meta["country"],
                        release_date=release_date,
                        release_time=None,
                        actual_value=float(obs["value"]),
                        forecast_value=None,
                        previous_value=None,
                        unit=meta["unit"],
                        importance=meta["importance"],
                        source_url="https://fred.stlouisfed.org/",
                        released_at=datetime.combine(release_date, datetime.min.time()),
                        metadata_json={"series_id": series_id},
                    )
                )
                processed += 1
        db.commit()
        return CollectorResult(
            name="fred_indicators",
            records_processed=processed,
            message=f"Stored {processed} indicator releases.",
        )
