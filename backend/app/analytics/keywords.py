from __future__ import annotations

import re
from collections import Counter
from pathlib import Path


TOKEN_RE = re.compile(r"[A-Za-z0-9가-힣]{2,}")


def load_word_list(filename: str) -> set[str]:
    base_dir = Path(__file__).resolve().parent / "lexicons"
    path = base_dir / filename
    with open(path, "r", encoding="utf-8") as file:
        return {
            line.strip().lower()
            for line in file
            if line.strip() and not line.strip().startswith("#")
        }


STOPWORDS = load_word_list("stopwords.txt")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def extract_keywords(text: str, top_k: int = 8) -> list[str]:
    tokens = [token for token in tokenize(text) if token not in STOPWORDS]
    counts = Counter(tokens)
    return [token for token, _ in counts.most_common(top_k)]
