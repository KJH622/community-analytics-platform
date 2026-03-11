from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.analytics.rule_based import RuleBasedAnalyzer
from app.analytics.snapshots import calculate_daily_snapshot
from app.db.session import SessionLocal
from app.models import (
    Article,
    CommunityPost,
    ConnectorStatus,
    EconomicIndicator,
    IndicatorRelease,
    Sentiment,
    Source,
    SourceConnector,
    SourceType,
    Topic,
)
from app.services.text_processor import anonymize_author
from app.utils.hashing import sha256_text


def seed_reference_data() -> None:
    analyzer = RuleBasedAnalyzer()
    with SessionLocal() as db:
        if db.execute(select(EconomicIndicator)).first():
            return

        db.add_all(
            [
                Topic(code="inflation", name="Inflation", category="macro", keywords_json=["cpi", "ppi", "물가"]),
                Topic(code="semiconductor", name="Semiconductor", category="equity", keywords_json=["반도체", "엔비디아"]),
                Topic(code="fx", name="FX", category="macro", keywords_json=["환율", "달러"]),
            ]
        )

        source_news = Source(
            code="seed_news",
            name="Seed News",
            source_type=SourceType.NEWS,
            country="US",
            base_url="https://example.local/news",
            is_official=False,
            compliance_notes="Seed data for local development.",
        )
        source_community = Source(
            code="seed_community",
            name="Seed Community",
            source_type=SourceType.COMMUNITY,
            country="KR",
            base_url="https://example.local/community",
            is_official=False,
            compliance_notes="Seed data for local development.",
        )
        dcinside_krstock = Source(
            code="dcinside_krstock_disabled",
            name="DCInside Korea Stock Minor Gallery",
            source_type=SourceType.COMMUNITY,
            country="KR",
            base_url="https://gall.dcinside.com/mgallery/board/lists/?id=krstock",
            is_official=False,
            is_active=False,
            compliance_notes=(
                "Disabled. DCInside robots.txt currently disallows automated crawling for general agents. "
                "Do not enable without renewed legal and technical review."
            ),
            metadata_json={
                "board_id": "krstock",
                "board_name": "krstock",
                "status": "disabled",
                "reason": "robots_disallow",
            },
        )
        dcinside_stockus = Source(
            code="dcinside_stockus_disabled",
            name="DCInside US Stock Minor Gallery",
            source_type=SourceType.COMMUNITY,
            country="KR",
            base_url="https://gall.dcinside.com/mgallery/board/lists?id=stockus",
            is_official=False,
            is_active=False,
            compliance_notes=(
                "Disabled. DCInside robots.txt currently disallows automated crawling for general agents. "
                "Do not enable without renewed legal and technical review."
            ),
            metadata_json={
                "board_id": "stockus",
                "board_name": "stockus",
                "status": "disabled",
                "reason": "robots_disallow",
            },
        )
        db.add_all([source_news, source_community, dcinside_krstock, dcinside_stockus])
        db.flush()

        db.add_all(
            [
                SourceConnector(
                    source_id=dcinside_krstock.id,
                    name="dcinside_krstock_connector",
                    connector_type="community",
                    status=ConnectorStatus.DISABLED,
                    schedule_cron=None,
                    rate_limit_per_minute=0,
                    timeout_seconds=20,
                    config_json={
                        "board_id": "krstock",
                        "target_url": "https://gall.dcinside.com/mgallery/board/lists/?id=krstock",
                        "enabled": False,
                        "reason": "robots_disallow",
                    },
                ),
                SourceConnector(
                    source_id=dcinside_stockus.id,
                    name="dcinside_stockus_connector",
                    connector_type="community",
                    status=ConnectorStatus.DISABLED,
                    schedule_cron=None,
                    rate_limit_per_minute=0,
                    timeout_seconds=20,
                    config_json={
                        "board_id": "stockus",
                        "target_url": "https://gall.dcinside.com/mgallery/board/lists?id=stockus",
                        "enabled": False,
                        "reason": "robots_disallow",
                    },
                ),
            ]
        )

        cpi = EconomicIndicator(
            code="CPIAUCSL",
            name="Consumer Price Index",
            country="US",
            category="inflation",
            unit="index",
            frequency="monthly",
            importance=5,
        )
        usdkrw = EconomicIndicator(
            code="USDKRW",
            name="USD/KRW Exchange Rate",
            country="KR",
            category="fx",
            unit="KRW",
            frequency="daily",
            importance=4,
        )
        db.add_all([cpi, usdkrw])
        db.flush()

        now = datetime.now(tz=timezone.utc)
        db.add_all(
            [
                IndicatorRelease(
                    indicator_id=cpi.id,
                    country="US",
                    release_date=date.today() - timedelta(days=30),
                    release_time=None,
                    actual_value=312.5,
                    forecast_value=311.9,
                    previous_value=310.8,
                    unit="index",
                    importance=5,
                    source_url="https://fred.stlouisfed.org/",
                    released_at=now - timedelta(days=30),
                    metadata_json={},
                ),
                IndicatorRelease(
                    indicator_id=usdkrw.id,
                    country="KR",
                    release_date=date.today(),
                    release_time=None,
                    actual_value=1332.4,
                    forecast_value=None,
                    previous_value=1327.1,
                    unit="KRW",
                    importance=4,
                    source_url="https://www.frankfurter.app/",
                    released_at=now,
                    metadata_json={},
                ),
            ]
        )

        article = Article(
            source_id=source_news.id,
            cluster_id=None,
            title="미국 CPI 둔화 기대 속 나스닥 반등",
            body="CPI 둔화 기대와 반도체 강세가 겹치며 나스닥이 반등했다.",
            summary="CPI 둔화 기대와 반도체 강세",
            author="seed",
            publisher="Seed Desk",
            canonical_url="https://example.local/news/1",
            original_url="https://example.local/news/1",
            language="ko",
            category="markets",
            tags_json=["cpi", "나스닥", "반도체"],
            title_hash=sha256_text("미국 CPI 둔화 기대 속 나스닥 반등"),
            body_hash=sha256_text("CPI 둔화 기대와 반도체 강세가 겹치며 나스닥이 반등했다."),
            published_at=now - timedelta(hours=3),
            raw_payload={},
        )
        post = CommunityPost(
            source_id=source_community.id,
            board_name="demo-market-board",
            external_post_id="seed-post-1",
            title="지금은 관망이 맞나 아니면 반도체 계속 간다?",
            body="엔비디아는 강한데 너무 과열 같기도 해서 긴가민가하다.",
            created_at=now - timedelta(hours=2),
            author_hash=anonymize_author("seed-user"),
            view_count=804,
            upvotes=24,
            downvotes=4,
            comment_count=9,
            original_url="https://example.local/community/1",
            raw_payload={},
        )
        db.add_all([article, post])
        db.flush()

        for document_type, row in [("article", article), ("community_post", post)]:
            analysis = analyzer.analyze(row.title, row.body)
            db.add(
                Sentiment(
                    document_type=document_type,
                    document_id=row.id,
                    sentiment_score=analysis.sentiment_score,
                    fear_greed_score=analysis.fear_greed_score,
                    hate_index=analysis.hate_index,
                    uncertainty_score=analysis.uncertainty_score,
                    market_bias=analysis.market_bias,
                    keywords_json=analysis.keywords,
                    entities_json=analysis.entities,
                    topics_json=analysis.topics,
                )
            )
        db.commit()
        calculate_daily_snapshot(db, date.today())
