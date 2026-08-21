"""Canonical internal identity for supported learning languages."""

from __future__ import annotations

from typing import Any, Optional


CANONICAL_LANGUAGES = frozenset({"japanese", "chinese", "korean", "english"})
_LANGUAGE_ALIASES = {
    "japanese": "japanese", "ja": "japanese",
    "chinese": "chinese", "zh": "chinese",
    "korean": "korean", "ko": "korean",
    "english": "english", "en": "english",
}


def normalize_language(value: Any) -> str:
    """Return a canonical language or reject missing/unsupported ownership."""
    key = str(value).strip().casefold() if value is not None else ""
    language = _LANGUAGE_ALIASES.get(key)
    if language is None:
        raise ValueError("unsupported or missing language")
    return language


def try_normalize_language(value: Any) -> Optional[str]:
    """Fail-closed normalization for persisted data that should be skipped."""
    try:
        return normalize_language(value)
    except ValueError:
        return None


__all__ = ["CANONICAL_LANGUAGES", "normalize_language", "try_normalize_language"]
