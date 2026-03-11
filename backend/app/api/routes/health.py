from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import HealthResponse
from app.utils.dates import utcnow


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.app_env,
        timestamp=utcnow(),
    )
