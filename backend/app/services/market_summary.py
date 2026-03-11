from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.core.config import get_settings


SYSTEM_PROMPT = """
You create a concise Korean market dashboard summary.
Return only valid JSON.

Rules:
- Use exactly 3 summary lines.
- Each line must be one Korean sentence.
- Reflect the hate index as a community heat/risk signal.
- Mention KOSPI and Nasdaq when values are available.
- Keep the tone analytical, not promotional.
- status_label must be exactly one of: CALM, WATCH, HIGH.
- analysis_note must briefly say this is a GPT-based reading of market and community mood.

JSON schema:
{
  "status_label": "CALM" | "WATCH" | "HIGH",
  "summary_lines": ["...", "...", "..."],
  "analysis_note": "..."
}
""".strip()

FALLBACK_MOOD_POSITIVE = "\uB9E4\uC218 \uC5F4\uAE30\uAC00 \uBD99\uB294 \uBD84\uC704\uAE30"
FALLBACK_MOOD_NEUTRAL = "\uAD00\uB9DD\uACFC \uACBD\uACC4\uAC00 \uD568\uAED8 \uB3C4\uB294 \uBD84\uC704\uAE30"
FALLBACK_MOOD_NEGATIVE = "\uBC29\uC5B4 \uC2EC\uB9AC\uAC00 \uAC15\uD55C \uBD84\uC704\uAE30"
FALLBACK_KEYWORDS = "\uD575\uC2EC \uD0A4\uC6CC\uB4DC \uC9D1\uACC4 \uB300\uAE30"
FALLBACK_NO_QUOTES = "\uAD6D\uB0B4\uC678 \uC9C0\uC218 \uD750\uB984\uACFC \uCEE4\uBBA4\uB2C8\uD2F0 \uC2EC\uB9AC\uB97C \uD568\uAED8 \uBCF4\uBA70 \uBC29\uD5A5\uC131 \uD655\uC778\uC774 \uD544\uC694\uD55C \uAD6C\uAC04\uC785\uB2C8\uB2E4."
FALLBACK_ANALYSIS_NOTE = "\uC694\uC57D\uC5D0 GPT\uB97C \uC4F8 \uC218 \uC5C6\uC5B4 \uD604\uC7AC\uB294 \uADDC\uCE59 \uAE30\uBC18 \uD574\uC11D\uC73C\uB85C \uC2DC\uC7A5\uACFC \uCEE4\uBBA4\uB2C8\uD2F0 \uBD84\uC704\uAE30\uB97C \uC815\uB9AC\uD588\uC2B5\uB2C8\uB2E4."


class MarketSummaryService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = (
            OpenAI(
                api_key=self.settings.openai_api_key,
                timeout=self.settings.openai_timeout_seconds,
            )
            if self.settings.openai_api_key
            else None
        )

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.client is None:
            return self._fallback(payload)

        try:
            response = self.client.responses.create(
                model=self.settings.openai_model,
                input=[
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": json.dumps(payload, ensure_ascii=False, indent=2),
                            }
                        ],
                    },
                ],
                max_output_tokens=500,
            )
            output = self._parse_response(getattr(response, "output_text", "") or "")
            return self._normalize(output, payload, source="gpt")
        except Exception:
            return self._fallback(payload)

    def _parse_response(self, value: str) -> dict[str, Any]:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            start = value.find("{")
            end = value.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(value[start : end + 1])
            raise

    def _normalize(self, raw: dict[str, Any], payload: dict[str, Any], source: str) -> dict[str, Any]:
        fallback = self._fallback(payload)
        status_label = str(raw.get("status_label", fallback["status_label"])).strip().upper()
        if status_label not in {"CALM", "WATCH", "HIGH"}:
            status_label = fallback["status_label"]

        summary_lines = [
            str(line).strip()
            for line in raw.get("summary_lines", [])
            if isinstance(line, str) and str(line).strip()
        ][:3]
        if len(summary_lines) < 3:
            summary_lines = fallback["summary_lines"]

        analysis_note = str(raw.get("analysis_note", "")).strip() or fallback["analysis_note"]

        return {
            "status_label": status_label,
            "summary_lines": summary_lines,
            "analysis_note": analysis_note,
            "source": source,
        }

    def _fallback(self, payload: dict[str, Any]) -> dict[str, Any]:
        hate_index = _as_float(payload.get("hate_index"), default=0.0)
        fear_greed = _as_float(payload.get("fear_greed_score"), default=50.0)
        uncertainty = _as_float(payload.get("uncertainty_score"), default=0.0)
        sentiment = _as_float(payload.get("sentiment_score"), default=0.0)
        kospi_value = payload.get("kospi_value")
        kospi_change = payload.get("kospi_change_percent")
        nasdaq_value = payload.get("nasdaq_value")
        nasdaq_change = payload.get("nasdaq_change_percent")
        keywords = [str(item).strip() for item in payload.get("top_keywords", []) if str(item).strip()][:3]

        intensity = max(hate_index, uncertainty, abs(fear_greed - 50.0) * 1.8)
        if intensity >= 70:
            status_label = "HIGH"
        elif intensity >= 40:
            status_label = "WATCH"
        else:
            status_label = "CALM"

        if sentiment > 15:
            mood = FALLBACK_MOOD_POSITIVE
        elif sentiment > -15:
            mood = FALLBACK_MOOD_NEUTRAL
        else:
            mood = FALLBACK_MOOD_NEGATIVE

        keywords_text = ", ".join(keywords) if keywords else FALLBACK_KEYWORDS
        line_one = (
            f"\uCEE4\uBBA4\uB2C8\uD2F0 \uD610\uC624\uC9C0\uC218\uB294 {hate_index:.1f}, "
            f"\uACF5\uD3EC\u00B7\uD0D0\uC695\uC740 {fear_greed:.1f}, "
            f"\uBD88\uD655\uC2E4\uC131\uC740 {uncertainty:.1f}\uB85C {mood}\uC785\uB2C8\uB2E4."
        )

        if kospi_value is not None and nasdaq_value is not None:
            line_two = (
                f"\uCF54\uC2A4\uD53C\uB294 {float(kospi_value):,.2f}({_signed_percent(kospi_change)}), "
                f"\uB098\uC2A4\uB2E5\uC740 {float(nasdaq_value):,.2f}({_signed_percent(nasdaq_change)}) \uC218\uC900\uC785\uB2C8\uB2E4."
            )
        else:
            line_two = FALLBACK_NO_QUOTES

        line_three = (
            f"\uC624\uB298 \uB300\uD654\uC758 \uC911\uC2EC \uD0A4\uC6CC\uB4DC\uB294 {keywords_text}\uC774\uBA70, "
            "\uBCC0\uB3D9\uC131\uBCF4\uB2E4 \uCCB4\uAC10 \uC2EC\uB9AC \uBCC0\uD654\uC5D0 \uBA3C\uC800 \uBC18\uC751\uD558\uB294 \uBAA8\uC2B5\uC785\uB2C8\uB2E4."
        )

        return {
            "status_label": status_label,
            "summary_lines": [line_one, line_two, line_three],
            "analysis_note": FALLBACK_ANALYSIS_NOTE,
            "source": "fallback",
        }


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _signed_percent(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{numeric:+.2f}%"
