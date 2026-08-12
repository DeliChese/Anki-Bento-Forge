"""Safety helpers for the final import step in Bento Forge."""


def summarize_import_batch(batch_data):
    """Return the number of new notes and updates in a selected import batch."""
    summary = {"new": 0, "updates": 0}
    for row in batch_data:
        action = row.get("action") if isinstance(row, dict) else None
        if action in ("add", "add_partial"):
            summary["new"] += 1
        elif action == "update":
            summary["updates"] += 1
    return summary


def rollback_added_notes(collection, note_ids):
    """Remove exactly the valid note IDs created by one import batch.

    The caller owns confirmation, checkpointing, and UI refresh. Updates are never
    supplied here, so this operation cannot overwrite or remove pre-existing notes.
    """
    normalized_ids = []
    seen = set()
    for note_id in note_ids or []:
        try:
            note_id = int(note_id)
        except (TypeError, ValueError):
            continue
        if note_id > 0 and note_id not in seen:
            normalized_ids.append(note_id)
            seen.add(note_id)

    if not normalized_ids:
        return 0

    remove_notes = getattr(collection, "remove_notes", None)
    if not callable(remove_notes):
        raise RuntimeError("Anki Collection.remove_notes() is unavailable")
    remove_notes(normalized_ids)
    return len(normalized_ids)
