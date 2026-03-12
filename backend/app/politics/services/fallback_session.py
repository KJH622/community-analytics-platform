from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _fallback_db_path() -> Path:
    return Path(__file__).resolve().parents[3] / "community_analytics.db"


@lru_cache(maxsize=1)
def _fallback_session_factory() -> sessionmaker[Session]:
    database_path = _fallback_db_path()
    engine = create_engine(f"sqlite:///{database_path.as_posix()}", future=True, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def fallback_db_available() -> bool:
    database_path = _fallback_db_path()
    return database_path.exists() and database_path.stat().st_size > 0


@contextmanager
def fallback_db_session() -> Iterator[Session]:
    session = _fallback_session_factory()()
    try:
        yield session
    finally:
        session.close()
