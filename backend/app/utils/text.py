import re
from collections import Counter


WHITESPACE_RE = re.compile(r"\s+")
HTML_TAG_RE = re.compile(r"<[^>]+>")
URL_RE = re.compile(r"https?://\S+")
NON_WORD_RE = re.compile(r"[^\w\s가-힣]")


def normalize_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def strip_html(value: str) -> str:
    return normalize_whitespace(HTML_TAG_RE.sub(" ", value))


def clean_text(value: str) -> str:
    return normalize_whitespace(URL_RE.sub(" ", strip_html(value)))


def tokenize(value: str) -> list[str]:
    lowered = NON_WORD_RE.sub(" ", value.lower())
    return [token for token in lowered.split() if len(token) >= 2]


def top_keywords(tokens: list[str], stopwords: set[str], limit: int = 10) -> list[str]:
    filtered = [token for token in tokens if token not in stopwords]
    return [word for word, _count in Counter(filtered).most_common(limit)]
