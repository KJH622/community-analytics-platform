from __future__ import annotations

from app.utils.hashing import sha256_text
from app.utils.text import clean_text


def anonymize_author(author_id: str | None) -> str | None:
    if not author_id:
        return None
    return sha256_text(author_id)


def normalize_document(title: str, body: str) -> tuple[str, str]:
    return clean_text(title), clean_text(body)
