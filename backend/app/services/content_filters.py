from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.sentiment import Sentiment
from app.politics.models.tables import PoliticalSentiment


COMMON_NOTICE_TERMS = {
    "공지",
    "공지사항",
    "운영",
    "운영규칙",
    "규칙",
    "이용안내",
    "안내",
    "가이드",
    "신문고",
    "제보",
    "모음",
    "정리",
    "정보",
    "faq",
}

MARKET_INFO_TERMS = {
    "휴장",
    "서머타임",
    "운영시간",
    "개장",
    "장전",
    "장후",
    "일정",
    "fomc",
    "cpi",
    "ppi",
    "발표",
    "경제지표",
}

MARKET_EMOTION_TERMS = {
    "폭락",
    "패닉",
    "손절",
    "공포",
    "붕괴",
    "떡상",
    "로켓",
    "간다",
    "미쳤",
    "망했다",
    "개같",
    "좆됐",
    "살려",
    "미장",
    "코스피",
    "개미",
}

POLITICAL_INFO_TERMS = {
    "권리당원",
    "모집",
    "입문",
    "인사드립니다",
    "업적",
    "공약 정리",
    "이용 규칙",
    "갤러리 이용",
    "안녕하세요",
}

POLITICAL_EMOTION_TERMS = {
    "지지",
    "반대",
    "분노",
    "조롱",
    "열광",
    "정치혐오",
    "탄핵",
    "심판",
    "후보",
    "대선",
    "총선",
}


@dataclass(slots=True)
class ContentFilterResult:
    excluded: bool
    reasons: list[str]


def classify_market_post(title: str, body: str | None = None) -> ContentFilterResult:
    return _classify_post(
        title=title,
        body=body,
        info_terms=MARKET_INFO_TERMS,
        emotion_terms=MARKET_EMOTION_TERMS,
    )


def classify_political_post(title: str, body: str | None = None) -> ContentFilterResult:
    return _classify_post(
        title=title,
        body=body,
        info_terms=POLITICAL_INFO_TERMS,
        emotion_terms=POLITICAL_EMOTION_TERMS,
    )


def compute_market_influence_score(
    *,
    sentiment: Sentiment | None,
    title: str,
    body: str | None,
    view_count: int | None,
    upvotes: int | None,
    comment_count: int | None,
    published_at: datetime | None,
) -> float:
    classification = classify_market_post(title, body)
    if classification.excluded:
        return 0.0

    reaction = _reaction_score(view_count, upvotes, comment_count)
    recency = _recency_multiplier(published_at)
    text_heat = _term_hits(f"{title} {body or ''}".lower(), MARKET_EMOTION_TERMS) * 3.0
    if sentiment is None:
        emotion = text_heat
    else:
        emotion = (
            abs(sentiment.sentiment_score) * 0.32
            + abs(sentiment.fear_greed_score - 50.0) * 0.65
            + sentiment.hate_index * 0.9
            + sentiment.uncertainty_score * 0.38
            + text_heat
        )
    return round(reaction * recency * (1.0 + min(emotion, 100.0) / 115.0), 2)


def compute_political_influence_score(
    *,
    sentiment: PoliticalSentiment | None,
    title: str,
    body: str | None,
    view_count: int | None,
    upvotes: int | None,
    comment_count: int | None,
    published_at: datetime | None,
) -> float:
    classification = classify_political_post(title, body)
    if classification.excluded:
        return 0.0

    reaction = _reaction_score(view_count, upvotes, comment_count)
    recency = _recency_multiplier(published_at)
    text_heat = _term_hits(f"{title} {body or ''}".lower(), POLITICAL_EMOTION_TERMS) * 3.6
    if sentiment is None:
        emotion = text_heat
    else:
        emotion = (
            sentiment.support_score * 0.22
            + sentiment.opposition_score * 0.24
            + sentiment.anger_score * 0.48
            + sentiment.sarcasm_score * 0.42
            + sentiment.enthusiasm_score * 0.28
            + sentiment.political_polarization_index * 0.65
            + sentiment.election_heat_index * 0.34
            + text_heat
        )
    return round(reaction * recency * (1.0 + min(emotion, 120.0) / 120.0), 2)


def _classify_post(
    *,
    title: str,
    body: str | None,
    info_terms: set[str],
    emotion_terms: set[str],
) -> ContentFilterResult:
    title_text = (title or "").lower()
    body_text = (body or "").lower()
    full_text = f"{title_text} {body_text}".strip()
    reasons: list[str] = []

    if title_text.startswith("📣") or title_text.startswith("[공지]"):
        reasons.append("title_notice_marker")
    if any(term in title_text for term in COMMON_NOTICE_TERMS):
        reasons.append("title_notice_term")

    info_hits = _term_hits(full_text, info_terms)
    emotion_hits = _term_hits(full_text, emotion_terms)

    if info_hits >= 2 and emotion_hits == 0:
        reasons.append("informational_post")
    if any(phrase in full_text for phrase in {"운영 규칙", "이용 규칙", "권리당원을 모집", "안녕하세요"}):
        reasons.append("housekeeping_or_campaign_notice")
    if "정리" in title_text and emotion_hits == 0:
        reasons.append("summary_post")

    return ContentFilterResult(excluded=bool(reasons), reasons=sorted(set(reasons)))


def _reaction_score(view_count: int | None, upvotes: int | None, comment_count: int | None) -> float:
    views = max(view_count or 0, 0)
    upvotes = max(upvotes or 0, 0)
    comments = max(comment_count or 0, 0)
    return (
        math.log10(views + 1) * 14.0
        + math.log10(upvotes + 1) * 26.0
        + math.log10(comments + 1) * 22.0
    )


def _recency_multiplier(published_at: datetime | None) -> float:
    if published_at is None:
        return 0.55
    timestamp = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
    age_days = max((datetime.now(timezone.utc) - timestamp).total_seconds() / 86_400.0, 0.0)
    if age_days <= 1:
        return 1.18
    if age_days <= 3:
        return 1.08
    if age_days <= 7:
        return 0.96
    if age_days <= 30:
        return 0.78
    if age_days <= 180:
        return 0.52
    return 0.24


def _term_hits(text: str, lexicon: set[str]) -> int:
    return sum(1 for term in lexicon if term in text)
