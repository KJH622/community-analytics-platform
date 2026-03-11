from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import dc_api
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import CommunityPost, Source, SourceType
from app.services.community_analysis import CommunityAnalysisService
from app.services.text_processor import anonymize_author
from app.utils.text import clean_text

SEOUL = ZoneInfo("Asia/Seoul")


@dataclass(slots=True)
class HistoricalPost:
    external_post_id: str
    title: str
    body: str
    author: str | None
    created_at: datetime
    view_count: int | None
    upvotes: int | None
    comment_count: int | None
    original_url: str
    raw_payload: dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import historical DCInside stockus concept posts.")
    parser.add_argument("--board-id", default="stockus")
    parser.add_argument("--board-name", default="stockus-concept")
    parser.add_argument("--since", default="2026-03-04", help="Inclusive start date in YYYY-MM-DD (Asia/Seoul).")
    parser.add_argument("--limit", type=int, default=0, help="Optional maximum number of posts to import.")
    parser.add_argument("--skip-analysis", action="store_true", help="Store posts without recalculating analysis.")
    parser.add_argument("--after-post-id", type=int, default=0, help="Only fetch posts newer than this numeric post id.")
    parser.add_argument("--sleep-seconds", type=float, default=2.0, help="Sleep between detail fetches.")
    return parser.parse_args()


def coerce_kst(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=SEOUL)
    return value.astimezone(SEOUL)


async def fetch_history(
    board_id: str,
    since_dt: datetime,
    limit: int = 0,
    *,
    after_post_id: int = 0,
    sleep_seconds: float = 2.0,
) -> list[HistoricalPost]:
    api = dc_api.API()
    collected: list[HistoricalPost] = []

    try:
        async for item in api.board(board_id, num=-1, recommend=True):
            numeric_post_id = int(item.id)
            if after_post_id and numeric_post_id <= after_post_id:
                break

            created_at = coerce_kst(item.time)
            if created_at < since_dt:
                break

            document = await item.document()
            if document is None:
                body = item.title
                view_count = item.view_count
                upvotes = item.voteup_count
                author = item.author
            else:
                body = document.contents or item.title
                view_count = document.view_count
                upvotes = document.voteup_count
                author = document.author_id or document.author

            post = HistoricalPost(
                external_post_id=f"{board_id}:{item.id}",
                title=clean_text(item.title),
                body=clean_text(body),
                author=clean_text(author) if author else None,
                created_at=created_at.astimezone(UTC),
                view_count=view_count,
                upvotes=upvotes,
                comment_count=item.comment_count,
                original_url=f"https://m.dcinside.com/board/{board_id}/{item.id}",
                raw_payload={
                    "board_id": board_id,
                    "external_post_id": f"{board_id}:{item.id}",
                    "title": item.title,
                    "body": body,
                    "author": author,
                    "created_at": created_at.isoformat(),
                    "view_count": view_count,
                    "upvotes": upvotes,
                    "comment_count": item.comment_count,
                    "subject": item.subject,
                    "original_url": f"https://m.dcinside.com/board/{board_id}/{item.id}",
                    "source": "dc_api_mobile",
                },
            )
            collected.append(post)
            if limit and len(collected) >= limit:
                break
            if sleep_seconds > 0:
                await asyncio.sleep(sleep_seconds)
    finally:
        await api.close()

    return collected


def upsert_history(posts: list[HistoricalPost], board_name: str, *, skip_analysis: bool = False) -> tuple[int, int]:
    analysis_service = CommunityAnalysisService()
    inserted = 0
    updated = 0

    with SessionLocal() as db:
        source = db.execute(select(Source).where(Source.code == "dcinside")).scalar_one_or_none()
        if source is None:
            source = Source(
                code="dcinside",
                name="DCInside Galleries",
                source_type=SourceType.COMMUNITY,
                country="KR",
                base_url="https://gall.dcinside.com",
                is_official=False,
                compliance_notes="Public gallery pages and mobile pages only.",
                metadata_json={"boards": [{"id": "stockus", "board_name": board_name}]},
            )
            db.add(source)
            db.flush()

        for item in posts:
            existing = db.execute(
                select(CommunityPost).where(
                    CommunityPost.source_id == source.id,
                    CommunityPost.external_post_id == item.external_post_id,
                )
            ).scalar_one_or_none()

            if existing is None:
                existing = CommunityPost(
                    source_id=source.id,
                    board_name=board_name,
                    external_post_id=item.external_post_id,
                    title=item.title,
                    body=item.body,
                    created_at=item.created_at,
                    author_hash=anonymize_author(item.author),
                    view_count=item.view_count,
                    upvotes=item.upvotes,
                    downvotes=None,
                    comment_count=item.comment_count,
                    original_url=item.original_url,
                    raw_payload=item.raw_payload,
                )
                db.add(existing)
                db.flush()
                inserted += 1
            else:
                existing.board_name = board_name
                existing.title = item.title
                existing.body = item.body
                existing.created_at = item.created_at
                existing.author_hash = anonymize_author(item.author)
                existing.view_count = item.view_count
                existing.upvotes = item.upvotes
                existing.comment_count = item.comment_count
                existing.original_url = item.original_url
                existing.raw_payload = item.raw_payload
                db.flush()
                updated += 1

            if not skip_analysis:
                analysis_service.persist_post_analysis(db, existing)

        db.commit()

    return inserted, updated


def main() -> None:
    args = parse_args()
    since_dt = datetime.fromisoformat(args.since).replace(tzinfo=SEOUL)
    posts = asyncio.run(
        fetch_history(
            args.board_id,
            since_dt,
            limit=args.limit,
            after_post_id=args.after_post_id,
            sleep_seconds=max(args.sleep_seconds, 2.0),
        )
    )
    inserted, updated = upsert_history(posts, args.board_name, skip_analysis=args.skip_analysis)
    print(
        {
            "fetched": len(posts),
            "inserted": inserted,
            "updated": updated,
            "since": args.since,
            "board_id": args.board_id,
            "board_name": args.board_name,
        }
    )


if __name__ == "__main__":
    main()
