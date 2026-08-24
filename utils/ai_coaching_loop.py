"""Local Reviewer learning checkpoints that never mutate Anki or call AI."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from .language_identity import try_normalize_language


CHECKPOINT_SCHEMA_VERSION = 1
COACHING_OUTCOMES = frozenset({"understood", "needs_practice"})
STUDY_MODES = frozenset({"qa", "vn", "wb", "pron", "lg"})


def _checkpoint_identity(card_context: Optional[Mapping[str, Any]]) -> tuple[str, str]:
    if not isinstance(card_context, Mapping):
        return "", ""
    card_id = str(card_context.get("card_id") or "").strip()[:100]
    study_mode = str(card_context.get("study_mode") or "").strip().casefold()
    if study_mode not in STUDY_MODES:
        return "", ""
    return card_id, study_mode


def build_reviewer_checkpoint(
    card_context: Optional[Mapping[str, Any]], outcome: str,
) -> dict:
    """Build one bounded checkpoint for an explicit current Reviewer card."""
    card_id, study_mode = _checkpoint_identity(card_context)
    language = try_normalize_language(
        card_context.get("language") if isinstance(card_context, Mapping) else None
    )
    normalized_outcome = str(outcome or "").strip().casefold()
    if not card_id or language is None:
        raise ValueError("Reviewer card context is required for a learning checkpoint")
    if normalized_outcome not in COACHING_OUTCOMES:
        raise ValueError("unsupported coaching outcome")
    return {
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "workspace": "reviewer",
        "outcome": normalized_outcome,
        "language": language,
        "card_id": card_id,
        "study_mode": study_mode,
        "side": str(card_context.get("side") or "question").strip().casefold()[:20],
    }


def latest_reviewer_checkpoint(
    messages: Sequence[Mapping[str, Any]],
    card_context: Optional[Mapping[str, Any]],
) -> Optional[dict]:
    """Return the newest valid local checkpoint for the current card + mode."""
    identity = _checkpoint_identity(card_context)
    if not all(identity):
        return None
    current_language = try_normalize_language(
        card_context.get("language") if isinstance(card_context, Mapping) else None
    )
    if current_language is None:
        return None
    for message in reversed(list(messages or ())):
        if (
            not isinstance(message, Mapping)
            or message.get("type") != "system_internal"
            or message.get("role") != "system"
        ):
            continue
        snapshot = message.get("context_snapshot")
        if not isinstance(snapshot, Mapping):
            continue
        try:
            schema_version = int(snapshot.get("checkpoint_schema_version") or 0)
        except (TypeError, ValueError):
            continue
        if (
            schema_version != CHECKPOINT_SCHEMA_VERSION
            or snapshot.get("workspace") != "reviewer"
            or str(snapshot.get("outcome") or "") not in COACHING_OUTCOMES
            or _checkpoint_identity(snapshot) != identity
            or try_normalize_language(snapshot.get("language")) != current_language
        ):
            continue
        return dict(snapshot)
    return None


__all__ = [
    "CHECKPOINT_SCHEMA_VERSION", "COACHING_OUTCOMES", "STUDY_MODES",
    "build_reviewer_checkpoint", "latest_reviewer_checkpoint",
]
