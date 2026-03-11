from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.analytics import router as analytics_router
from app.api.routes.community import router as community_router
from app.api.routes.health import router as health_router
from app.api.routes.indicators import router as indicators_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.news import router as news_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine
from app.jobs.scheduler import build_scheduler
from app.politics.api.routes.politics import router as politics_router
from app.politics.services.seed import seed_political_data
from app.services.seed import seed_reference_data

settings = get_settings()
scheduler = build_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    Base.metadata.create_all(bind=engine)
    if settings.seed_demo_data:
        seed_reference_data()
        seed_political_data()
    if settings.scheduler_enabled and not scheduler.running:
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(title="Market Signal Hub API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(indicators_router)
app.include_router(news_router)
app.include_router(community_router)
app.include_router(analytics_router)
app.include_router(jobs_router)
app.include_router(politics_router)
