"""Collection-side phases of a Bento Forge import.

Network/audio work deliberately lives outside this module.  These helpers are
called only by :class:`aqt.operations.QueryOp` and ``CollectionOp``.
"""

import re

from anki.notes import Note

from .knowledge_model import ensure_knowledge_model, knowledge_note_payload


def _save_note(col, note):
    """Persist a note through the collection API when it is available.

    Anki 26.5 deprecates ``Note.flush()`` and its compatibility implementation
    bypasses the current undo entry.  ``Collection.update_note()`` keeps the
    mutation inside the surrounding CollectionOp.  The fallback retains
    support for the older Anki API and lightweight test doubles.
    """
    update_note = getattr(col, "update_note", None)
    if callable(update_note):
        return update_note(note)
    return note.flush()


def _fill_example_blanks(note, front_field):
    if not front_field:
        return
    try:
        front_value = note[front_field].strip()
    except Exception:
        return
    if not front_value:
        return
    for source, target in (("Example", "Example Fill"), ("Example2", "Example2 Fill")):
        try:
            if note[source].strip():
                note[target] = re.sub(re.escape(front_value), "<span class='blank'>___</span>", note[source])
        except Exception:
            continue


def _mapped_value(item, cfg, field_name, fallback=""):
    for json_key, mapped_field in cfg["json_field_map"].items():
        if mapped_field == field_name and json_key in item:
            return str(item[json_key]).strip()
    return fallback


def prepare_audio_tasks(col, batch, cfg):
    """Read the text required for audio without mutating ``col``.

    Each task key is stable across the later CollectionOp and maps to a single
    audio field.  A missing source is intentionally omitted rather than
    producing an empty media tag.
    """
    tasks = []
    for item_index, entry in enumerate(batch):
        item = entry["item"]
        note = col.get_note(entry["nid"]) if entry["action"] == "update" else None
        audio_enabled = entry.get("audio_enabled")
        for audio_index, (audio_field, source_field) in enumerate(cfg["audio_fields"]):
            # Older pending batches only have the first three choices; do not
            # unexpectedly generate Examples 3/4 for those batches.
            enabled = (
                True if audio_enabled is None
                else audio_index < len(audio_enabled) and bool(audio_enabled[audio_index])
            )
            if not enabled:
                continue
            if note is None:
                source = _mapped_value(item, cfg, source_field)
            else:
                source = _mapped_value(item, cfg, source_field, note[source_field])
            if source:
                tasks.append({
                    "key": f"{item_index}:{audio_field}",
                    "text": source,
                    "lang": cfg["lang_code"],
                })
    return tasks


def apply_import(col, batch, cfg, deck_id, audio_tags, is_cancelled):
    """Apply one import batch inside an undo-aware ``CollectionOp``."""
    report = {"added": 0, "added_note_ids": [], "updated": 0, "audio_gen": 0,
              "audio_failed": 0, "errors": 0, "cancelled": False}
    errors = []
    for item_index, entry in enumerate(batch):
        if is_cancelled():
            report["cancelled"] = True
            break
        item = entry["item"]
        display = str(item.get(cfg["detect_key"], item.get("front", ""))).strip()
        try:
            if entry["action"] == "update":
                note = col.get_note(entry["nid"])
                for field_name in entry.get("update_fields", []):
                    if field_name not in {field for field, _ in cfg["audio_fields"]}:
                        value = _mapped_value(item, cfg, field_name)
                        if value:
                            note[field_name] = value
                report["updated"] += 1
            else:
                note = Note(col, col.models.by_name(cfg["model_name"]))
                for json_key, field_name in cfg["json_field_map"].items():
                    if json_key in item and field_name in cfg["all_fields"]:
                        note[field_name] = str(item[json_key])
                for field_name, value in (cfg.get("note_defaults") or {}).items():
                    if field_name in cfg["all_fields"] and value:
                        note[field_name] = str(value)
                col.add_note(note, deck_id)
                if getattr(note, "id", 0):
                    report["added_note_ids"].append(int(note.id))
                report["added"] += 1

            _fill_example_blanks(note, cfg.get("front_field", ""))
            for audio_field, _source_field in cfg["audio_fields"]:
                tag = audio_tags.get(f"{item_index}:{audio_field}", "")
                if tag:
                    note[audio_field] = tag
                    report["audio_gen"] += 1
                elif f"{item_index}:{audio_field}" in audio_tags:
                    report["audio_failed"] += 1
            _save_note(col, note)
        except Exception as exc:
            report["errors"] += 1
            errors.append(f"• {display}: {exc}")
    if errors:
        report["errors_detail"] = errors[:10]
    return report


def apply_knowledge_import(col, batch, deck_id, is_cancelled):
    """Apply a strict Knowledge batch inside one undo-aware CollectionOp."""
    model = ensure_knowledge_model(col.models).model
    report = {
        "learning_mode": "knowledge", "added": 0, "added_note_ids": [],
        "updated": 0, "audio_gen": 0, "audio_failed": 0,
        "errors": 0, "cancelled": False, "updated_before": [],
    }
    errors = []
    for entry in batch:
        if is_cancelled():
            report["cancelled"] = True
            break
        payload = knowledge_note_payload(entry["item"])
        display = payload["fields"].get("Question") or payload["fields"].get("Cloze Text")
        try:
            if entry["action"] == "update":
                note = col.get_note(entry["nid"])
                before = {field: str(note[field]) for field in payload["fields"]}
                before["tags"] = list(getattr(note, "tags", []) or [])
                report["updated_before"].append({"nid": int(entry["nid"]), "values": before})
                for field in entry.get("update_fields", []):
                    if field == "tags":
                        note.tags = list(payload["tags"])
                    elif field in payload["fields"]:
                        note[field] = str(payload["fields"][field])
                report["updated"] += 1
            else:
                note = Note(col, model)
                for field, value in payload["fields"].items():
                    note[field] = str(value)
                note.tags = list(payload["tags"])
                col.add_note(note, deck_id)
                if getattr(note, "id", 0):
                    report["added_note_ids"].append(int(note.id))
                report["added"] += 1
            _save_note(col, note)
        except Exception as exc:
            report["errors"] += 1
            errors.append(f"• {display}: {exc}")
    if report["cancelled"] and (report["added_note_ids"] or report["updated_before"]):
        report["cancel_rollback"] = rollback_knowledge_import(col, report)
        report["added"] = 0
        report["updated"] = 0
        report["added_note_ids"] = []
        report["updated_before"] = []
    if errors:
        report["errors_detail"] = errors[:10]
    return report


def rollback_knowledge_import(col, rollback_token):
    """Undo exactly one Knowledge batch: delete its adds and restore its updates."""
    note_ids = [int(nid) for nid in rollback_token.get("added_note_ids", []) if int(nid) > 0]
    if note_ids:
        col.remove_notes(note_ids)
    restored = 0
    for snapshot in rollback_token.get("updated_before", []):
        note = col.get_note(int(snapshot["nid"]))
        values = snapshot.get("values", {})
        for field, value in values.items():
            if field == "tags":
                note.tags = list(value or [])
            else:
                note[field] = str(value)
        _save_note(col, note)
        restored += 1
    return {"removed": len(note_ids), "restored": restored}
