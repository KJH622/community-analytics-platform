from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass


TOKEN_RE = re.compile(r"[A-Za-z0-9가-힣]{2,}")

SUPPORT_TERMS = {"지지", "응원", "찬성", "호감", "믿는다", "잘한다", "밀어준다"}
OPPOSITION_TERMS = {"반대", "비판", "실망", "못한다", "퇴진", "불신", "심판"}
ANGER_TERMS = {"분노", "화난다", "열받", "빡친", "격분", "짜증"}
SARCASM_TERMS = {"조롱", "비웃", "비꼰", "웃기네", "실화냐", "ㅋㅋ"}
APATHY_TERMS = {"무관심", "관심없", "정치혐오", "모르겠", "싫다", "안본다"}
ENTHUSIASM_TERMS = {"열광", "대박", "확신", "무조건", "압승", "간다", "드가자"}
ELECTION_TERMS = {"대선", "총선", "후보", "경선", "정당", "투표", "대통령", "탄핵"}

POLITICIAN_NAMES = {"이재명", "한동훈", "윤석열", "이준석", "조국", "홍준표", "김문수"}
PARTY_NAMES = {"국민의힘", "더불어민주당", "민주당", "개혁신당", "조국혁신당", "진보당"}
POLICY_KEYWORDS = {"부동산", "증세", "복지", "외교", "연금", "청년", "반도체", "의료", "노동", "추경"}


@dataclass(slots=True)
class PoliticalAnalysisResult:
    political_sentiment_score: float
    support_score: float
    opposition_score: float
    anger_score: float
    sarcasm_score: float
    apathy_score: float
    enthusiasm_score: float
    political_polarization_index: float
    election_heat_index: float
    labels: list[str]
    keywords: list[str]
    politicians: list[str]


def analyze_political_text(title: str, body: str | None) -> PoliticalAnalysisResult:
    full_body = body or ""
    combined_text = f"{title} {full_body}".strip()
    normalized = combined_text.lower()

    title_tokens = TOKEN_RE.findall(title.lower())
    body_tokens = TOKEN_RE.findall(full_body.lower())
    counts = Counter(title_tokens + body_tokens)

    support = _score_terms(title_tokens, body_tokens, SUPPORT_TERMS, factor=16)
    opposition = _score_terms(title_tokens, body_tokens, OPPOSITION_TERMS, factor=16)
    anger = _score_terms(title_tokens, body_tokens, ANGER_TERMS, factor=18)
    sarcasm = _score_terms(title_tokens, body_tokens, SARCASM_TERMS, factor=14)
    apathy = _score_terms(title_tokens, body_tokens, APATHY_TERMS, factor=14)
    enthusiasm = _score_terms(title_tokens, body_tokens, ENTHUSIASM_TERMS, factor=16)
    election_hits = _score_terms(title_tokens, body_tokens, ELECTION_TERMS, factor=12)

    politician_hits = sum(1 for name in POLITICIAN_NAMES if name.lower() in normalized)
    party_hits = sum(1 for name in PARTY_NAMES if name.lower() in normalized)

    sentiment_score = max(
        -100.0,
        min(
            100.0,
            support
            + enthusiasm * 0.8
            - opposition
            - anger * 0.65
            - apathy * 0.55,
        ),
    )
    polarization = max(
        0.0,
        min(
            100.0,
            abs(support - opposition) * 0.8
            + (support + opposition) * 0.35
            + anger * 0.4
            + sarcasm * 0.35,
        ),
    )
    election_heat = max(
        0.0,
        min(100.0, election_hits + (politician_hits * 8.0) + (party_hits * 5.0)),
    )

    matched_keywords = []
    for token, _ in counts.most_common(16):
        if token in POLITICIAN_NAMES or token in PARTY_NAMES or token in POLICY_KEYWORDS or token in ELECTION_TERMS:
            matched_keywords.append(token)
    politicians = [name for name in POLITICIAN_NAMES if name.lower() in normalized]

    labels: list[str] = []
    if support >= 25:
        labels.append("지지")
    if opposition >= 25:
        labels.append("반대")
    if anger >= 25:
        labels.append("분노")
    if sarcasm >= 18:
        labels.append("조롱")
    if apathy >= 18:
        labels.append("정치 무관심")
    if enthusiasm >= 22:
        labels.append("정치 열광")

    return PoliticalAnalysisResult(
        political_sentiment_score=round(sentiment_score, 2),
        support_score=round(min(support, 100.0), 2),
        opposition_score=round(min(opposition, 100.0), 2),
        anger_score=round(min(anger, 100.0), 2),
        sarcasm_score=round(min(sarcasm, 100.0), 2),
        apathy_score=round(min(apathy, 100.0), 2),
        enthusiasm_score=round(min(enthusiasm, 100.0), 2),
        political_polarization_index=round(polarization, 2),
        election_heat_index=round(election_heat, 2),
        labels=labels,
        keywords=matched_keywords[:8],
        politicians=politicians,
    )


def _score_terms(
    title_tokens: list[str],
    body_tokens: list[str],
    lexicon: set[str],
    *,
    factor: float,
) -> float:
    title_hits = sum(1 for token in title_tokens if any(token == term or token.startswith(term) for term in lexicon))
    body_hits = sum(1 for token in body_tokens if any(token == term or token.startswith(term) for term in lexicon))
    return (title_hits * 1.6 + body_hits) * factor
