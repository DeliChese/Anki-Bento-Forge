"""Pure V18 Knowledge preview, duplicate, and update planning.

Collection access is injected into the small read adapter below.  Network
workers never import or call this module with a live collection.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping

from mode.knowledge import KNOWLEDGE_FIELDS, KNOWLEDGE_MODEL_NAME

from .knowledge_model import knowledge_duplicate_key, knowledge_note_payload
from .knowledge_schema import validate_knowledge_card


KNOWLEDGE_IMPORT_CONFIG = {
    "model_name": KNOWLEDGE_MODEL_NAME,
    "all_fields": list(KNOWLEDGE_FIELDS),
    "detect_key": "question",
    "front_field": "Question",
    "level_field": "",
    "furi_label": "",
    "json_field_map": {
        "type": "Type",
        "question": "Question",
        "answer": "Answer",
        "explanation": "Explanation",
        "source": "Source",
        "cloze_text": "Cloze Text",
    },
    "audio_fields": [],
    "note_defaults": {},
    "lang_code": "",
}


def _model_id(model: Any):
    if isinstance(model, Mapping):
        return model.get("id")
    return getattr(model, "id", None)


def read_knowledge_notes_for_deck(collection, deck_id: object) -> List[Dict[str, Any]]:
    """Serialize only Knowledge notes whose cards belong to the selected deck."""
    model = collection.models.by_name(KNOWLEDGE_MODEL_NAME)
    mid = _model_id(model)
    if not mid:
        return []
    note_ids = collection.db.list(
        "SELECT DISTINCT n.id FROM notes n JOIN cards c ON c.nid = n.id "
        "WHERE n.mid = ? AND c.did = ?",
        mid,
        deck_id,
    )
    result = []
    for nid in note_ids:
        note = collection.get_note(nid)
        fields = {}
        for field in KNOWLEDGE_FIELDS:
            try:
                fields[field] = str(note[field])
            except Exception:
                fields[field] = ""
        result.append({"nid": int(nid), "fields": fields, "tags": list(getattr(note, "tags", []) or [])})
    return result


def read_knowledge_duplicate_keys(collection, deck_id: object) -> List[str]:
    """Return normalized keys for AI avoidance context in the same model/deck."""
    return [
        row["fields"].get("Duplicate Key", "")
        for row in read_knowledge_notes_for_deck(collection, deck_id)
        if row["fields"].get("Duplicate Key", "")
    ]


def _existing_key(row: Mapping[str, Any]) -> str:
    fields = row.get("fields") or {}
    key = str(fields.get("Duplicate Key", "")).strip()
    if key:
        return key
    card_type = str(fields.get("Type", "")).strip().lower()
    candidate = {
        "type": card_type,
        "question": fields.get("Question", ""),
        "answer": fields.get("Answer", ""),
        "explanation": fields.get("Explanation", ""),
        "source": fields.get("Source", ""),
        "tags": row.get("tags", []),
        "cloze_text": fields.get("Cloze Text", ""),
    }
    try:
        return knowledge_duplicate_key(candidate)
    except Exception:
        return ""


def prepare_knowledge_batch(
    cards: Iterable[Mapping[str, Any]], existing_notes: Iterable[Mapping[str, Any]]
) -> Dict[str, Any]:
    """Validate cards and plan add/update actions within one Knowledge deck."""
    existing = {}
    for row in existing_notes:
        key = _existing_key(row)
        if key and key not in existing:
            existing[key] = row

    prepared = []
    seen = set()
    counts = {"new": 0, "update": 0, "duplicate": 0}
    for card in cards:
        normalized = validate_knowledge_card(card)
        payload = knowledge_note_payload(normalized)
        key = payload["fields"]["Duplicate Key"]
        if key in seen:
            counts["duplicate"] += 1
            continue
        seen.add(key)
        old = existing.get(key)
        if old is None:
            prepared.append({
                "item": normalized, "action": "add", "nid": None,
                "update_fields": [], "conflict_info": None,
            })
            counts["new"] += 1
            continue

        old_fields = old.get("fields") or {}
        changed = []
        for field, value in payload["fields"].items():
            # Missing optional provenance/explanation is never permission to
            # erase existing user data during an update.
            if field in {"Source", "Explanation"} and not value:
                continue
            if str(old_fields.get(field, "")) != str(value):
                changed.append(field)
        old_tags = list(old.get("tags", []) or [])
        if payload["tags"] and old_tags != payload["tags"]:
            changed.append("tags")
        if not changed:
            counts["duplicate"] += 1
            continue
        prepared.append({
            "item": normalized, "action": "update", "nid": int(old["nid"]),
            "update_fields": changed, "conflict_info": None,
        })
        counts["update"] += 1
    return {"prepared": prepared, "counts": counts}
