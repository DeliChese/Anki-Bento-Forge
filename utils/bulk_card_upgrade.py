"""Pure planning and persistence contracts for collection-wide card upgrades."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .card_upgrade import (
    apply_card_upgrade, detect_note_field, proposed_field_changes, upgrade_is_available,
)


def snapshot_from_note(note, cfg: Mapping, *, language: str, kind: str) -> dict:
    """Build the minimum safe upgrade snapshot for one existing Anki note."""
    values = {
        str(name): str(value or "").strip()
        for name, value in (note.items() if callable(getattr(note, "items", None)) else [])
    }
    field_map = dict(cfg.get("json_field_map") or {})
    snapshot = {
        "language": str(language),
        "card_kind": str(kind),
        "note_id": int(getattr(note, "id", 0) or 0),
        "note_type": str((note.model() or {}).get("name") or ""),
        "bento_field_values": values,
    }
    for json_key, field_name in field_map.items():
        value = values.get(str(field_name))
        if value:
            snapshot[str(json_key)] = value
    detect_field = detect_note_field(cfg)
    snapshot["current_target"] = values.get(detect_field, "")
    snapshot["meaning"] = snapshot.get("meaning", "")
    snapshot["quality_version"] = values.get("Bento Quality Version", "")
    return snapshot


def build_bulk_upgrade_plan(notes: Sequence[object], cfg: Mapping, *, language: str, kind: str) -> dict:
    """Classify current-model notes without mutating them or calling AI."""
    snapshots = [snapshot_from_note(note, cfg, language=language, kind=kind) for note in notes]
    actionable = [
        snapshot for snapshot in snapshots
        if snapshot.get("note_id") and snapshot.get("current_target") and upgrade_is_available(snapshot)
    ]
    return {
        "total": len(snapshots),
        "ai_required": len(actionable),
        "template_only": len(snapshots) - len(actionable),
        "snapshots": actionable,
    }


def apply_bulk_upgrade_candidate(col, snapshot: Mapping, candidate: Mapping, cfg: Mapping) -> dict:
    """Persist all non-identity AI changes for one planned note, undo-aware upstream."""
    fields = dict(snapshot.get("bento_field_values") or {})
    changes = proposed_field_changes(fields, candidate, cfg)
    return apply_card_upgrade(
        col,
        int(snapshot["note_id"]),
        str(snapshot["current_target"]),
        detect_note_field(cfg),
        changes,
        {},
        True,
    )
