from __future__ import annotations

from dataclasses import dataclass

from app.analytics.lexicons import (
    ENTITY_PATTERNS,
    FEAR_WORDS,
    GREED_WORDS,
    HATE_OR_AGGRESSION_WORDS,
    INTENSIFIERS,
    NEGATIONS,
    NEGATIVE_WORDS,
    POSITIVE_WORDS,
    STOPWORDS,
    TAG_KEYWORDS,
    TOPIC_KEYWORDS,
    UNCERTAINTY_WORDS,
)
from app.utils.text import clean_text, tokenize, top_keywords


@dataclass
class AnalysisResult:
    sentiment_score: float
    fear_greed_score: float
    hate_score: float
    hate_index: float
    uncertainty_score: float
    market_bias: str
    keywords: list[str]
    tags: list[str]
    topics: list[str]
    entities: list[str]


class RuleBasedAnalyzer:
    def analyze(self, title: str, body: str) -> AnalysisResult:
        clean_title = clean_text(title)
        clean_body = clean_text(body)
        title_tokens = tokenize(clean_title)
        body_tokens = tokenize(clean_body)
        combined_tokens = title_tokens + body_tokens

        title_score = self._score_sentiment(title_tokens) * 1.7
        body_score = self._score_sentiment(body_tokens)
        sentiment_score = self._clamp((title_score + body_score) * 8, low=-100.0, high=100.0)

        fear_hits = self._count_hits(combined_tokens, FEAR_WORDS)
        greed_hits = self._count_hits(combined_tokens, GREED_WORDS)
        uncertainty_hits = self._count_hits(combined_tokens, UNCERTAINTY_WORDS)
        hate_hits = self._count_hits(combined_tokens, HATE_OR_AGGRESSION_WORDS)

        total_tokens = max(len(combined_tokens), 1)
        fear_ratio = fear_hits / total_tokens
        greed_ratio = greed_hits / total_tokens
        uncertainty_ratio = uncertainty_hits / total_tokens
        hate_ratio = hate_hits / total_tokens

        fear_greed_score = self._score_fear_greed(fear_ratio, greed_ratio, sentiment_score)
        hate_score = self._score_hate(hate_ratio, sentiment_score)
        uncertainty_score = self._score_uncertainty(uncertainty_ratio, title_tokens, body_tokens)
        hate_index = self._score_hate_index(hate_score, uncertainty_score, fear_greed_score)

        keywords = top_keywords(combined_tokens, STOPWORDS, limit=8)
        topics = self._extract_topics(combined_tokens)
        entities = self._extract_entities(combined_tokens)
        tags = self._extract_tags(combined_tokens, keywords, topics, entities)
        bias = self._derive_market_bias(sentiment_score, fear_greed_score, uncertainty_score)

        return AnalysisResult(
            sentiment_score=round(sentiment_score, 2),
            fear_greed_score=round(fear_greed_score, 2),
            hate_score=round(hate_score, 2),
            hate_index=round(hate_index, 2),
            uncertainty_score=round(uncertainty_score, 2),
            market_bias=bias,
            keywords=keywords,
            tags=tags,
            topics=topics,
            entities=entities,
        )

    def _score_sentiment(self, tokens: list[str]) -> float:
        score = 0.0
        for index, token in enumerate(tokens):
            weight = 1.0
            if index > 0 and tokens[index - 1] in INTENSIFIERS:
                weight += 0.5
            if index > 0 and tokens[index - 1] in NEGATIONS:
                weight *= -0.7
            if any(neg in token for neg in NEGATIONS):
                weight *= -0.3
            if self._matches_lexicon(token, POSITIVE_WORDS):
                score += weight
            if self._matches_lexicon(token, NEGATIVE_WORDS):
                score -= weight
        return score

    def _count_hits(self, tokens: list[str], lexicon: set[str]) -> int:
        return sum(self._matches_lexicon(token, lexicon) for token in tokens)

    def _score_fear_greed(self, fear_ratio: float, greed_ratio: float, sentiment_score: float) -> float:
        net = greed_ratio - fear_ratio
        baseline = 50 + (net * 240)
        sentiment_push = sentiment_score * 0.18
        return self._clamp(baseline + sentiment_push)

    def _score_hate(self, hate_ratio: float, sentiment_score: float) -> float:
        base = hate_ratio * 520
        negativity_boost = max(0.0, -sentiment_score) * 0.22
        return self._clamp(base + negativity_boost)

    def _score_uncertainty(self, uncertainty_ratio: float, title_tokens: list[str], body_tokens: list[str]) -> float:
        question_marks = sum(
            token.endswith("까") or token.endswith("냐") or token in {"왜", "뭘까", "어쩌지", "맞냐"}
            for token in title_tokens + body_tokens
        )
        base = uncertainty_ratio * 380
        question_boost = min(question_marks * 5, 15)
        ambiguity_boost = 8 if any(token in {"현황", "근황", "속보", "자료표"} for token in title_tokens + body_tokens) else 0
        return self._clamp(base + question_boost + ambiguity_boost)

    def _score_hate_index(self, hate_score: float, uncertainty_score: float, fear_greed_score: float) -> float:
        extremity = abs(fear_greed_score - 50) * 2
        composite = hate_score * 0.72 + uncertainty_score * 0.12 + extremity * 0.16
        return self._clamp(composite)

    def _derive_market_bias(
        self, sentiment_score: float, fear_greed_score: float, uncertainty_score: float
    ) -> str:
        composite = sentiment_score + (fear_greed_score - 50) - uncertainty_score * 0.25
        if composite >= 15:
            return "bullish"
        if composite <= -15:
            return "bearish"
        return "neutral"

    def _extract_topics(self, tokens: list[str]) -> list[str]:
        return [topic for topic, keywords in TOPIC_KEYWORDS.items() if self._count_hits(tokens, keywords) > 0]

    def _extract_entities(self, tokens: list[str]) -> list[str]:
        found: list[str] = []
        for keywords in ENTITY_PATTERNS.values():
            for token in tokens:
                if self._matches_lexicon(token, keywords) and token not in found:
                    found.append(token)
        return found

    def _extract_tags(
        self, tokens: list[str], keywords: list[str], topics: list[str], entities: list[str]
    ) -> list[str]:
        scored_tags: list[tuple[str, int]] = []
        for tag, tag_keywords in TAG_KEYWORDS.items():
            score = self._count_hits(tokens, tag_keywords)
            if score > 0:
                scored_tags.append((tag, score))

        scored_tags.sort(key=lambda item: (-item[1], item[0]))
        tags = [tag for tag, _score in scored_tags[:2]]

        for topic in topics:
            mapped = self._topic_to_tag(topic)
            if mapped not in tags:
                tags.append(mapped)
            if len(tags) == 2:
                break

        while len(tags) < 2:
            fallback = "커뮤니티반응" if not tags else "시장심리"
            if fallback not in tags:
                tags.append(fallback)

        return tags[:2]

    def _topic_to_tag(self, topic: str) -> str:
        mapping = {
            "rates": "금리",
            "inflation": "인플레이션",
            "fx": "환율",
            "semiconductor": "반도체",
            "ai": "AI",
            "us_equity": "미국주식",
            "kr_equity": "국내주식",
            "crypto": "암호화폐",
            "oil": "원유",
            "geopolitics": "전쟁리스크",
        }
        return mapping.get(topic, topic)

    def _clamp(self, value: float, low: float = 0.0, high: float = 100.0) -> float:
        return max(low, min(high, value))

    def _matches_lexicon(self, token: str, lexicon: set[str]) -> bool:
        return any(term == token or term in token or token in term for term in lexicon)
