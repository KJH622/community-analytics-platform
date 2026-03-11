from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.analytics import router as analytics_router
from app.api.routes.community import router as community_router
from app.api.routes.health import router as health_router
from app.api.routes.indicators import router as indicators_router
from app.api.routes.news import router as news_router
from app.db.base import Base
from app.models import *  # noqa: F403
from app.politics.api.routes.politics import router as politics_router
from app.politics.models import *  # noqa: F403


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def api_client(db_session: Session) -> Generator[TestClient, None, None]:
    from app.api.deps import get_db

    app = FastAPI()
    app.include_router(health_router)
    app.include_router(indicators_router)
    app.include_router(news_router)
    app.include_router(community_router)
    app.include_router(analytics_router)
    app.include_router(politics_router)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
