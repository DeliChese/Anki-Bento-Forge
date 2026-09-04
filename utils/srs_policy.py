"""SRS layout policy and safe migration helpers.

This module is deliberately independent of ``aqt``/Qt.  Callers provide the
collection and model manager so migration remains testable and undo can be
owned by the Anki UI boundary.
"""

from __future__ import annotations

from dataclasses import dataclass


SRS_FIELD = "SRS Independent"
SRS_LAYOUTS = ("combo", "independent")


@dataclass(frozen=True)
class SrsMigrationResult:
    matched_notes: int
    changed_notes: int


def normalize_srs_layout(layout) -> str:
    return layout if layout in SRS_LAYOUTS else "combo"


def apply_srs_layout_to_config(cfg: dict, layout: str) -> dict:
    """Return a copy with defaults used only when creating new notes."""
    result = dict(cfg)
    defaults = dict(result.get("note_defaults") or {})
    defaults[SRS_FIELD] = "1" if normalize_srs_layout(layout) == "independent" else ""
    result["note_defaults"] = defaults
    return result


def needs_legacy_srs_migration(model) -> bool:
    """Old multi-template vocabulary models already had independent cards."""
    if not model or len(model.get("tmpls") or []) <= 1:
        return False
    fields = {field.get("name") for field in model.get("flds") or []}
    templates = (model.get("tmpls") or [])[1:5]
    uses_new_conditions = all(
        "{{#SRS Independent}}" in str(template.get("qfmt") or "")
        for template in templates
    )
    return SRS_FIELD not in fields or not uses_new_conditions


def prepare_legacy_srs_model(collection, model_manager, model) -> SrsMigrationResult:
    """Mark notes from an old multi-card model before templates become conditional.

    Existing cards are never removed.  Their ordinals and review history remain
    intact; the marker merely keeps their new conditional templates rendered.
    The caller must create an Anki checkpoint before invoking this function.
    """
    if not needs_legacy_srs_migration(model):
        return SrsMigrationResult(matched_notes=0, changed_notes=0)

    fields = {field.get("name") for field in model.get("flds") or []}
    if SRS_FIELD not in fields:
        model_manager.add_field(model, model_manager.new_field(SRS_FIELD))
        model_manager.save(model)
    note_ids = list(collection.find_notes(f'"mid:{model["id"]}"'))
    changed = 0
    for note_id in note_ids:
        note = collection.get_note(note_id)
        if not str(note[SRS_FIELD] or "").strip():
            note[SRS_FIELD] = "1"
            update_note = getattr(collection, "update_note", None)
            if callable(update_note):
                update_note(note)
            else:
                note.flush()
            changed += 1
    return SrsMigrationResult(matched_notes=len(note_ids), changed_notes=changed)


def migrate_deck_to_independent(collection, model, deck_id: int) -> SrsMigrationResult:
    """Enable independent cards for this model's notes in one deck.

    The operation is idempotent.  Card ``ord=0`` is preserved as recognition;
    Anki only generates the four newly eligible card templates.
    """
    if not model:
        return SrsMigrationResult(matched_notes=0, changed_notes=0)
    fields = {field.get("name") for field in model.get("flds") or []}
    if SRS_FIELD not in fields:
        raise ValueError(f"Model is missing required field: {SRS_FIELD}")

    note_ids = list(collection.db.list(
        "select distinct n.id from notes n join cards c on c.nid=n.id "
        "where n.mid=? and c.did=?",
        model["id"],
        deck_id,
    ))
    changed_ids = []
    for note_id in note_ids:
        note = collection.get_note(note_id)
        if str(note[SRS_FIELD] or "").strip():
            continue
        note[SRS_FIELD] = "1"
        note.flush()
        changed_ids.append(note_id)

    if changed_ids:
        generate = getattr(collection, "gen_cards", None)
        if callable(generate):
            generate(changed_ids)
    return SrsMigrationResult(
        matched_notes=len(note_ids),
        changed_notes=len(changed_ids),
    )
