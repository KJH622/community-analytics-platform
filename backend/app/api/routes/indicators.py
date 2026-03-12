from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.indicator import IndicatorHistoryRead, IndicatorLatestRead, IndicatorReleaseRead
from app.services.query import get_indicator_history, get_latest_indicators

router = APIRouter(prefix="/api/v1/indicators", tags=["indicators"])


@router.get("/latest", response_model=list[IndicatorLatestRead])
def latest_indicators(db: Session = Depends(get_db)):
    items = []
    for indicator, latest_release in get_latest_indicators(db):
        items.append(
            IndicatorLatestRead(
                code=indicator.code,
                name=indicator.name,
                country=indicator.country,
                category=indicator.category,
                unit=indicator.unit,
                latest_release=IndicatorReleaseRead.model_validate(latest_release)
                if latest_release
                else None,
            )
        )
    return items


@router.get("/{indicator_code}/history", response_model=IndicatorHistoryRead)
def indicator_history(indicator_code: str, db: Session = Depends(get_db)):
    indicator, releases = get_indicator_history(db, indicator_code)
    if indicator is None:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return IndicatorHistoryRead(
        code=indicator.code,
        name=indicator.name,
        country=indicator.country,
        releases=[IndicatorReleaseRead.model_validate(release) for release in releases],
    )
