from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from app.utils.text import clean_text, tokenize, top_keywords

SUPPORT_WORDS = {"지지", "응원", "찬성", "신뢰", "기대", "호감"}
OPPOSITION_WORDS = {"반대", "비판", "실망", "무능", "퇴진", "불신"}
ANGER_WORDS = {"분노", "화난", "열받", "짜증", "격분"}
MOCKERY_WORDS = {"조롱", "비웃", "놀리", "비꼼", "비아냥"}
POLITICAL_HATE_WORDS = {"정치혐오", "혐오", "다싫", "환멸", "역겹"}
APATHY_WORDS = {"무관심", "관심없", "모르겠", "아무나", "지겹"}
ENTHUSIASM_WORDS = {"열광", "결집", "총공", "압승", "기세"}
ELECTION_WORDS = {"대선", "총선", "재보선", "후보", "경선", "투표"}


@dataclass
class PoliticalAnalysisResult:
    political_sentiment_score: float
    support_score: float
    opposition_score: float
    anger_score: float
    mockery_score: float
    political_hate_score: float
    apathy_score: float
    enthusiasm_score: float
    political_polarization_index: float
    election_heat_index: float
    politician_mentions: list[str]
    keywords: list[str]
    labels: list[str]


class PoliticalRuleBasedAnalyzer:
    def analyze(self, title: str, body: str, politician_names: list[str]) -> PoliticalAnalysisResult:
        text = clean_text(f"{title} {body}")
        tokens = tokenize(text)

        support = sum(any(word in token for word in SUPPORT_WORDS) for token in tokens) * 14
        opposition = sum(any(word in token for word in OPPOSITION_WORDS) for token in tokens) * 14
        anger = sum(any(word in token for word in ANGER_WORDS) for token in tokens) * 18
        mockery = sum(any(word in token for word in MOCKERY_WORDS) for token in tokens) * 16
        political_hate = sum(any(word in token for word in POLITICAL_HATE_WORDS) for token in tokens) * 18
        apathy = sum(any(word in token for word in APATHY_WORDS) for token in tokens) * 15
        enthusiasm = sum(any(word in token for word in ENTHUSIASM_WORDS) for token in tokens) * 16
        election_heat = sum(token in ELECTION_WORDS for token in tokens) * 14

        sentiment = max(-100.0, min(100.0, support + enthusiasm - opposition - anger * 0.6 - political_hate * 0.4))
        polarization = max(0.0, min(100.0, abs(support - opposition) + (anger + mockery) * 0.4))
        mentions = [name for name in politician_names if name in text]
        keywords = top_keywords(tokens, {"그리고", "하지만", "정치", "커뮤니티", "게시판"}, limit=10)
        labels = self._derive_labels(support, opposition, anger, mockery, political_hate, apathy, enthusiasm)

        return PoliticalAnalysisResult(
            political_sentiment_score=round(sentiment, 2),
            support_score=min(100.0, float(support)),
            opposition_score=min(100.0, float(opposition)),
            anger_score=min(100.0, float(anger)),
            mockery_score=min(100.0, float(mockery)),
            political_hate_score=min(100.0, float(political_hate)),
            apathy_score=min(100.0, float(apathy)),
            enthusiasm_score=min(100.0, float(enthusiasm)),
            political_polarization_index=round(min(100.0, polarization), 2),
            election_heat_index=round(min(100.0, float(election_heat)), 2),
            politician_mentions=mentions,
            keywords=keywords,
            labels=labels,
        )

    def mention_top10(self, sentiments: list[PoliticalAnalysisResult]) -> list[dict]:
        counter = Counter(name for sentiment in sentiments for name in sentiment.politician_mentions)
        return [{"name": name, "mentions": count} for name, count in counter.most_common(10)]

    def _derive_labels(
        self,
        support: float,
        opposition: float,
        anger: float,
        mockery: float,
        political_hate: float,
        apathy: float,
        enthusiasm: float,
    ) -> list[str]:
        labels: list[str] = []
        if support > opposition:
            labels.append("지지")
        if opposition >= support and opposition > 0:
            labels.append("반대")
        if anger > 0:
            labels.append("분노")
        if mockery > 0:
            labels.append("조롱")
        if political_hate > 0:
            labels.append("정치 혐오")
        if apathy > 0:
            labels.append("정치 무관심")
        if enthusiasm > 0:
            labels.append("정치 열광")
        return labels
