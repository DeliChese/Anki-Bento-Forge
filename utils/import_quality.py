"""Non-destructive quality checks for candidate import rows."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Iterable, Optional, Tuple


def normalize_for_comparison(value: object) -> str:
    """Normalize display text for duplicate matching without changing card data."""
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE)


def near_duplicate_score(left: object, right: object) -> float:
    left_normalized = normalize_for_comparison(left)
    right_normalized = normalize_for_comparison(right)
    if not left_normalized or not right_normalized:
        return 0.0
    if left_normalized == right_normalized:
        return 1.0
    return SequenceMatcher(None, left_normalized, right_normalized, autojunk=False).ratio()


def find_near_duplicate(
    value: object,
    candidates: Iterable[object],
    *,
    threshold: float = 0.88,
) -> Optional[Tuple[str, float]]:
    """Return the closest likely duplicate, never deciding an automatic merge.

    Matching is constrained by first or last character before doing the more
    expensive similarity comparison.  This keeps a large deck scan practical.
    """
    normalized = normalize_for_comparison(value)
    if len(normalized) < 2:
        return None
    best = None
    for candidate in candidates:
        candidate_text = str(candidate or "").strip()
        candidate_normalized = normalize_for_comparison(candidate_text)
        if len(candidate_normalized) < 2 or candidate_normalized == normalized:
            continue
        if candidate_normalized[0] != normalized[0] and candidate_normalized[-1] != normalized[-1]:
            continue
        score = SequenceMatcher(None, normalized, candidate_normalized, autojunk=False).ratio()
        if score >= threshold and (best is None or score > best[1]):
            best = (candidate_text, round(score, 3))
    return best
