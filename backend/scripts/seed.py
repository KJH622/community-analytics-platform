from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.session import SessionLocal
from app.jobs.runner import run_job
from app.models.reference import Entity, Topic
from app.politics.models.tables import PoliticalParty, PoliticalTopic, Politician


TOPICS = [
    ("rates", "금리", "기준금리와 국채금리 이슈", ["금리", "fomc", "fed"]),
    ("inflation", "물가", "CPI와 PPI 등 물가 이슈", ["cpi", "ppi", "물가"]),
    ("fx", "환율", "원달러 환율과 달러 흐름", ["환율", "달러", "원달러"]),
    ("semiconductors", "반도체", "반도체와 AI 하드웨어 이슈", ["반도체", "엔비디아", "hbm"]),
    ("ai", "AI", "AI 서비스와 인프라 이슈", ["ai", "llm", "gpu"]),
]

ENTITIES = [
    ("index", "코스피", "KOSPI", "KOSPI"),
    ("index", "나스닥", "Nasdaq", "IXIC"),
    ("asset", "비트코인", "Bitcoin", "BTC"),
    ("company", "테슬라", "Tesla", "TSLA"),
    ("company", "엔비디아", "NVIDIA", "NVDA"),
]

POLITICAL_PARTIES = [
    ("국민의힘", "conservative", "KR", "대한민국 보수 성향 정당"),
    ("더불어민주당", "liberal", "KR", "대한민국 진보 성향 정당"),
    ("개혁신당", "reform", "KR", "대한민국 개혁 성향 정당"),
]

POLITICIANS = [
    ("윤석열", "국민의힘", "대통령", "conservative", "KR"),
    ("이재명", "더불어민주당", "국회의원", "liberal", "KR"),
    ("한동훈", "국민의힘", "정치인", "conservative", "KR"),
    ("이준석", "개혁신당", "정치인", "reform", "KR"),
]

POLITICAL_TOPICS = [
    ("presidential", "대통령·대선", "대통령 지지율과 대선 후보 관련 이슈", ["대통령", "대선", "후보"]),
    ("party_approval", "정당 지지율", "정당 선호와 지지율 흐름", ["정당", "민주당", "국민의힘"]),
    ("policy", "정책", "정책 공약과 이슈", ["정책", "연금", "부동산", "청년"]),
]


def seed_reference_data() -> None:
    with SessionLocal() as db:
        for code, name, description, keywords in TOPICS:
            if not db.query(Topic).filter(Topic.code == code).first():
                db.add(Topic(code=code, name=name, description=description, keywords=keywords))

        for entity_type, name, canonical_name, symbol in ENTITIES:
            if not db.query(Entity).filter(Entity.canonical_name == canonical_name).first():
                db.add(
                    Entity(
                        entity_type=entity_type,
                        name=name,
                        canonical_name=canonical_name,
                        symbol=symbol,
                    )
                )

        for name, ideology, country, description in POLITICAL_PARTIES:
            if not db.query(PoliticalParty).filter(PoliticalParty.name == name).first():
                db.add(
                    PoliticalParty(
                        name=name,
                        ideology=ideology,
                        country=country,
                        description=description,
                    )
                )
        db.commit()

        for name, party_name, position, ideology, country in POLITICIANS:
            if not db.query(Politician).filter(Politician.name == name).first():
                party = db.query(PoliticalParty).filter(PoliticalParty.name == party_name).first()
                db.add(
                    Politician(
                        name=name,
                        party=party_name,
                        party_id=party.id if party else None,
                        position=position,
                        ideology=ideology,
                        country=country,
                    )
                )

        for code, name, description, keywords in POLITICAL_TOPICS:
            if not db.query(PoliticalTopic).filter(PoliticalTopic.code == code).first():
                db.add(
                    PoliticalTopic(
                        code=code,
                        name=name,
                        description=description,
                        keywords=keywords,
                    )
                )
        db.commit()


if __name__ == "__main__":
    seed_reference_data()
    for job_name in [
        "collect_indicators",
        "collect_news",
        "collect_dcinside_market",
        "compute_daily_snapshots",
        "collect_political_indicators",
        "collect_dcinside_political_posts",
        "compute_political_daily_snapshots",
    ]:
        try:
            run_job(job_name, triggered_by="seed")
        except Exception:
            # Network-bound jobs can fail temporarily; keep the seed script resilient.
            continue
