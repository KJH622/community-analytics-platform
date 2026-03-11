from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.analytics.rule_based import AnalysisResult, RuleBasedAnalyzer
from app.core.config import Settings, get_settings
from app.utils.text import clean_text

OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_JSON_SCHEMA = {
    "name": "community_post_analysis",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "sentiment_score": {"type": "number", "minimum": -100, "maximum": 100},
            "fear_greed_score": {"type": "number", "minimum": 0, "maximum": 100},
            "hate_index": {"type": "number", "minimum": 0, "maximum": 100},
            "uncertainty_score": {"type": "number", "minimum": 0, "maximum": 100},
            "market_bias": {
                "type": "string",
                "enum": ["bullish", "neutral", "bearish"],
            },
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 8,
            },
            "topics": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 6,
            },
            "entities": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 6,
            },
        },
        "required": [
            "sentiment_score",
            "fear_greed_score",
            "hate_index",
            "uncertainty_score",
            "market_bias",
            "keywords",
            "topics",
            "entities",
        ],
    },
}
SYSTEM_PROMPT = """
You analyze Korean finance and stock community posts.

Return JSON only.

Scoring rules:
- sentiment_score: -100 very negative, 0 neutral, 100 very positive
- fear_greed_score: 0 fear, 50 balanced, 100 greed
- hate_index: 0 no hostility, 100 extreme hostility, contempt, aggressive mockery, or dehumanizing tone
- uncertainty_score: 0 certainty, 100 highly speculative, confused, rumor-driven, or doubtful
- market_bias: bullish, neutral, or bearish
- keywords/topics/entities: extract only from the provided text, keep them short, deduplicated, and in Korean when possible

Judge only from the title and body. Do not invent facts outside the text.
""".strip()


@dataclass
class CommunityAnalysisEnvelope:
    analysis: AnalysisResult
    provider: str
    model: str | None = None


class OpenAICommunityAnalyzer:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.fallback = RuleBasedAnalyzer()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.openai_api_key)

    @property
    def model(self) -> str:
        return self.settings.openai_community_model

    def analyze(self, title: str, body: str) -> CommunityAnalysisEnvelope:
        fallback = self.fallback.analyze(title, body)
        if not self.enabled:
            return CommunityAnalysisEnvelope(analysis=fallback, provider="rule_based", model=None)

        clean_title = clean_text(title)[: self.settings.openai_community_title_char_limit]
        clean_body = clean_text(body)[: self.settings.openai_community_body_char_limit]
        if not clean_title and not clean_body:
            return CommunityAnalysisEnvelope(analysis=fallback, provider="rule_based", model=None)

        try:
            payload = self._request_analysis(clean_title, clean_body)
            analysis = self._normalize_payload(payload)
            return CommunityAnalysisEnvelope(analysis=analysis, provider="openai", model=self.model)
        except Exception:
            return CommunityAnalysisEnvelope(analysis=fallback, provider="rule_based", model=None)

    def _request_analysis(self, title: str, body: str) -> dict[str, Any]:
        response = httpx.post(
            OPENAI_CHAT_COMPLETIONS_URL,
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            "Analyze the following Korean community post using only the title and body.\n"
                            f"Title: {title}\n"
                            f"Body: {body}"
                        ),
                    },
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": OPENAI_JSON_SCHEMA,
                },
            },
            timeout=self.settings.request_timeout_seconds + 15,
        )
        response.raise_for_status()
        payload = response.json()
        message = payload["choices"][0]["message"]
        if message.get("refusal"):
            raise RuntimeError("OpenAI refused the analysis request.")
        content = message.get("content")
        if not content:
            raise RuntimeError("OpenAI returned an empty analysis payload.")
        return json.loads(content)

    def _normalize_payload(self, payload: dict[str, Any]) -> AnalysisResult:
        return AnalysisResult(
            sentiment_score=round(_clamp(payload.get("sentiment_score"), -100.0, 100.0), 2),
            fear_greed_score=round(_clamp(payload.get("fear_greed_score"), 0.0, 100.0), 2),
            hate_index=round(_clamp(payload.get("hate_index"), 0.0, 100.0), 2),
            uncertainty_score=round(_clamp(payload.get("uncertainty_score"), 0.0, 100.0), 2),
            market_bias=_normalize_bias(payload.get("market_bias")),
            keywords=_normalize_terms(payload.get("keywords"), limit=8),
            topics=_normalize_terms(payload.get("topics"), limit=6),
            entities=_normalize_terms(payload.get("entities"), limit=6),
        )


def _clamp(value: Any, minimum: float, maximum: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = minimum
    return max(minimum, min(maximum, numeric))


def _normalize_bias(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"bullish", "bearish"}:
        return normalized
    return "neutral"


def _normalize_terms(value: Any, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    deduped: list[str] = []
    for item in value:
        text = str(item).strip()
        if not text or text in deduped:
            continue
        deduped.append(text)
        if len(deduped) >= limit:
            break
    return deduped
