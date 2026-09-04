"""Pure contracts for opt-in upgrades of existing Language notes.

An Anki note can keep its SRS history while its learning content is upgraded.
This module deliberately has no Anki, Qt, network, or AI dependency: callers
provide the current note snapshot and an already-validated AI candidate.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence


QUALITY_FIELD = "Bento Quality Version"
# Bump only when the released Language content standard meaningfully changes.
# Existing notes then become eligible for an explicit Reviewer upgrade again.
CURRENT_QUALITY_VERSION = "1"
_SUPPORTED_KINDS = frozenset({"vocab", "grammar", "collocation"})


def normalized_kind(value: object) -> str:
    value = str(value or "").strip().lower()
    if value == "vocabulary":
        return "vocab"
    return value if value in _SUPPORTED_KINDS else ""


def quality_is_current(snapshot: Mapping | None) -> bool:
    return str((snapshot or {}).get("quality_version") or "").strip() == CURRENT_QUALITY_VERSION


def upgrade_is_available(snapshot: Mapping | None) -> bool:
    """Only managed Language notes with an older quality revision can upgrade."""
    snapshot = snapshot or {}
    note_type = str(snapshot.get("note_type") or "").casefold()
    return bool(
        normalized_kind(snapshot.get("card_kind"))
        and str(snapshot.get("language") or "").strip()
        and ("ankitool " in note_type or "mẫu từ vựng tiếng nhật " in note_type)
        and "(add-on)" in note_type
        and not quality_is_current(snapshot)
    )


def build_upgrade_source(snapshot: Mapping, field_values: Mapping[str, object]) -> str:
    """Build bounded, explicitly supplied source material for a one-note refresh."""
    target = str(snapshot.get("current_target") or "").strip()[:500]
    meaning = str(snapshot.get("meaning") or "").strip()[:1_000]
    lines = [f"MỤC TIÊU CẦN GIỮ NGUYÊN: {target}"]
    if meaning:
        lines.append(f"NGHĨA HIỆN CÓ: {meaning}")
    lines.append("DỮ LIỆU THẺ HIỆN CÓ (chỉ để đối chiếu, có thể đã cũ):")
    for field, value in field_values.items():
        text = str(value or "").strip()
        if not text or field == QUALITY_FIELD or field.endswith(" Audio"):
            continue
        lines.append(f"{str(field)[:120]}: {text[:2_000]}")
    return "\n".join(lines)[:12_000]


def upgrade_instruction(snapshot: Mapping) -> str:
    kind = normalized_kind(snapshot.get("card_kind")) or "vocab"
    target = str(snapshot.get("current_target") or "").strip()
    return (
        "Đây là yêu cầu NÂNG CẤP một thẻ học đã có, không phải trích xuất danh sách. "
        f"Chỉ trả đúng MỘT thẻ loại {kind} cho mục tiêu {target!r}. "
        "Giữ nguyên mục tiêu/mặt chữ hoặc pattern; không đổi sang mục khác. "
        "Điền đầy đủ schema chất lượng hiện hành khi có căn cứ, tạo ví dụ khác nhau, "
        "và để trống field tùy chọn khi không hữu ích. Dữ liệu cũ là tham chiếu, không "
        "được bịa thông tin cá nhân hay nguồn không được cung cấp."
    )


def _identity(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return "".join(char for char in text if not char.isspace())


def select_upgrade_candidate(cards: Sequence[object], snapshot: Mapping) -> dict:
    """Accept only the single AI card that preserves this note's identity."""
    kind = normalized_kind(snapshot.get("card_kind"))
    target = _identity(snapshot.get("current_target"))
    key = "pattern" if kind == "grammar" else "chunk" if kind == "collocation" else "front"
    matches = [
        dict(card) for card in cards
        if isinstance(card, Mapping) and _identity(card.get(key) or card.get("front")) == target
    ]
    if len(matches) != 1:
        raise ValueError("card_upgrade_identity_mismatch")
    return matches[0]


def proposed_field_changes(
    current_fields: Mapping[str, object], candidate: Mapping[str, object], cfg: Mapping,
) -> list[dict]:
    """Map candidate JSON to visible Note fields without deleting old data."""
    changes = []
    detect_field = str(cfg.get("detect_key") or "front")
    field_map = dict(cfg.get("json_field_map") or {})
    for json_key, field_name in field_map.items():
        field_name = str(field_name or "").strip()
        if not field_name or field_name == QUALITY_FIELD or json_key not in candidate:
            continue
        if field_name == detect_field:
            continue
        proposed = str(candidate.get(json_key) or "").strip()
        if not proposed:
            continue
        current = str(current_fields.get(field_name) or "").strip()
        if proposed != current:
            changes.append({
                "json_key": str(json_key), "field": field_name,
                "current": current, "proposed": proposed,
                "missing": not bool(current),
            })
    return changes


def apply_card_upgrade(col, note_id: int, expected_target: str, detect_field: str,
                       changes: Sequence[Mapping], audio_tags: Mapping[str, str],
                       mark_current: bool) -> dict:
    """Apply selected fields in one undo-aware collection operation.

    The note is re-read and its identity checked immediately before mutation so
    a delayed AI result can never be written onto a different Reviewer card.
    """
    note = col.get_note(int(note_id))
    current_target = str(note[str(detect_field)] or "").strip()
    if _identity(current_target) != _identity(expected_target):
        raise ValueError("card_upgrade_stale_note")

    fields = [str(item.get("field") or "").strip() for item in changes]
    fields.extend(str(name or "").strip() for name in audio_tags)
    if mark_current:
        fields.append(QUALITY_FIELD)
    model = note.model()
    existing = {str(field.get("name") or "") for field in model.get("flds", [])}
    added_fields = False
    for field in dict.fromkeys(field for field in fields if field and field not in existing):
        col.models.add_field(model, col.models.new_field(field))
        existing.add(field)
        added_fields = True
    if added_fields:
        col.models.save(model)
        note = col.get_note(int(note_id))

    changed = []
    for item in changes:
        field = str(item.get("field") or "").strip()
        value = str(item.get("proposed") or "").strip()
        try:
            existing_value = str(note[field] or "")
        except Exception:
            existing_value = ""
        if field and value and existing_value != value:
            note[field] = value
            changed.append(field)
    for field, tag in audio_tags.items():
        field, tag = str(field or "").strip(), str(tag or "").strip()
        if field and tag:
            note[field] = tag
            changed.append(field)
    if mark_current:
        note[QUALITY_FIELD] = CURRENT_QUALITY_VERSION
        changed.append(QUALITY_FIELD)
    update_note = getattr(col, "update_note", None)
    if callable(update_note):
        update_note(note)
    else:
        note.flush()
    return {"updated_fields": list(dict.fromkeys(changed)), "quality_current": bool(mark_current)}
