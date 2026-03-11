from __future__ import annotations

from dataclasses import dataclass

from app.analytics.keywords import tokenize


TOPIC_KEYWORDS = {
    "rates": {"금리", "fomc", "fed", "기준금리", "국채금리"},
    "inflation": {"cpi", "ppi", "물가", "인플레", "core", "근원물가"},
    "fx": {"환율", "달러", "원달러", "dxy"},
    "semiconductors": {"반도체", "엔비디아", "nvidia", "tsmc", "hbm"},
    "ai": {"ai", "인공지능", "openai", "llm", "gpu"},
    "tesla": {"테슬라", "tesla", "tsla"},
    "korea_market": {"국장", "코스피", "코스닥", "kospi", "kosdaq"},
    "us_market": {"미장", "나스닥", "s&p500", "nasdaq", "dow"},
}

ENTITY_ALIASES = {
    "S&P500": {"s&p500", "sp500"},
    "Nasdaq": {"nasdaq", "나스닥"},
    "KOSPI": {"kospi", "코스피"},
    "KOSDAQ": {"kosdaq", "코스닥"},
    "Bitcoin": {"btc", "bitcoin", "비트코인"},
    "Tesla": {"tsla", "tesla", "테슬라"},
    "NVIDIA": {"nvidia", "엔비디아", "nvda"},
    "Fed": {"fed", "연준", "fomc"},
}


@dataclass(slots=True)
class EntityTopicResult:
    entities: list[str]
    topics: list[str]


def extract_entities_and_topics(text: str) -> EntityTopicResult:
    tokens = set(tokenize(text))
    entities = [
        entity for entity, aliases in ENTITY_ALIASES.items() if tokens.intersection({a.lower() for a in aliases})
    ]
    topics = [
        topic for topic, keywords in TOPIC_KEYWORDS.items() if tokens.intersection({kw.lower() for kw in keywords})
    ]
    return EntityTopicResult(entities=entities, topics=topics)
