"""Explicit topic scope for intentional duplicate vocabulary notes.

The optional ``_bf_variant`` JSON metadata never changes a note type.  It is
stored as a Bento Forge-owned tag so the same headword can be learned in two
different topic contexts without weakening ordinary duplicate protection.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping, Sequence


VARIANT_KEY = "_bf_variant"
_VARIANT_TAG_PREFIX = "bento-forge::variant::"
_MAX_VARIANT_LENGTH = 120


class VariantScopeError(ValueError):
    """A requested topic scope cannot be represented safely as an Anki tag."""


def variant_key_for(card: Mapping[str, Any]) -> str:
    """Return the optional, normalized topic scope on one imported card."""
    value = unicodedata.normalize("NFKC", str(card.get(VARIANT_KEY) or "")).strip()
    if not value:
        return ""
    if len(value) > _MAX_VARIANT_LENGTH or "\n" in value or "\r" in value:
        raise VariantScopeError("invalid_variant_key")
    return value.casefold()


def variant_tag_for(card: Mapping[str, Any]) -> str:
    """Build the stable Bento Forge tag that persists one topic scope."""
    key = variant_key_for(card)
    if not key:
        return ""
    slug = re.sub(r"[^\w-]+", "-", key, flags=re.UNICODE).strip("-")
    if not slug:
        raise VariantScopeError("invalid_variant_key")
    return _VARIANT_TAG_PREFIX + slug


def note_matches_variant(note: Any, variant_key: str) -> bool:
    """Whether an existing note belongs to the same intentional topic scope."""
    tags = getattr(note, "tags", []) or []
    if not variant_key:
        return not any(str(tag).startswith(_VARIANT_TAG_PREFIX) for tag in tags)
    return variant_tag_for({VARIANT_KEY: variant_key}) in tags


def routing_tags(card: Mapping[str, Any]) -> tuple[str, ...]:
    """Return the one system-owned tag needed to preserve a topic scope."""
    tag = variant_tag_for(card)
    return (tag,) if tag else ()


def preserves_scoped_variants(cards: Sequence[Any]) -> bool:
    """Whether this import contains at least one intentional topic variant."""
    return any(
        isinstance(card, Mapping) and bool(variant_key_for(card))
        for card in cards
    )


__all__ = [
    "VARIANT_KEY", "VariantScopeError", "note_matches_variant",
    "preserves_scoped_variants", "routing_tags", "variant_key_for",
]
