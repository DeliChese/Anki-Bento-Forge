"""Pure Usage Guide V1 normalization and deterministic quality checks."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence


USAGE_GUIDE_FIELDS = ("usage_pattern", "usage_note", "collocation")
_EMPTY_MARKERS = frozenset({
    "", "-", "?", "n/a", "na", "none", "null", "undefined", "unknown",
    "tbd", "todo", "not available", "not applicable",
})
_SECOND_EXAMPLE_FIELDS = (
    "example_2", "example_2_vn", "example_2_pinyin",
    "example_2_romanization", "example2", "example2_vn",
)
_GENERIC_PREPOSITION_NOTE_RE = re.compile(
    r"^thường dùng với giới từ\s*['\"]?([a-z]+)['\"]?\.?$",
    re.IGNORECASE,
)


def _clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _comparison_key(value: object) -> str:
    text = unicodedata.normalize("NFKC", _clean_text(value)).casefold()
    return re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE)


def _is_empty_marker(value: object) -> bool:
    return _clean_text(value).casefold() in _EMPTY_MARKERS


def _note_only_repeats_pattern(note: str, pattern: object) -> bool:
    """Drop only the proven low-value English preposition restatement."""
    match = _GENERIC_PREPOSITION_NOTE_RE.fullmatch(note)
    if not match:
        return False
    return bool(re.search(rf"\b{re.escape(match.group(1))}\b", _clean_text(pattern), re.IGNORECASE))


def _first_collocation(value: object) -> str:
    """Return one displayable ``phrase — meaning`` candidate at most."""
    if isinstance(value, Mapping):
        phrase = _clean_text(value.get("phrase"))
        meaning = _clean_text(value.get("meaning"))
        return f"{phrase} — {meaning}" if phrase and meaning else ""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for candidate in value:
            cleaned = _first_collocation(candidate)
            if cleaned:
                return cleaned
        return ""
    lines = str(value or "").splitlines() if value is not None else []
    first_line = lines[0] if lines else ""
    return re.sub(r"^[\s•*\-–—\d.)]+", "", first_line).strip()


def _collocation_repeats_pattern(collocation: str, pattern: object) -> bool:
    """Detect an exact lexical phrase already embedded in the pattern field."""
    phrase, separator, _meaning = collocation.partition(" — ")
    if not separator:
        return False
    phrase_key = _comparison_key(phrase)
    pattern_key = _comparison_key(pattern)
    return len(phrase_key) >= 4 and phrase_key in pattern_key


def normalize_usage_guide_card(card: object) -> object:
    """Normalize optional guide fields without mutating the AI response object.

    Empty placeholders are omitted, only the first collocation is retained, and
    repeated optional content is removed. If both examples are identical, the
    second example bundle is omitted so duplicate text never reaches a note.
    """
    if not isinstance(card, Mapping):
        return card

    normalized = dict(card)
    comparison_values = {
        _comparison_key(normalized.get("example")),
        _comparison_key(normalized.get("example_2")),
    }
    comparison_values.discard("")

    for field in USAGE_GUIDE_FIELDS:
        raw = normalized.get(field)
        value = _first_collocation(raw) if field == "collocation" else _clean_text(raw)
        key = _comparison_key(value)
        if (
            _is_empty_marker(value)
            or not key
            or key in comparison_values
            or (field == "collocation" and " — " not in value)
            or (
                field == "collocation"
                and _collocation_repeats_pattern(value, normalized.get("usage_pattern"))
            )
            or (
                field == "usage_note"
                and _note_only_repeats_pattern(value, normalized.get("usage_pattern"))
            )
        ):
            normalized.pop(field, None)
            continue
        normalized[field] = value
        comparison_values.add(key)

    if (
        _comparison_key(normalized.get("example"))
        and _comparison_key(normalized.get("example"))
        == _comparison_key(normalized.get("example_2"))
    ):
        for field in _SECOND_EXAMPLE_FIELDS:
            normalized.pop(field, None)

    return normalized


def normalize_usage_guide_cards(cards: Sequence[object]) -> list[object]:
    """Normalize a parsed AI vocabulary response while preserving row order."""
    return [normalize_usage_guide_card(card) for card in cards]


def evaluate_usage_guide_card(card: object) -> dict:
    """Return observable Usage Guide issues for corpus and regression review."""
    if not isinstance(card, Mapping):
        return {"score": 0, "issues": ("invalid_card",), "valid": False}

    issues = []
    seen = set()
    example_keys = {
        _comparison_key(card.get("example")),
        _comparison_key(card.get("example_2")),
    }
    example_keys.discard("")
    if len(example_keys) == 1 and card.get("example") and card.get("example_2"):
        issues.append("duplicate_examples")

    for field in USAGE_GUIDE_FIELDS:
        if field not in card:
            continue
        value = card.get(field)
        cleaned = _first_collocation(value) if field == "collocation" else _clean_text(value)
        key = _comparison_key(cleaned)
        if _is_empty_marker(cleaned) or not key:
            issues.append(f"empty_{field}")
            continue
        if key in seen or key in example_keys:
            issues.append(f"duplicate_{field}")
        seen.add(key)

    collocation = _first_collocation(card.get("collocation"))
    if collocation and " — " not in collocation:
        issues.append("collocation_missing_meaning")
    raw_collocation = card.get("collocation")
    if isinstance(raw_collocation, Sequence) and not isinstance(raw_collocation, (str, bytes, bytearray)):
        if len(raw_collocation) > 1:
            issues.append("multiple_collocations")
    elif isinstance(raw_collocation, str) and len(raw_collocation.splitlines()) > 1:
        issues.append("multiple_collocations")

    issues = tuple(dict.fromkeys(issues))
    return {
        "score": max(0, 100 - 20 * len(issues)),
        "issues": issues,
        "valid": not issues,
    }


__all__ = [
    "USAGE_GUIDE_FIELDS",
    "evaluate_usage_guide_card",
    "normalize_usage_guide_card",
    "normalize_usage_guide_cards",
]
