"""Pure version-history model for Reviewer example regeneration."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone


HISTORY_FIELD = "Example Versions"
HISTORY_SCHEMA_VERSION = 1
VALID_SLOTS = (1, 2, 3, 4)


def _slot_field(slot: int, suffix: str = "") -> str:
    if slot not in VALID_SLOTS:
        raise ValueError("invalid_example_slot")
    stem = "Example" if slot == 1 else f"Example{slot}"
    return f"{stem}{suffix}"


def example_field_names(language: str, slot: int) -> dict:
    """Return stable note-field names for one example slot."""
    language = str(language or "").strip().lower()
    reading_suffix = {
        "japanese": " Reading",
        "chinese": " Pinyin",
        "korean": " Romanization",
        "english": " Pronunciation",
    }.get(language, " Reading")
    return {
        "text": _slot_field(slot),
        "reading": _slot_field(slot, reading_suffix),
        "translation": _slot_field(slot, " in Vietnamese"),
        "audio": _slot_field(slot, " Audio"),
    }


def required_example_fields(language: str) -> list[str]:
    fields = [HISTORY_FIELD]
    for slot in VALID_SLOTS:
        fields.extend(example_field_names(language, slot).values())
    return list(dict.fromkeys(fields))


def empty_history() -> dict:
    return {"schema": HISTORY_SCHEMA_VERSION, "slots": {}}


def parse_history(raw: str | None) -> dict:
    """Parse strict history JSON; malformed non-empty data is never discarded."""
    text = str(raw or "").strip()
    if not text:
        return empty_history()
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError("example_history_corrupt") from error
    if not isinstance(value, dict) or not isinstance(value.get("slots", {}), dict):
        raise ValueError("example_history_corrupt")
    value.setdefault("schema", HISTORY_SCHEMA_VERSION)
    value.setdefault("slots", {})
    return value


def serialize_history(history: dict) -> str:
    return json.dumps(history, ensure_ascii=False, separators=(",", ":"))


def normalize_record(record: dict | None, *, source: str = "manual") -> dict:
    record = record if isinstance(record, dict) else {}
    normalized = {
        "text": str(record.get("text") or "").strip()[:4_000],
        "reading": str(record.get("reading") or "").strip()[:4_000],
        "translation": str(record.get("translation") or "").strip()[:4_000],
        "audio": str(record.get("audio") or "").strip()[:1_000],
        "source": str(record.get("source") or source).strip()[:32] or source,
        "created_at": str(record.get("created_at") or "").strip()[:64],
    }
    if not normalized["created_at"]:
        normalized["created_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if not normalized["text"]:
        raise ValueError("example_text_required")
    return normalized


def record_from_note(note, language: str, slot: int) -> dict | None:
    fields = example_field_names(language, slot)

    def value(name):
        try:
            return str(note[name] or "").strip()
        except Exception:
            return ""

    text = value(fields["text"])
    if not text:
        return None
    return normalize_record({
        "text": text,
        "reading": value(fields["reading"]),
        "translation": value(fields["translation"]),
        "audio": value(fields["audio"]),
        "source": "original",
    })


def slot_state(history: dict, slot: int, seed: dict | None = None) -> dict:
    key = str(slot)
    raw = (history.get("slots") or {}).get(key, {})
    versions = []
    for item in raw.get("versions", []) if isinstance(raw, dict) else []:
        try:
            versions.append(normalize_record(item))
        except ValueError:
            continue
    if not versions and seed:
        versions = [normalize_record(seed, source="original")]
    active = int(raw.get("active", len(versions) - 1)) if versions else -1
    active = max(0, min(active, len(versions) - 1)) if versions else -1
    return {"active": active, "versions": versions}


def with_slot_state(history: dict, slot: int, state: dict) -> dict:
    updated = copy.deepcopy(history)
    updated.setdefault("schema", HISTORY_SCHEMA_VERSION)
    updated.setdefault("slots", {})[str(slot)] = state
    return updated


def append_version(history: dict, slot: int, record: dict, seed: dict | None = None) -> tuple[dict, dict]:
    state = slot_state(history, slot, seed)
    candidate = normalize_record(record)
    comparable = (candidate["text"], candidate["reading"], candidate["translation"])
    if any(
        (item["text"], item["reading"], item["translation"]) == comparable
        for item in state["versions"]
    ):
        raise ValueError("example_version_duplicate")
    state["versions"].append(candidate)
    state["active"] = len(state["versions"]) - 1
    return with_slot_state(history, slot, state), state


def select_version(history: dict, slot: int, index: int, seed: dict | None = None) -> tuple[dict, dict]:
    state = slot_state(history, slot, seed)
    if not state["versions"]:
        raise ValueError("example_version_missing")
    if index < 0 or index >= len(state["versions"]):
        raise ValueError("invalid_example_version")
    state["active"] = int(index)
    return with_slot_state(history, slot, state), state


def delete_version(history: dict, slot: int, index: int, seed: dict | None = None) -> tuple[dict, dict]:
    state = slot_state(history, slot, seed)
    if index < 0 or index >= len(state["versions"]):
        raise ValueError("invalid_example_version")
    state["versions"].pop(index)
    if state["versions"]:
        state["active"] = min(index, len(state["versions"]) - 1)
    else:
        state["active"] = -1
    return with_slot_state(history, slot, state), state


def active_record(state: dict) -> dict | None:
    versions = state.get("versions") or []
    active = int(state.get("active", -1))
    return versions[active] if 0 <= active < len(versions) else None


def reusable_audio(history: dict, slot: int, text: str, seed: dict | None = None) -> str:
    target = str(text or "").strip()
    for item in slot_state(history, slot, seed)["versions"]:
        if item["text"] == target and item.get("audio"):
            return str(item["audio"])
    return ""

