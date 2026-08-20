"""Non-destructive quality checks for candidate import rows."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from html import unescape
from typing import Iterable, Mapping, Optional, Tuple


_HTML_TAG_RE = re.compile(r"<[^>]*>")
_CHINESE_TEXT_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
_JAPANESE_TEXT_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff\u3040-\u30ff]")
_KOREAN_TEXT_RE = re.compile(r"[\uac00-\ud7af]")
_PATTERN_LITERAL_RE = re.compile(r"^[\u3400-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]{2,}$")

# Curated exact-form sets only. This intentionally avoids fuzzy semantic
# guessing: a warning needs both a known contrast and an exact same-deck peer.
_CONFUSION_GROUPS = {
    "english": (
        ("affect", "effect"), ("economic", "economical"),
        ("sensible", "sensitive"),
    ),
    "japanese": (
        ("気になる", "気にする"), ("見える", "見られる"),
        ("開く", "開ける"),
    ),
    "chinese": (
        ("了解", "理解"), ("发现", "发觉"),
        ("提高", "提升"), ("适合", "合适"),
    ),
    "korean": (
        ("늘다", "늘리다"), ("맞다", "맞추다"),
        ("알다", "알아보다"),
    ),
}

_PLACEHOLDERS = frozenset({
    "-", "?", "n/a", "na", "none", "null", "undefined", "unknown",
    "tbd", "todo", "not available", "not applicable", "chua co", "khong ro",
})


def _has_visible_value(value: object) -> bool:
    """Return whether a field contains visible content, including HTML fields."""
    if value is None:
        return False
    text = unescape(str(value)).replace("\xa0", " ")
    text = _HTML_TAG_RE.sub(" ", text)
    return bool(text.strip())


def _visible_text(value: object) -> str:
    """Return visible text from a field without changing the original card data."""
    if value is None:
        return ""
    text = unescape(str(value)).replace("\xa0", " ")
    return _HTML_TAG_RE.sub(" ", text).strip()


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


def detect_card_warnings(
    item: object,
    *,
    lang: str = "",
    grammar: bool = False,
) -> tuple[str, ...]:
    """Detect deterministic, advisory problems in an AI candidate card.

    These rules deliberately avoid claiming that a translation is correct or an
    example is natural.  They catch only observable output mistakes, such as a
    placeholder value, an example written in the wrong script, or a Chinese
    headword that is not used in its example.  Callers must keep import enabled
    because every result remains a prompt for human review.
    """
    if not isinstance(item, Mapping):
        return ("invalid_card",)

    front_keys = ("pattern", "front") if grammar else ("front", "simplified")
    front = next((_visible_text(item.get(key)) for key in front_keys
                  if _has_visible_value(item.get(key))), "")
    meaning = _visible_text(item.get("meaning"))
    example = _visible_text(item.get("example"))
    warnings = []
    examples = [example]
    examples.extend(
        _visible_text(item.get(f"example_{index}") or item.get(f"example{index}"))
        for index in (2, 3, 4)
    )
    example_keys = [normalize_for_comparison(value) for value in examples if value]
    if len(example_keys) != len(set(example_keys)):
        warnings.append("duplicate_examples")

    for field, value in (("front", front), ("meaning", meaning), ("example", example)):
        if value.casefold() in _PLACEHOLDERS:
            warnings.append(f"placeholder_{field}")

    target = normalize_for_comparison(front)
    normalized_meaning = normalize_for_comparison(meaning)
    normalized_example = normalize_for_comparison(example)
    if len(target) >= 2 and target == normalized_meaning:
        warnings.append("meaning_repeats_front")

    if example and front:
        expected_script = {
            "chinese": _CHINESE_TEXT_RE,
            "japanese": _JAPANESE_TEXT_RE,
            "korean": _KOREAN_TEXT_RE,
        }.get(lang)
        if expected_script and expected_script.search(front) and not expected_script.search(example):
            warnings.append("example_wrong_script")

        # Chinese words do not inflect, so an exact headword check is reliable.
        # Japanese/Korean vocabulary can conjugate, therefore they are not
        # checked here to avoid misleading users with false positives.
        if (
            lang == "chinese"
            and len(target) >= 2
            and _CHINESE_TEXT_RE.search(front)
            and target not in normalized_example
        ):
            warnings.append("target_not_in_example")

        # Grammar is checked only for a literal pattern.  Formula-style
        # patterns (for example "V-ながら") are intentionally left to review.
        literal_pattern = re.sub(r"[〜～~\s]", "", front)
        if grammar and _PATTERN_LITERAL_RE.fullmatch(literal_pattern):
            if normalize_for_comparison(literal_pattern) not in normalized_example:
                warnings.append("pattern_not_in_example")

        if target and normalized_example == target:
            warnings.append("example_is_only_target")

    # Pronunciation is a core learning aid for CJK cards.  Keep this advisory
    # so existing notes remain importable, but surface omissions before a card
    # reaches a learner's review queue.
    pronunciation_field = {
        "chinese": "pinyin",
        "english": "pronunciation",
        "korean": "romanization",
    }.get(lang)
    if lang == "japanese":
        pronunciation_field = "reading" if grammar else "furigana"
        # Kana-only vocabulary does not need a separate furigana reading.
        if not _CHINESE_TEXT_RE.search(front):
            pronunciation_field = None
    if pronunciation_field and not _has_visible_value(item.get(pronunciation_field)):
        warnings.append(f"missing_{pronunciation_field}")
    if lang == "korean" and "-" in _visible_text(item.get("romanization")):
        warnings.append("romanization_contains_hyphen")

    return tuple(dict.fromkeys(warnings))


def evaluate_card_candidate(
    item: object,
    *,
    lang: str = "",
    grammar: bool = False,
    existing_terms: Iterable[object] = (),
) -> dict:
    """Return structural score plus deterministic advisory warnings for preview."""
    completeness = evaluate_card_completeness(item, grammar=grammar)
    warnings = () if not isinstance(item, Mapping) else detect_card_warnings(
        item, lang=lang, grammar=grammar,
    )
    confusion_candidates = ()
    if isinstance(item, Mapping) and not grammar:
        front = item.get("front") or item.get("simplified")
        confusion_candidates = find_confusion_candidates(front, existing_terms, lang=lang)
        if confusion_candidates:
            warnings = (*warnings, "confusion_candidate")
    issues = tuple(dict.fromkeys((*completeness["issues"], *warnings)))
    return {
        **completeness,
        "issues": issues,
        "warnings": warnings,
        "confusion_candidates": confusion_candidates,
        "has_warnings": bool(issues),
    }


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


def find_confusion_candidates(
    value: object,
    candidates: Iterable[object],
    *,
    lang: str,
) -> tuple[str, ...]:
    """Return curated same-deck contrasts; never mutate or block an import."""
    target = normalize_for_comparison(value)
    if not target:
        return ()
    candidate_by_key = {
        normalize_for_comparison(candidate): str(candidate).strip()
        for candidate in candidates or ()
        if normalize_for_comparison(candidate)
    }
    matches = []
    for group in _CONFUSION_GROUPS.get(lang, ()):
        normalized_group = {normalize_for_comparison(term): term for term in group}
        if target not in normalized_group:
            continue
        for key in normalized_group:
            if key != target and key in candidate_by_key:
                matches.append(candidate_by_key[key])
    return tuple(dict.fromkeys(matches))


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
