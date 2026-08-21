"""Validated snapshot artifacts produced by explicit Study Session Card Mode."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from .ai_output_validation import AI_OUTPUT_SCHEMA_VERSION, validate_ai_cards
from .language_identity import normalize_language


ARTIFACT_COMPATIBILITY_CURRENT = "current"
ARTIFACT_COMPATIBILITY_STALE = "stale"


def artifact_is_compatible(artifact: Any) -> bool:
    """Return whether an artifact may enter the current Factory contract."""
    if not isinstance(artifact, dict):
        return False
    try:
        schema = int(artifact.get("schema_version") or 0)
    except (TypeError, ValueError):
        return False
    compatibility = str(artifact.get("compatibility") or "").strip().lower()
    return (
        schema == AI_OUTPUT_SCHEMA_VERSION
        and compatibility in {"", ARTIFACT_COMPATIBILITY_CURRENT}
    )


def create_card_artifact(
    *,
    session_id: str,
    language: str,
    kind: str,
    cards: Sequence[dict],
    source_message_id: str,
) -> dict:
    """Validate once more before making an immutable-on-disk card snapshot."""
    language = normalize_language(language)
    source_message_id = str(source_message_id or "").strip()
    if not str(session_id or "").strip() or not source_message_id:
        raise ValueError("artifact provenance is incomplete")
    report = validate_ai_cards(
        list(cards), lang=language, kind=kind, require_example=True,
    )
    if (
        not report.valid_cards
        or report.invalid
        or report.duplicate_count
        or len(report.valid_cards) != len(cards)
    ):
        raise ValueError("card payload is not a complete validated artifact")
    normalized = [dict(card) for card in report.valid_cards]
    # An artifact is a snapshot. No semantic repair or caller-specific
    # normalization is allowed after this validation boundary.
    revalidated = validate_ai_cards(
        normalized, lang=language, kind=kind, require_example=True,
    )
    if revalidated.invalid or len(revalidated.valid_cards) != len(normalized):
        raise ValueError("card payload changed across artifact validation")
    return {
        "artifact_id": f"artifact_{uuid.uuid4().hex}",
        "session_id": str(session_id),
        "created_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "language": language,
        "kind": kind,
        "schema_version": AI_OUTPUT_SCHEMA_VERSION,
        "compatibility": ARTIFACT_COMPATIBILITY_CURRENT,
        "cards": [dict(card) for card in normalized],
        "source_message_id": source_message_id,
    }


def artifact_to_factory_payload(artifact: dict) -> tuple[str, str, list[dict]]:
    """Return a snapshot for Xưởng without network access or regeneration."""
    if not isinstance(artifact, dict):
        raise ValueError("invalid card artifact")
    if not artifact_is_compatible(artifact):
        raise ValueError("unsupported card artifact schema")
    language = normalize_language(artifact.get("language"))
    kind = str(artifact.get("kind") or "")
    cards = artifact.get("cards")
    report = validate_ai_cards(
        cards or [], lang=language, kind=kind, require_example=True,
    )
    if (
        not cards or report.invalid or report.duplicate_count
        or len(report.valid_cards) != len(cards)
    ):
        raise ValueError("card artifact is no longer compatible")
    return language, kind, [dict(card) for card in report.valid_cards]


def artifact_label(artifact: dict) -> str:
    kind = "Grammar" if artifact.get("kind") == "grammar" else "Vocabulary"
    language = str(artifact.get("language") or "").title()
    return f"{language} {kind} · {len(artifact.get('cards') or [])}"


__all__ = [
    "ARTIFACT_COMPATIBILITY_CURRENT", "ARTIFACT_COMPATIBILITY_STALE",
    "artifact_is_compatible", "artifact_label", "artifact_to_factory_payload",
    "create_card_artifact",
]
