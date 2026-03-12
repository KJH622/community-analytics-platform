from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from sqlalchemy import select

from app.db.session import SessionLocal
from app.politics.analytics.rule_based import PoliticalRuleBasedAnalyzer
from app.politics.collectors.mock_politics import MockPoliticsConnector
from app.politics.models import (
    PoliticalCommunitySource,
    PoliticalDailySnapshot,
    PoliticalIndicator,
    PoliticalIndicatorValue,
    PoliticalParty,
    PoliticalPost,
    PoliticalSentiment,
    PoliticalTopic,
    Politician,
)


def seed_political_data() -> None:
    analyzer = PoliticalRuleBasedAnalyzer()
    with SessionLocal() as db:
        if db.execute(select(Politician)).first():
            return

        parties = [
            PoliticalParty(name="가상여당", country="KR", ideology="centrist", description="샘플 여당", official_color="#d94f3d"),
            PoliticalParty(name="가상야당", country="KR", ideology="reformist", description="샘플 야당", official_color="#2d61d1"),
        ]
        db.add_all(parties)
        db.flush()

        politicians = [
            Politician(name="김민준", party="가상여당", party_id=parties[0].id, position="대통령", ideology="centrist", country="KR", start_term=date(2025, 5, 10), aliases_json=["민준 대통령"]),
            Politician(name="이서현", party="가상야당", party_id=parties[1].id, position="대선 후보", ideology="reformist", country="KR", aliases_json=["서현 후보"]),
            Politician(name="박도윤", party="가상여당", party_id=parties[0].id, position="당대표", ideology="centrist", country="KR", aliases_json=[]),
        ]
        db.add_all(politicians)
        db.add_all(
            [
                PoliticalTopic(code="president", name="대통령", category="office", keywords_json=["대통령", "국정수행", "탄핵"]),
                PoliticalTopic(code="election", name="대선", category="election", keywords_json=["대선", "후보", "투표", "경선"]),
                PoliticalTopic(code="party", name="정당", category="party", keywords_json=["여당", "야당", "정당", "당대표"]),
                PoliticalTopic(code="policy", name="정책", category="policy", keywords_json=["정책", "복지", "부동산", "외교"]),
            ]
        )

        indicators = [
            PoliticalIndicator(code="president_approval", indicator_name="대통령 지지율", country="KR", source="Sample Polling Desk", unit="%"),
            PoliticalIndicator(code="party_support", indicator_name="정당 지지율", country="KR", source="Sample Polling Desk", unit="%"),
            PoliticalIndicator(code="national_performance", indicator_name="국정 수행 평가", country="KR", source="Sample Polling Desk", unit="%"),
        ]
        db.add_all(indicators)
        db.flush()

        today = date.today()
        values = []
        for offset, approval in enumerate([47.2, 46.4, 45.8, 46.9, 48.3]):
            values.append(
                PoliticalIndicatorValue(
                    indicator_id=indicators[0].id,
                    date=today - timedelta(days=offset * 7),
                    value=approval,
                    label="대통령",
                    source="Sample Polling Desk",
                    unit="%",
                )
            )
        for offset, ruling in enumerate([36.0, 35.2, 34.9, 36.7, 37.4]):
            values.append(
                PoliticalIndicatorValue(
                    indicator_id=indicators[1].id,
                    date=today - timedelta(days=offset * 7),
                    value=ruling,
                    label="가상여당",
                    source="Sample Polling Desk",
                    unit="%",
                )
            )
            values.append(
                PoliticalIndicatorValue(
                    indicator_id=indicators[1].id,
                    date=today - timedelta(days=offset * 7),
                    value=31.0 + offset,
                    label="가상야당",
                    source="Sample Polling Desk",
                    unit="%",
                )
            )
        values.append(
            PoliticalIndicatorValue(
                indicator_id=indicators[2].id,
                date=today,
                value=49.1,
                label="긍정",
                source="Sample Polling Desk",
                unit="%",
            )
        )
        db.add_all(values)

        db.add_all(
            [
                PoliticalCommunitySource(
                    code="dcinside-politics-disabled",
                    name="DCInside Politics Galleries",
                    description="정치 관련 갤러리 군. 실제 수집 전 robots.txt 및 약관 검토 필요.",
                    leaning="mixed / board-dependent",
                    link="https://www.dcinside.com/",
                    board_name="various",
                    status="disabled",
                    compliance_notes="Disabled until legal and technical review is complete.",
                    metadata_json={"source_reference": "user-provided candidate community category"},
                ),
                PoliticalCommunitySource(
                    code="fmkorea-politics-disabled",
                    name="FM Korea Politics Boards",
                    description="정치 토론 게시판 후보 소스. 실제 수집 전 사전 검토 필요.",
                    leaning="unknown",
                    link="https://www.fmkorea.com/",
                    board_name="politics",
                    status="disabled",
                    compliance_notes="Disabled pending review.",
                    metadata_json={},
                ),
                PoliticalCommunitySource(
                    code="clien-politics-disabled",
                    name="Clien Politics Boards",
                    description="정치/시사 토론 게시판 후보 소스. 실제 수집 전 사전 검토 필요.",
                    leaning="unknown",
                    link="https://www.clien.net/",
                    board_name="park",
                    status="disabled",
                    compliance_notes="Disabled pending review.",
                    metadata_json={},
                ),
            ]
        )
        db.commit()

        MockPoliticsConnector().collect(db)
        posts = db.execute(select(PoliticalPost)).scalars().all()
        names = [politician.name for politician in politicians]
        analyses = []
        for post in posts:
            result = analyzer.analyze(post.title, post.body, names)
            analyses.append(result)
            db.add(
                PoliticalSentiment(
                    post_id=post.id,
                    political_sentiment_score=result.political_sentiment_score,
                    support_score=result.support_score,
                    opposition_score=result.opposition_score,
                    anger_score=result.anger_score,
                    mockery_score=result.mockery_score,
                    political_hate_score=result.political_hate_score,
                    apathy_score=result.apathy_score,
                    enthusiasm_score=result.enthusiasm_score,
                    political_polarization_index=result.political_polarization_index,
                    election_heat_index=result.election_heat_index,
                    politician_mentions_json=result.politician_mentions,
                    keywords_json=result.keywords,
                    labels_json=result.labels,
                )
            )
        db.commit()

        keyword_counter = Counter(keyword for item in analyses for keyword in item.keywords)
        mentions_counter = Counter(name for item in analyses for name in item.politician_mentions)
        db.add(
            PoliticalDailySnapshot(
                snapshot_date=today,
                country="KR",
                political_sentiment_score=sum(item.political_sentiment_score for item in analyses) / max(1, len(analyses)),
                political_polarization_index=sum(item.political_polarization_index for item in analyses) / max(1, len(analyses)),
                election_heat_index=sum(item.election_heat_index for item in analyses) / max(1, len(analyses)),
                top_keywords_json=[word for word, _ in keyword_counter.most_common(10)],
                top_politicians_json=[name for name, _ in mentions_counter.most_common(10)],
                source_counts_json={"posts": len(posts)},
            )
        )
        db.commit()
