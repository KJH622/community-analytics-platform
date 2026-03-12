from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.models import CommunityPost
from app.politics.services.fallback_session import fallback_db_available, fallback_db_session
from app.politics.services.live_dashboard import build_politics_dashboard


def load_politics_dashboard(db: Session) -> dict:
    try:
        has_politics_posts = db.execute(
            select(CommunityPost.id).where(CommunityPost.topic_category == "politics").limit(1)
        ).scalar_one_or_none()
        if has_politics_posts is not None:
            return build_politics_dashboard(db)
    except OperationalError:
        pass

    if fallback_db_available():
        with fallback_db_session() as fallback_db:
            return build_politics_dashboard(fallback_db)

    return build_politics_dashboard(db)
