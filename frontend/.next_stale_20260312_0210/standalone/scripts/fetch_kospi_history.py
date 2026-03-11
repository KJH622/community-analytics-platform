#!/usr/bin/env python
"""Fetch recent daily KOSPI history from Naver Finance."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from html import unescape
from urllib.request import Request, urlopen


URL = "https://finance.naver.com/sise/sise_index_day.naver?code=KOSPI&page=1"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)


def _clean(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_float(value: str) -> float:
    return float(value.replace(",", "").replace("%", "").strip())


def fetch_html() -> str:
    request = Request(URL, headers={"User-Agent": USER_AGENT, "Referer": "https://finance.naver.com/"})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("euc-kr", errors="replace")


def parse_rows(html: str, days: int) -> list[dict]:
    table_match = re.search(r'<table[^>]*class="type_1"[^>]*>(.*?)</table>', html, flags=re.S)
    if not table_match:
        raise RuntimeError("Failed to locate KOSPI history table.")

    rows: list[dict] = []
    for chunk in re.findall(r"<tr>(.*?)</tr>", table_match.group(1), flags=re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", chunk, flags=re.S)
        if len(cells) < 6:
            continue
        date_text = _clean(cells[0])
        if not re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", date_text):
            continue

        diff_direction = "up" if "ico_up.gif" in cells[2] else "down" if "ico_down.gif" in cells[2] else "flat"
        diff_value = _parse_float(_clean(cells[2]))
        if diff_direction == "down":
            diff_value *= -1

        rows.append(
            {
                "date": datetime.strptime(date_text, "%Y.%m.%d").strftime("%Y-%m-%d"),
                "close": _parse_float(_clean(cells[1])),
                "diff": diff_value,
                "rate": _parse_float(_clean(cells[3])),
                "volume": int(_clean(cells[4]).replace(",", "")),
                "trade_value": int(_clean(cells[5]).replace(",", "")),
            }
        )
        if len(rows) >= days:
            break
    if not rows:
        raise RuntimeError("Naver returned no KOSPI history rows.")
    return rows


def main() -> int:
    days = 7
    if len(sys.argv) > 1:
        days = max(1, int(sys.argv[1]))

    html = fetch_html()
    rows = parse_rows(html, days)
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
