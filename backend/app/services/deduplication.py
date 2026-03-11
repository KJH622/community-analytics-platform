from difflib import SequenceMatcher


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()


def is_probable_duplicate(
    title_similarity: float, same_hash: bool, threshold: float = 0.92
) -> bool:
    return same_hash or title_similarity >= threshold
