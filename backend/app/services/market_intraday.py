from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Codex/1.0"
KST = ZoneInfo("Asia/Seoul")


def fetch_intraday_index(symbol: str, limit: int = 24) -> list[dict[str, float | str | None]]:
    response = httpx.get(
        YAHOO_CHART_URL.format(symbol=symbol),
        params={
            "range": "5d",
            "interval": "60m",
            "includePrePost": "false",
            "events": "div,splits",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json()

    result = payload.get("chart", {}).get("result", [])
    if not result:
        raise ValueError(f"Yahoo Finance returned no chart data for {symbol}")

    series = result[0]
    timestamps = series.get("timestamp") or []
    quote = (series.get("indicators") or {}).get("quote") or [{}]
    closes = quote[0].get("close") or []

    points: list[dict[str, float | str | None]] = []
    for timestamp, close in zip(timestamps, closes, strict=False):
        if close is None:
            continue
        observed_at = datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC")).astimezone(KST)
        points.append(
            {
                "timestamp": observed_at.isoformat(),
                "label": observed_at.strftime("%m-%d %H:00"),
                "value": round(float(close), 2),
            }
        )

    return points[-limit:]
