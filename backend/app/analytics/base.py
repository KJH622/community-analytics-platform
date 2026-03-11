from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AnalysisResult:
    sentiment_score: float
    fear_greed_score: float
    hate_index: float
    uncertainty_score: float
    market_bias: str
    labels: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)


class BaseAnalysisEngine:
    def analyze(self, title: str, body: str | None = None) -> AnalysisResult:
        raise NotImplementedError
