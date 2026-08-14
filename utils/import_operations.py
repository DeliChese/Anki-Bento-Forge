"""Collection-side phases of a Bento Forge import.

Network/audio work deliberately lives outside this module.  These helpers are
called only by :class:`aqt.operations.QueryOp` and ``CollectionOp``.
"""

import re

from anki.notes import Note


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
        for audio_index, (audio_field, source_field) in enumerate(cfg["audio_fields"]):
            enabled = entry.get("audio_enabled", (True, True, True))[min(audio_index, 2)]
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
            note.flush()
        except Exception as exc:
            report["errors"] += 1
            errors.append(f"• {display}: {exc}")
    if errors:
        report["errors_detail"] = errors[:10]
    return report
