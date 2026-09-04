"""Undo-aware collection mutations for versioned Reviewer examples."""

from __future__ import annotations

from .example_versions import (
    HISTORY_FIELD,
    active_record,
    append_version,
    delete_version,
    example_field_names,
    parse_history,
    record_from_note,
    required_example_fields,
    select_version,
    serialize_history,
    slot_state,
)


def _ensure_fields(col, note_id: int, language: str):
    note = col.get_note(note_id)
    model = note.model()
    existing = {field["name"] for field in model.get("flds", [])}
    missing = [field for field in required_example_fields(language) if field not in existing]
    if missing:
        for name in missing:
            col.models.add_field(model, col.models.new_field(name))
        col.models.save(model)
        note = col.get_note(note_id)
    return note


def read_example_state(note, language: str, slot: int) -> dict:
    try:
        raw = note[HISTORY_FIELD]
    except Exception:
        raw = ""
    history = parse_history(raw)
    return slot_state(history, slot, record_from_note(note, language, slot))


def _write_active(note, language: str, slot: int, state: dict) -> None:
    fields = example_field_names(language, slot)
    record = active_record(state) or {key: "" for key in fields}
    for key, field_name in fields.items():
        try:
            note[field_name] = str(record.get(key) or "")
        except Exception:
            continue


def _persist(col, note, history: dict, language: str, slot: int, state: dict) -> dict:
    note[HISTORY_FIELD] = serialize_history(history)
    _write_active(note, language, slot, state)
    update_note = getattr(col, "update_note", None)
    if callable(update_note):
        update_note(note)
    else:
        note.flush()
    return {
        "slot": slot,
        "current": state["active"] + 1 if state["active"] >= 0 else 0,
        "total": len(state["versions"]),
        "record": active_record(state),
        "versions": list(state["versions"]),
    }


def save_example_version(col, note_id: int, language: str, slot: int, record: dict) -> dict:
    note = _ensure_fields(col, note_id, language)
    history = parse_history(note[HISTORY_FIELD])
    seed = record_from_note(note, language, slot)
    history, state = append_version(history, slot, record, seed)
    return _persist(col, note, history, language, slot, state)


def activate_example_version(col, note_id: int, language: str, slot: int, index: int) -> dict:
    note = _ensure_fields(col, note_id, language)
    history = parse_history(note[HISTORY_FIELD])
    seed = record_from_note(note, language, slot)
    history, state = select_version(history, slot, index, seed)
    return _persist(col, note, history, language, slot, state)


def delete_example_version(col, note_id: int, language: str, slot: int, index: int) -> dict:
    note = _ensure_fields(col, note_id, language)
    history = parse_history(note[HISTORY_FIELD])
    seed = record_from_note(note, language, slot)
    history, state = delete_version(history, slot, index, seed)
    return _persist(col, note, history, language, slot, state)
