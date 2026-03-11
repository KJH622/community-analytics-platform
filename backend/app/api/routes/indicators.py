from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.indicator import EconomicIndicator
from app.schemas.indicator import IndicatorHistoryResponse, IndicatorLatestRead, IndicatorReleaseRead


router = APIRouter()


@router.get("/latest", response_model=list[IndicatorLatestRead])
def latest_indicators(
    country: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[IndicatorLatestRead]:
    query = select(EconomicIndicator).options(selectinload(EconomicIndicator.releases))
    if country:
        query = query.where(EconomicIndicator.country == country.upper())
    indicators = db.scalars(query.order_by(EconomicIndicator.code)).all()
    payload: list[IndicatorLatestRead] = []
    for indicator in indicators:
        latest_release = max(indicator.releases, key=lambda item: item.release_date) if indicator.releases else None
        payload.append(
            IndicatorLatestRead(
                id=indicator.id,
                code=indicator.code,
                name=indicator.name,
                country=indicator.country,
                category=indicator.category,
                unit=indicator.unit,
                frequency=indicator.frequency,
                source_url=indicator.source_url,
                latest_release=IndicatorReleaseRead.model_validate(latest_release) if latest_release else None,
            )
        )
    return payload


@router.get("/{indicator_code}/history", response_model=IndicatorHistoryResponse)
def indicator_history(
    indicator_code: str,
    limit: int = Query(default=60, le=365),
    db: Session = Depends(get_db),
) -> IndicatorHistoryResponse:
    indicator = db.scalar(
        select(EconomicIndicator)
        .options(selectinload(EconomicIndicator.releases))
        .where(EconomicIndicator.code == indicator_code)
    )
    if indicator is None:
        raise HTTPException(status_code=404, detail="Indicator not found")
    releases = sorted(indicator.releases, key=lambda item: item.release_date, reverse=True)[:limit]
    return IndicatorHistoryResponse(
        indicator_code=indicator.code,
        releases=[IndicatorReleaseRead.model_validate(item) for item in releases],
    )
