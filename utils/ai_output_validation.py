"""Language/mode schema identity and minimum semantic validation for AI cards."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from Language import LANG_CONFIG, LANG_GRAMMAR_CONFIG
from .language_identity import normalize_language


AI_OUTPUT_SCHEMA_VERSION = 3

_LEVEL_KEYS = {
    "japanese": frozenset({"jlptlevel"}),
    "chinese": frozenset({"hsk_level", "hsklevel"}),
    "korean": frozenset({"topik_level", "topiklevel"}),
    "english": frozenset({"cefr_level", "cefrlevel"}),
}
_ALL_LEVEL_KEYS = frozenset().union(*_LEVEL_KEYS.values())
_LEVEL_PATTERNS = {
    "japanese": re.compile(r"N[1-5]", re.IGNORECASE),
    "chinese": re.compile(r"(?:HSK[1-6]|HSK7-9)", re.IGNORECASE),
    "korean": re.compile(r"(?:TOPIK\s*(?:I|II)|[1-6])", re.IGNORECASE),
    "english": re.compile(r"[ABC][12]", re.IGNORECASE),
}

_KANA_RE = re.compile(r"[\u3040-\u30ff]")
_HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_HANGUL_RE = re.compile(r"[\uac00-\ud7af\u1100-\u11ff]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_PLACEHOLDER_RE = re.compile(
    r"^(?:todo|tbd|n/?a|none|null|placeholder|<[^>]+>|\[[^]]*placeholder[^]]*\]|[-?â€¦]+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CardValidationIssue:
    index: int
    category: str


@dataclass(frozen=True)
class CardValidationReport:
    valid_cards: tuple[dict, ...]
    invalid: tuple[CardValidationIssue, ...]
    duplicate_count: int
    language: str
    kind: str
    schema_version: int = AI_OUTPUT_SCHEMA_VERSION

    @property
    def raw_count(self) -> int:
        return len(self.valid_cards) + len(self.invalid) + self.duplicate_count


def _visible(value: Any) -> bool:
    return bool(str(value or "").strip())


def _identity(card: Mapping[str, Any], kind: str) -> str:
    keys = ("pattern", "front") if kind == "grammar" else ("front", "simplified")
    for key in keys:
        if _visible(card.get(key)):
            return str(card[key]).strip()
    return ""


def _dedupe_key(card: Mapping[str, Any], kind: str) -> tuple[str, str]:
    identity = re.sub(r"[\W_]+", "", _identity(card, kind).casefold())
    meaning = re.sub(r"[\W_]+", "", str(card.get("meaning") or "").casefold())
    return identity, meaning


def _script_counts(value: Any) -> tuple[int, int, int, int]:
    text = str(value or "")
    return (
        len(_KANA_RE.findall(text)), len(_HAN_RE.findall(text)),
        len(_HANGUL_RE.findall(text)), len(_LATIN_RE.findall(text)),
    )


def _script_contradiction(value: Any, lang: str, *, example: bool) -> bool:
    kana, han, hangul, latin = _script_counts(value)
    significant = kana + han + hangul + latin
    if not significant:
        return False
    if lang == "english":
        return bool(hangul or kana >= 2 or (han >= 2 and latin == 0))
    if lang == "chinese":
        return bool(kana or hangul)
    if lang == "japanese":
        return bool(hangul)
    # Hanja headwords remain possible. A sentence made only of Han is a
    # high-confidence contradiction for modern Korean learning content.
    return bool(
        kana
        or ((example and han >= 3) or (not example and han >= 4))
        and hangul == 0 and latin == 0
    )


def _content_language_issue(card: Mapping[str, Any], lang: str, kind: str) -> str | None:
    identity_keys = ("pattern",) if kind == "grammar" else ("front", "simplified", "traditional")
    for key in identity_keys:
        if _visible(card.get(key)) and _script_contradiction(card[key], lang, example=False):
            return "content_language_mismatch"
    for key, value in card.items():
        normalized = str(key).casefold().replace("-", "_")
        if not re.fullmatch(r"example(?:_?[2-4])?", normalized):
            continue
        if _visible(value) and _script_contradiction(value, lang, example=True):
            return "example_language_mismatch"
    return None


def _validate_one(
    card: Any, *, lang: str, kind: str, require_example: bool,
) -> str | None:
    if not isinstance(card, Mapping):
        return "not_an_object"
    if set(card) == {"_comment"}:
        return "comment_sentinel"

    expected_levels = _LEVEL_KEYS[lang]
    for key in _ALL_LEVEL_KEYS - expected_levels:
        if _visible(card.get(key)):
            return "schema_language_mismatch"

    identity = _identity(card, kind)
    if not identity:
        if kind == "vocab" and _visible(card.get("pattern")):
            return "grammar_in_vocab_flow"
        return "missing_identity"
    if _PLACEHOLDER_RE.fullmatch(identity):
        return "placeholder_identity"
    if not _visible(card.get("meaning")):
        return "missing_meaning"
    if _PLACEHOLDER_RE.fullmatch(str(card.get("meaning") or "").strip()):
        return "placeholder_meaning"

    if kind == "grammar":
        if not (_visible(card.get("usage")) or _visible(card.get("explanation"))):
            if any(_visible(card.get(key)) for key in ("usage_pattern", "usage_note", "collocation")):
                return "vocab_in_grammar_flow"
            return "missing_grammar_function"
    elif _visible(card.get("pattern")) and not any(
        _visible(card.get(key)) for key in ("front", "simplified")
    ):
        return "grammar_in_vocab_flow"

    level_key = next(
        (key for key in (*expected_levels, "level") if _visible(card.get(key))),
        None,
    )
    if level_key is not None:
        value = str(card[level_key]).strip().upper()
        if not _LEVEL_PATTERNS[lang].fullmatch(value):
            return "invalid_level"
    if require_example and not _visible(card.get("example")):
        return "missing_primary_example"
    return _content_language_issue(card, lang, kind)


def validate_ai_cards(
    cards: Sequence[Any], *, lang: str, kind: str, require_example: bool = False,
) -> CardValidationReport:
    """Validate cards without coercing fields or inventing missing content."""
    lang = normalize_language(lang)
    if lang not in LANG_CONFIG or kind not in {"vocab", "grammar"}:
        raise ValueError("unsupported language or card kind")
    # Accessing the language registry here makes it the authoritative schema
    # identity boundary, including officially supported historical aliases.
    config = (LANG_GRAMMAR_CONFIG if kind == "grammar" else LANG_CONFIG)[lang]
    expected_level = config.get("level_json_key")
    if expected_level not in _LEVEL_KEYS[lang]:
        raise ValueError("language config has an inconsistent level_json_key")

    valid = []
    invalid = []
    seen = set()
    duplicate_count = 0
    for index, card in enumerate(cards):
        category = _validate_one(
            card, lang=lang, kind=kind, require_example=require_example,
        )
        if category:
            invalid.append(CardValidationIssue(index, category))
            continue
        copied = dict(card)
        key = _dedupe_key(copied, kind)
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        valid.append(copied)
    return CardValidationReport(
        tuple(valid), tuple(invalid), duplicate_count, lang, kind,
    )


def cache_payload_is_compatible(cards: Any, *, lang: str, kind: str) -> bool:
    """Reject malformed, partial, wrong-language, or pre-contract cache data."""
    if not isinstance(cards, list):
        return False
    report = validate_ai_cards(cards, lang=lang, kind=kind)
    return bool(cards) and len(report.valid_cards) == len(cards) and not report.invalid


__all__ = [
    "AI_OUTPUT_SCHEMA_VERSION", "CardValidationIssue", "CardValidationReport",
    "cache_payload_is_compatible", "validate_ai_cards",
]
