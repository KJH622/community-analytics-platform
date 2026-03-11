from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base.contracts import BaseCollector, CollectorResult
from app.models import EconomicIndicator, IndicatorRelease


class FrankfurterFxCollector(BaseCollector):
    base_url = "https://api.frankfurter.app/latest"

    def collect(self, db: Session) -> CollectorResult:
        indicator = db.execute(
            select(EconomicIndicator).where(
                EconomicIndicator.code == "USDKRW",
                EconomicIndicator.country == "KR",
            )
        ).scalar_one_or_none()
        if indicator is None:
            indicator = EconomicIndicator(
                code="USDKRW",
                name="USD/KRW Exchange Rate",
                country="KR",
                category="fx",
                unit="KRW",
                frequency="daily",
                importance=4,
                description="ECB reference rate based public exchange rate snapshot.",
            )
            db.add(indicator)
            db.flush()

        response = self.get(self.base_url, params={"from": "USD", "to": "KRW"})
        payload = response.json()
        release_date = datetime.strptime(payload["date"], "%Y-%m-%d").date()
        exists = db.execute(
            select(IndicatorRelease).where(
                IndicatorRelease.indicator_id == indicator.id,
                IndicatorRelease.release_date == release_date,
                IndicatorRelease.country == "KR",
            )
        ).scalar_one_or_none()
        if exists:
            return CollectorResult(name="frankfurter_fx", message="FX release already stored.")

        db.add(
            IndicatorRelease(
                indicator_id=indicator.id,
                country="KR",
                release_date=release_date,
                release_time=None,
                actual_value=float(payload["rates"]["KRW"]),
                forecast_value=None,
                previous_value=None,
                unit="KRW",
                importance=4,
                source_url="https://www.frankfurter.app/",
                released_at=datetime.combine(release_date, datetime.min.time()),
                metadata_json={"provider": "Frankfurter"},
            )
        )
        db.commit()
        return CollectorResult(name="frankfurter_fx", records_processed=1, message="Stored USD/KRW rate.")
