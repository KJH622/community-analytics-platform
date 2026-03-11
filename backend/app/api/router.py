from fastapi import APIRouter

from app.api.routes import analytics, community, health, indicators, jobs, news
from app.politics.api import routes as politics


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(indicators.router, prefix="/api/v1/indicators", tags=["indicators"])
api_router.include_router(news.router, prefix="/api/v1/news", tags=["news"])
api_router.include_router(
    community.router, prefix="/api/v1/community", tags=["community"]
)
api_router.include_router(
    analytics.router, prefix="/api/v1/analytics", tags=["analytics"]
)
api_router.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
api_router.include_router(politics.router)
