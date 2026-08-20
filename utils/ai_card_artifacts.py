"""Validated snapshot artifacts produced by explicit Study Session Card Mode."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from .ai_output_validation import AI_OUTPUT_SCHEMA_VERSION, validate_ai_cards
from .ai_output_repairs import repair_vocabulary_cards
from .usage_guide import normalize_language_cards


def create_card_artifact(
    *,
    session_id: str,
    language: str,
    kind: str,
    cards: Sequence[dict],
    source_message_id: str,
) -> dict:
    """Validate once more before making an immutable-on-disk card snapshot."""
    report = validate_ai_cards(list(cards), lang=language, kind=kind)
    if (
        not report.valid_cards
        or report.invalid
        or report.duplicate_count
        or len(report.valid_cards) != len(cards)
    ):
        raise ValueError("card payload is not a complete validated artifact")
    normalized = list(report.valid_cards)
    normalized = (
        repair_vocabulary_cards(normalized, language)
        if kind == "vocab" else normalize_language_cards(normalized)
    )
    return {
        "artifact_id": f"artifact_{uuid.uuid4().hex}",
        "session_id": str(session_id),
        "created_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "language": language,
        "kind": kind,
        "schema_version": AI_OUTPUT_SCHEMA_VERSION,
        "cards": [dict(card) for card in normalized],
        "source_message_id": str(source_message_id),
    }


def artifact_to_factory_payload(artifact: dict) -> tuple[str, str, list[dict]]:
    """Return a snapshot for Xưởng without network access or regeneration."""
    if not isinstance(artifact, dict):
        raise ValueError("invalid card artifact")
    schema = int(artifact.get("schema_version") or 0)
    if schema > AI_OUTPUT_SCHEMA_VERSION or schema < 1:
        raise ValueError("unsupported card artifact schema")
    language = str(artifact.get("language") or "")
    kind = str(artifact.get("kind") or "")
    cards = artifact.get("cards")
    report = validate_ai_cards(cards or [], lang=language, kind=kind)
    if not cards or report.invalid or len(report.valid_cards) != len(cards):
        raise ValueError("card artifact is no longer compatible")
    return language, kind, [dict(card) for card in report.valid_cards]


def artifact_label(artifact: dict) -> str:
    kind = "Grammar" if artifact.get("kind") == "grammar" else "Vocabulary"
    language = str(artifact.get("language") or "").title()
    return f"{language} {kind} · {len(artifact.get('cards') or [])}"


__all__ = ["artifact_label", "artifact_to_factory_payload", "create_card_artifact"]
