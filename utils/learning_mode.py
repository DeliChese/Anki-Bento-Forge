"""Learning-mode contract and collection-config persistence.

This module deliberately has no Anki or Qt imports so callers can decide when
collection writes are appropriate.  V18 keeps language as the compatibility
default for every deck that has not explicitly selected a learning mode.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Tuple


DEFAULT_LEARNING_MODE = "language"
LEARNING_MODE_CONFIG_KEY = "bento_forge_learning_mode_by_deck"
LEARNING_MODES = ("language", "knowledge")
LANGUAGE_KINDS = ("vocab", "grammar", "collocation")

# Knowledge is retained as a private beta, but deliberately has no UI entry
# while Bento Forge focuses on the language-learning workflow.  Keep the
# persisted mode and its domain code intact so a future opt-in can reactivate
# it without migrating or discarding a user's existing Knowledge drafts.
KNOWLEDGE_MODE_ENABLED = False


@dataclass(frozen=True)
class LearningModeSpec:
    """Stable product-level description of one learning mode."""

    name: str
    uses_language: bool
    kinds: Tuple[str, ...]


LEARNING_MODE_REGISTRY = {
    "language": LearningModeSpec("language", uses_language=True, kinds=LANGUAGE_KINDS),
    "knowledge": LearningModeSpec("knowledge", uses_language=False, kinds=()),
}


def is_learning_mode_available(mode: object) -> bool:
    """Whether a recognized mode may be selected from the current UI.

    Availability is intentionally separate from normalization/persistence:
    old deck configuration containing ``knowledge`` remains readable while
    the beta is dormant.
    """
    normalized = normalize_learning_mode(mode)
    return normalized == "language" or (
        normalized == "knowledge" and KNOWLEDGE_MODE_ENABLED
    )


def normalize_learning_mode(value: object) -> str:
    """Return a supported mode, preserving V17 behavior for unknown values."""
    return value if value in LEARNING_MODES else DEFAULT_LEARNING_MODE


def get_learning_mode(conf: Mapping[str, object], deck_id: Optional[object] = None) -> str:
    """Read a deck default without mutating old collections or global config."""
    if deck_id is None:
        return DEFAULT_LEARNING_MODE
    mode_by_deck = conf.get(LEARNING_MODE_CONFIG_KEY, {})
    if not isinstance(mode_by_deck, Mapping):
        return DEFAULT_LEARNING_MODE
    return normalize_learning_mode(mode_by_deck.get(str(deck_id)))


def set_learning_mode(conf: MutableMapping[str, object], mode: object,
                      deck_id: Optional[object] = None) -> str:
    """Persist one explicit deck default and return its normalized value.

    A missing deck id intentionally does not create a global default: V18's
    contract is deck-scoped and existing decks must continue to mean language.
    """
    normalized = normalize_learning_mode(mode)
    if deck_id is None:
        return normalized
    existing = conf.get(LEARNING_MODE_CONFIG_KEY, {})
    mode_by_deck = dict(existing) if isinstance(existing, Mapping) else {}
    mode_by_deck[str(deck_id)] = normalized
    conf[LEARNING_MODE_CONFIG_KEY] = mode_by_deck
    return normalized
