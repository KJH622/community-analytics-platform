import re
from html import unescape

from bs4 import BeautifulSoup


WHITESPACE_RE = re.compile(r"\s+")
URL_RE = re.compile(r"https?://\S+")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = unescape(value)
    soup = BeautifulSoup(value, "html.parser")
    text = soup.get_text(" ")
    text = URL_RE.sub(" ", text)
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def canonicalize_url(url: str) -> str:
    return url.split("?")[0].rstrip("/")
