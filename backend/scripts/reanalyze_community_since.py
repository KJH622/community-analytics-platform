from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import CommunityPost
from app.services.community_analysis import CommunityAnalysisService

SEOUL = ZoneInfo("Asia/Seoul")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reanalyze community posts since a given date.")
    parser.add_argument("--since", required=True, help="Inclusive start date in YYYY-MM-DD (Asia/Seoul).")
    parser.add_argument("--board-name", default="stockus-concept")
    parser.add_argument("--batch-size", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    since_dt = datetime.fromisoformat(args.since).replace(tzinfo=SEOUL).astimezone(ZoneInfo("UTC"))
    service = CommunityAnalysisService()

    with SessionLocal() as db:
        posts = db.execute(
            select(CommunityPost)
            .where(CommunityPost.board_name == args.board_name, CommunityPost.created_at >= since_dt)
            .order_by(CommunityPost.created_at.asc())
        ).scalars().all()

        processed = 0
        total = len(posts)
        for post in posts:
            service.persist_post_analysis(db, post)
            processed += 1
            if processed % args.batch_size == 0:
                db.commit()
                print({"processed": processed, "total": total, "last_post_id": post.id}, flush=True)

        db.commit()
        print({"processed": processed, "total": total, "status": "done"}, flush=True)


if __name__ == "__main__":
    main()
