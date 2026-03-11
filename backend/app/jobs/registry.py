from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.analytics.snapshots import upsert_daily_snapshot
from app.collectors.communities.dcinside_connector import DcInsideConnector, DcInsideGalleryConfig
from app.collectors.communities.mock_connector import MockCommunityConnector
from app.collectors.indicators.bls import BlsIndicatorCollector
from app.collectors.indicators.fred import FredMarketSeriesCollector
from app.collectors.news.rss import RssNewsCollector
from app.core.config import get_settings
from app.models.ingestion import IngestionJob, IngestionLog
from app.politics.collectors.dcinside import DcInsidePoliticalConnector
from app.politics.collectors.mock_sources import (
    MockPoliticalCommunityConnector,
    MockPoliticalIndicatorCollector,
)
from app.politics.services.storage import (
    analyze_and_store_political_post,
    ensure_political_source,
    update_political_daily_snapshot,
    upsert_political_indicator_value,
    upsert_political_post,
)
from app.services.analysis_service import AnalysisService
from app.services.storage import (
    ensure_source_connector,
    get_or_create_source,
    upsert_article,
    upsert_community_post,
    upsert_indicator_release,
)


logger = logging.getLogger(__name__)


MARKET_GALLERIES = [
    {
        "code": "dcinside_stockus",
        "name": "DCInside 미국 주식 마이너 갤러리",
        "gallery_id": "stockus",
        "board_name": "미국 주식 마이너 갤러리",
        "base_url": "https://gall.dcinside.com/mgallery/board/lists/?id=stockus",
    },
    {
        "code": "dcinside_nasdaq",
        "name": "DCInside 나스닥 마이너 갤러리",
        "gallery_id": "nasdaq",
        "board_name": "나스닥 마이너 갤러리",
        "base_url": "https://gall.dcinside.com/mgallery/board/lists/?id=nasdaq",
    },
]

POLITICAL_GALLERIES = [
    {
        "code": "dcinside_leejaemyung_politics",
        "name": "DCInside 이재명 마이너 갤러리",
        "gallery_id": "leejaemyung",
        "board_name": "이재명 마이너 갤러리",
        "base_url": "https://gall.dcinside.com/mgallery/board/lists/?id=leejaemyung",
    },
    {
        "code": "dcinside_conservative_politics",
        "name": "DCInside 보수주의 마이너 갤러리",
        "gallery_id": "conservative",
        "board_name": "보수주의 마이너 갤러리",
        "base_url": "https://gall.dcinside.com/mgallery/board/lists/?id=conservative",
    },
]


def collect_indicators(db: Session, job: IngestionJob) -> None:
    sources = {
        "bls": get_or_create_source(
            db,
            code="bls",
            name="US Bureau of Labor Statistics",
            kind="indicator",
            country="US",
            base_url="https://www.bls.gov/",
        ),
        "fred": get_or_create_source(
            db,
            code="fred",
            name="FRED",
            kind="indicator",
            country="US",
            base_url="https://fred.stlouisfed.org/",
        ),
    }
    ensure_source_connector(
        db,
        sources["bls"],
        connector_type="bls_api",
        status="active",
        schedule_hint="0 */6 * * *",
        rate_limit_per_minute=30,
    )
    ensure_source_connector(
        db,
        sources["fred"],
        connector_type="fred_csv",
        status="active",
        schedule_hint="0 */2 * * *",
        rate_limit_per_minute=60,
    )
    collectors = [
        (sources["bls"], BlsIndicatorCollector()),
        (sources["fred"], FredMarketSeriesCollector()),
    ]
    for source, collector in collectors:
        releases = list(collector.fetch())
        job.items_seen += len(releases)
        for release in releases:
            upsert_indicator_release(db, source, release)
            job.items_written += 1
        db.add(IngestionLog(job_id=job.id, level="INFO", message=f"Ingested {collector.collector_name}"))
    db.commit()


def collect_news(db: Session, job: IngestionJob) -> None:
    settings = get_settings()
    configs = [
        {
            "code": "nasdaq_markets",
            "name": "Nasdaq Markets RSS",
            "feed_url": settings.nasdaq_markets_rss,
            "category": "markets",
        },
        {
            "code": "nasdaq_stocks",
            "name": "Nasdaq Stocks RSS",
            "feed_url": settings.nasdaq_stocks_rss,
            "category": "stocks",
        },
    ]
    analysis_service = AnalysisService()
    for config in configs:
        source = get_or_create_source(
            db,
            code=config["code"],
            name=config["name"],
            kind="news",
            country="US",
            base_url="https://www.nasdaq.com/",
        )
        ensure_source_connector(
            db,
            source,
            connector_type="rss",
            status="active",
            schedule_hint="*/30 * * * *",
            rate_limit_per_minute=30,
        )
        collector = RssNewsCollector(
            feed_url=config["feed_url"], source_code=config["code"], category=config["category"]
        )
        articles = list(collector.fetch())
        job.items_seen += len(articles)
        for article_payload in articles:
            article, created = upsert_article(db, source, article_payload)
            if created:
                job.items_written += 1
            else:
                job.items_skipped += 1
            analysis_service.analyze_document(
                db, "article", article.id, article.title, article.body or article.summary
            )
        db.add(
            IngestionLog(
                job_id=job.id,
                level="INFO",
                message=f"Ingested RSS feed {config['code']}",
            )
        )
    db.commit()


def collect_mock_community(db: Session, job: IngestionJob) -> None:
    settings = get_settings()
    source = get_or_create_source(
        db,
        code="mock_community",
        name="Mock Community Connector",
        kind="community",
        country="KR",
        base_url="https://community.local/",
        enabled=settings.mock_community_connector_enabled,
        robots_policy="local fixture only",
        tos_notes="Safe mock connector. Replace with real connector only after legal review.",
    )
    ensure_source_connector(
        db,
        source,
        connector_type="mock_fixture",
        status="active" if settings.mock_community_connector_enabled else "disabled",
        schedule_hint="0 * * * *",
        rate_limit_per_minute=120,
        legal_notes="Development-only safe fixture connector.",
    )
    collector = MockCommunityConnector()
    analysis_service = AnalysisService()
    posts = list(collector.fetch())
    job.items_seen += len(posts)
    for post_payload in posts:
        post, created = upsert_community_post(db, source, post_payload)
        if created:
            job.items_written += 1
        else:
            job.items_skipped += 1
        analysis_service.analyze_document(db, "community_post", post.id, post.title, post.body)
    db.add(IngestionLog(job_id=job.id, level="INFO", message="Ingested mock community posts"))
    db.commit()


def collect_dcinside_market(db: Session, job: IngestionJob) -> None:
    analysis_service = AnalysisService()
    collected_galleries = 0

    for config in MARKET_GALLERIES:
        source = get_or_create_source(
            db,
            code=config["code"],
            name=config["name"],
            kind="community",
            country="KR",
            base_url=config["base_url"],
            enabled=True,
            robots_policy=(
                "Allowlisted public list/view pages only. Re-check robots.txt before broadening scope."
            ),
            tos_notes=(
                "Use only publicly reachable gallery pages. Disable this connector immediately if "
                "robots.txt or terms of service change."
            ),
        )
        ensure_source_connector(
            db,
            source,
            connector_type="dcinside_gallery",
            status="active",
            schedule_hint="*/30 * * * *",
            rate_limit_per_minute=20,
            legal_notes=(
                "Public allowlisted gallery pages only. No login, no private endpoints, no bypassing."
            ),
        )

        collector = DcInsideConnector(
            DcInsideGalleryConfig(
                gallery_id=config["gallery_id"],
                board_name=config["board_name"],
                community_name="디시인사이드",
                max_pages=3,
                limit=18,
            )
        )

        try:
            posts = list(collector.fetch())
        except Exception as exc:
            db.add(
                IngestionLog(
                    job_id=job.id,
                    level="WARNING",
                    message=f"{config['name']} 수집 실패",
                    context={"error": str(exc), "source_code": config["code"]},
                )
            )
            continue

        collected_galleries += 1
        job.items_seen += len(posts)
        for payload in posts:
            post, created = upsert_community_post(db, source, payload)
            if created:
                job.items_written += 1
            else:
                job.items_skipped += 1
            analysis_service.analyze_document(db, "community_post", post.id, post.title, post.body)

        db.add(
            IngestionLog(
                job_id=job.id,
                level="INFO",
                message=f"{config['name']} 공개 게시글 {len(posts)}건 수집",
                context={"source_code": config["code"]},
            )
        )

    if collected_galleries == 0:
        raise RuntimeError("No allowlisted DCInside market galleries could be collected.")
    db.commit()


def compute_daily_snapshots(db: Session, job: IngestionJob) -> None:
    for offset in range(3):
        snapshot_date = date.today() - timedelta(days=offset)
        upsert_daily_snapshot(db, snapshot_date, source_kind="all")
        upsert_daily_snapshot(db, snapshot_date, source_kind="community")
    job.items_seen = 6
    job.items_written = 6
    db.add(
        IngestionLog(
            job_id=job.id,
            level="INFO",
            message="Updated daily sentiment snapshots for today, yesterday, and two days ago",
        )
    )
    db.commit()


def collect_political_indicators(db: Session, job: IngestionJob) -> None:
    source = ensure_political_source(
        db,
        code="politics_mock_poll",
        name="정치 지표 시드 데이터",
        base_url="https://politics.local/polls",
    )
    ensure_source_connector(
        db,
        source,
        connector_type="mock_political_indicator",
        status="active",
        schedule_hint="0 6 * * *",
        rate_limit_per_minute=120,
        legal_notes="Fixture-backed political indicator source for MVP.",
    )
    collector = MockPoliticalIndicatorCollector()
    values = collector.fetch()
    job.items_seen += len(values)
    for value in values:
        upsert_political_indicator_value(db, value)
        job.items_written += 1
    db.add(IngestionLog(job_id=job.id, level="INFO", message="Ingested mock political indicators"))
    db.commit()


def collect_political_posts(db: Session, job: IngestionJob) -> None:
    source = ensure_political_source(
        db,
        code="politics_mock",
        name="Mock Political Community",
        base_url="https://politics.local/",
    )
    ensure_source_connector(
        db,
        source,
        connector_type="mock_political_community",
        status="active",
        schedule_hint="0 */2 * * *",
        rate_limit_per_minute=120,
        legal_notes="Local fixture connector. Real communities remain disabled until reviewed.",
    )
    collector = MockPoliticalCommunityConnector()
    posts = list(collector.fetch())
    job.items_seen += len(posts)
    for payload in posts:
        post = upsert_political_post(db, source, payload)
        analyze_and_store_political_post(db, post)
        job.items_written += 1
    db.add(IngestionLog(job_id=job.id, level="INFO", message="Ingested mock political posts"))
    db.commit()


def collect_dcinside_political_posts(db: Session, job: IngestionJob) -> None:
    collected_galleries = 0

    for config in POLITICAL_GALLERIES:
        source = ensure_political_source(
            db,
            code=config["code"],
            name=config["name"],
            base_url=config["base_url"],
        )
        ensure_source_connector(
            db,
            source,
            connector_type="dcinside_political_gallery",
            status="active",
            schedule_hint="*/30 * * * *",
            rate_limit_per_minute=20,
            legal_notes=(
                "Public allowlisted gallery pages only. Respect robots.txt and terms of service on every run."
            ),
        )
        collector = DcInsidePoliticalConnector(
            gallery_id=config["gallery_id"],
            board_name=config["board_name"],
            limit=18,
            max_pages=3,
        )

        try:
            posts = list(collector.fetch())
        except Exception as exc:
            db.add(
                IngestionLog(
                    job_id=job.id,
                    level="WARNING",
                    message=f"{config['name']} 수집 실패",
                    context={"error": str(exc), "source_code": config["code"]},
                )
            )
            continue

        collected_galleries += 1
        job.items_seen += len(posts)
        for payload in posts:
            post = upsert_political_post(db, source, payload)
            analyze_and_store_political_post(db, post)
            job.items_written += 1

        db.add(
            IngestionLog(
                job_id=job.id,
                level="INFO",
                message=f"{config['name']} 공개 정치글 {len(posts)}건 수집",
                context={"source_code": config["code"]},
            )
        )

    if collected_galleries == 0:
        raise RuntimeError("No allowlisted DCInside political galleries could be collected.")
    db.commit()


def compute_political_daily_snapshots(db: Session, job: IngestionJob) -> None:
    for offset in range(3):
        snapshot_date = date.today() - timedelta(days=offset)
        update_political_daily_snapshot(db, snapshot_date)
    job.items_seen = 3
    job.items_written = 3
    db.add(
        IngestionLog(
            job_id=job.id,
            level="INFO",
            message="Updated political daily snapshots for today, yesterday, and two days ago",
        )
    )
    db.commit()


JOB_REGISTRY = {
    "collect_indicators": collect_indicators,
    "collect_news": collect_news,
    "collect_mock_community": collect_mock_community,
    "collect_dcinside_market": collect_dcinside_market,
    "compute_daily_snapshots": compute_daily_snapshots,
    "collect_political_indicators": collect_political_indicators,
    "collect_political_posts": collect_political_posts,
    "collect_dcinside_political_posts": collect_dcinside_political_posts,
    "compute_political_daily_snapshots": compute_political_daily_snapshots,
}
