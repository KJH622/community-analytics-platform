from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.market import MarketComparisonResponse
from app.services.market import get_market_comparison

router = APIRouter(prefix="/api/v1/market", tags=["market"])


@router.get("/comparison", response_model=MarketComparisonResponse)
def market_comparison(
    db: Session = Depends(get_db),
    days: int = Query(default=14, ge=7, le=30),
):
    return MarketComparisonResponse.model_validate(get_market_comparison(db, days=days))
