"""Non-destructive quality checks for candidate import rows."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from html import unescape
from typing import Iterable, Mapping, Optional, Tuple


_HTML_TAG_RE = re.compile(r"<[^>]*>")


def _has_visible_value(value: object) -> bool:
    """Return whether a field contains visible content, including HTML fields."""
    if value is None:
        return False
    text = unescape(str(value)).replace("\xa0", " ")
    text = _HTML_TAG_RE.sub(" ", text)
    return bool(text.strip())


def evaluate_card_completeness(item: object, *, grammar: bool = False) -> dict:
    """Score only required structural fields of an AI candidate card.

    This deliberately does not claim to verify translation, grammar, naturalness,
    or proficiency level. Those require a curated reference dataset or human
    review. The result is advisory and callers must never block an import from
    it alone.
    """
    if not isinstance(item, Mapping):
        return {"score": 0, "issues": ("invalid_card",), "complete": False}

    front_keys = ("pattern", "front") if grammar else ("front", "simplified")
    checks = (
        ("missing_front", front_keys, 40),
        ("missing_meaning", ("meaning",), 35),
        ("missing_example", ("example",), 25),
    )
    score = 0
    issues = []
    for issue, keys, weight in checks:
        if any(_has_visible_value(item.get(key)) for key in keys):
            score += weight
        else:
            issues.append(issue)
    return {"score": score, "issues": tuple(issues), "complete": not issues}


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
