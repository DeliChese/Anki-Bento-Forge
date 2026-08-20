"""Pure Language Card Quality V2 normalization and deterministic checks."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence


USAGE_GUIDE_FIELDS = ("usage_pattern", "usage_note", "collocation")
_EMPTY_MARKERS = frozenset({
    "", "-", "?", "n/a", "na", "none", "null", "undefined", "unknown",
    "tbd", "todo", "not available", "not applicable",
})
_MAX_GUIDE_ITEMS = 3
_ITEM_SPLIT_RE = re.compile(r"(?:<br\s*/?>|\r?\n)+", re.IGNORECASE)
_ITEM_PREFIX_RE = re.compile(r"^[\s•*\-–—\d.)]+")
_EXAMPLE_BUNDLES = {
    1: ("example", "example_vn", "example_pinyin", "example_romanization"),
    2: (
        "example_2", "example_2_vn", "example_2_pinyin", "example_2_romanization",
        "example2", "example2_vn", "example2_pinyin", "example2_romanization",
        "example2invietnamese",
    ),
    3: (
        "example_3", "example_3_vn", "example_3_pinyin", "example_3_romanization",
        "example3", "example3_vn", "example3_pinyin", "example3_romanization",
        "example3invietnamese",
    ),
    4: (
        "example_4", "example_4_vn", "example_4_pinyin", "example_4_romanization",
        "example4", "example4_vn", "example4_pinyin", "example4_romanization",
        "example4invietnamese",
    ),
}
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


def _iter_items(value: object):
    """Yield displayable items from legacy strings or structured AI output."""
    if isinstance(value, Mapping):
        phrase = _clean_text(value.get("phrase"))
        meaning = _clean_text(value.get("meaning"))
        if phrase and meaning:
            yield f"{phrase} — {meaning}"
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for candidate in value:
            yield from _iter_items(candidate)
        return
    for raw in _ITEM_SPLIT_RE.split(str(value or "")):
        cleaned = _ITEM_PREFIX_RE.sub("", raw).strip()
        if cleaned:
            yield cleaned


def _normalize_guide_items(value: object, *, collocation: bool = False) -> list[str]:
    items = []
    seen = set()
    for candidate in _iter_items(value):
        cleaned = _clean_text(candidate)
        key = _comparison_key(cleaned)
        if _is_empty_marker(cleaned) or not key or key in seen:
            continue
        if collocation and " — " not in cleaned:
            continue
        items.append(cleaned)
        seen.add(key)
        if len(items) == _MAX_GUIDE_ITEMS:
            break
    return items


def _first_example_value(card: Mapping, index: int) -> object:
    primary = "example" if index == 1 else f"example_{index}"
    aliases = (primary, f"example{index}") if index > 1 else (primary,)
    return next((card.get(key) for key in aliases if _clean_text(card.get(key))), "")


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

    Empty placeholders are omitted, guide values are serialized as at most
    three unique newline-separated items, and duplicate/orphan example bundles
    are removed. Existing one-item strings and two-example cards remain valid.
    """
    if not isinstance(card, Mapping):
        return card

    normalized = dict(card)
    comparison_values = {
        _comparison_key(_first_example_value(normalized, index))
        for index in range(1, 5)
    }
    comparison_values.discard("")

    for field in USAGE_GUIDE_FIELDS:
        raw = normalized.get(field)
        values = _normalize_guide_items(raw, collocation=field == "collocation")
        kept = []
        for value in values:
            key = _comparison_key(value)
            if (
                key in comparison_values
                or (
                    field == "collocation"
                    and _collocation_repeats_pattern(value, normalized.get("usage_pattern"))
                )
                or (
                    field == "usage_note"
                    and _note_only_repeats_pattern(value, normalized.get("usage_pattern"))
                )
            ):
                continue
            kept.append(value)
            comparison_values.add(key)
        if not kept:
            normalized.pop(field, None)
            continue
        normalized[field] = "\n".join(kept)

    seen_examples = set()
    for index in range(1, 5):
        key = _comparison_key(_first_example_value(normalized, index))
        if not key or key in seen_examples:
            if index > 1 or not key:
                for field in _EXAMPLE_BUNDLES[index]:
                    normalized.pop(field, None)
            continue
        seen_examples.add(key)

    return normalized


def normalize_usage_guide_cards(cards: Sequence[object]) -> list[object]:
    """Normalize a parsed AI vocabulary response while preserving row order."""
    return [normalize_usage_guide_card(card) for card in cards]


normalize_language_card = normalize_usage_guide_card
normalize_language_cards = normalize_usage_guide_cards


def evaluate_usage_guide_card(card: object) -> dict:
    """Return observable Usage Guide issues for corpus and regression review."""
    if not isinstance(card, Mapping):
        return {"score": 0, "issues": ("invalid_card",), "valid": False}

    issues = []
    seen = set()
    example_keys = set()
    for index in range(1, 5):
        raw_example = _first_example_value(card, index)
        key = _comparison_key(raw_example)
        if key and key in example_keys:
            issues.append("duplicate_examples")
        if key:
            example_keys.add(key)

    for field in USAGE_GUIDE_FIELDS:
        if field not in card:
            continue
        value = card.get(field)
        raw_items = list(_iter_items(value))
        cleaned_items = _normalize_guide_items(value, collocation=field == "collocation")
        if not cleaned_items:
            issues.append(f"empty_{field}")
            continue
        if len(raw_items) > _MAX_GUIDE_ITEMS:
            issues.append(f"too_many_{field}")
        raw_keys = [_comparison_key(item) for item in raw_items if _comparison_key(item)]
        if len(raw_keys) != len(set(raw_keys)):
            issues.append(f"duplicate_{field}")
        for cleaned in cleaned_items:
            key = _comparison_key(cleaned)
            if key in seen or key in example_keys:
                issues.append(f"duplicate_{field}")
            seen.add(key)
        if field == "collocation" and any(" — " not in item for item in raw_items):
            issues.append("collocation_missing_meaning")

    issues = tuple(dict.fromkeys(issues))
    return {
        "score": max(0, 100 - 20 * len(issues)),
        "issues": issues,
        "valid": not issues,
    }


__all__ = [
    "USAGE_GUIDE_FIELDS",
    "evaluate_usage_guide_card",
    "normalize_language_card",
    "normalize_language_cards",
    "normalize_usage_guide_card",
    "normalize_usage_guide_cards",
]
