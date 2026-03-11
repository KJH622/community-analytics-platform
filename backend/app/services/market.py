from __future__ import annotations

from datetime import UTC, datetime
from time import time

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DailyMarketSentimentSnapshot

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
MARKET_TTL_SECONDS = 900

_market_cache: dict[str, tuple[float, list[tuple[str, float]]]] = {}


def get_market_comparison(db: Session, days: int = 14) -> dict:
    snapshots = db.execute(
        select(DailyMarketSentimentSnapshot)
        .order_by(DailyMarketSentimentSnapshot.snapshot_date.desc())
        .limit(max(days, 7))
    ).scalars().all()
    snapshots = list(reversed(snapshots))

    if not snapshots:
        return {
            "reference_date": None,
            "comparison_basis": "최근 구간 0~100 정규화",
            "latest": {
                "kospi_close": None,
                "kosdaq_close": None,
                "kospi_change_pct": None,
                "kosdaq_change_pct": None,
                "hate_index": None,
                "hate_change": None,
            },
            "points": [],
        }

    dates = [item.snapshot_date.isoformat() for item in snapshots]
    hate_values = [round(float(item.hate_index), 4) for item in snapshots]

    kospi_points = _fetch_yahoo_history("%5EKS11")
    kosdaq_points = _fetch_yahoo_history("%5EKQ11")

    kospi_aligned = _align_market_series(dates, kospi_points)
    kosdaq_aligned = _align_market_series(dates, kosdaq_points)

    kospi_scaled = _scale_series(kospi_aligned)
    kosdaq_scaled = _scale_series(kosdaq_aligned)
    hate_scaled = _scale_series(hate_values)

    points = []
    for index, snapshot in enumerate(snapshots):
        points.append(
            {
                "date": snapshot.snapshot_date,
                "kospi_close": kospi_aligned[index],
                "kosdaq_close": kosdaq_aligned[index],
                "hate_index": hate_values[index],
                "kospi_scaled": kospi_scaled[index],
                "kosdaq_scaled": kosdaq_scaled[index],
                "hate_scaled": hate_scaled[index],
            }
        )

    return {
        "reference_date": snapshots[-1].snapshot_date,
        "comparison_basis": "최근 구간 0~100 정규화",
        "latest": {
            "kospi_close": kospi_aligned[-1] if kospi_aligned else None,
            "kosdaq_close": kosdaq_aligned[-1] if kosdaq_aligned else None,
            "kospi_change_pct": _pct_change(kospi_aligned),
            "kosdaq_change_pct": _pct_change(kosdaq_aligned),
            "hate_index": hate_values[-1] if hate_values else None,
            "hate_change": _diff_change(hate_values),
        },
        "points": points,
    }


def _fetch_yahoo_history(symbol: str) -> list[tuple[str, float]]:
    cached = _market_cache.get(symbol)
    now = time()
    if cached and now - cached[0] < MARKET_TTL_SECONDS:
        return cached[1]

    response = httpx.get(
        YAHOO_CHART_URL.format(symbol=symbol),
        params={"range": "3mo", "interval": "1d"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json()
    result = payload["chart"]["result"][0]
    timestamps = result.get("timestamp", [])
    closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])

    rows: list[tuple[str, float]] = []
    for timestamp, close in zip(timestamps, closes, strict=False):
        if close is None:
            continue
        item_date = datetime.fromtimestamp(timestamp, tz=UTC).date().isoformat()
        rows.append((item_date, round(float(close), 4)))

    _market_cache[symbol] = (now, rows)
    return rows


def _align_market_series(dates: list[str], market_points: list[tuple[str, float]]) -> list[float | None]:
    if not market_points:
        return [None for _ in dates]

    market_points = sorted(market_points, key=lambda item: item[0])
    aligned: list[float | None] = []
    cursor = 0
    latest_value: float | None = None

    for item_date in dates:
        while cursor < len(market_points) and market_points[cursor][0] <= item_date:
            latest_value = market_points[cursor][1]
            cursor += 1
        aligned.append(latest_value)

    return aligned


def _scale_series(values: list[float | None]) -> list[float]:
    numeric = [value for value in values if value is not None]
    if not numeric:
        return [0.0 for _ in values]

    minimum = min(numeric)
    maximum = max(numeric)
    if maximum == minimum:
        return [0.0 for _ in values]

    scaled = []
    for value in values:
        if value is None:
            scaled.append(0.0)
        else:
            scaled.append(round(((value - minimum) / (maximum - minimum)) * 100, 2))
    return scaled


def _pct_change(values: list[float | None]) -> float | None:
    numeric = [value for value in values if value is not None]
    if len(numeric) < 2:
        return None
    previous = numeric[-2]
    current = numeric[-1]
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 2)


def _diff_change(values: list[float | None]) -> float | None:
    numeric = [value for value in values if value is not None]
    if len(numeric) < 2:
        return None
    return round(numeric[-1] - numeric[-2], 2)
