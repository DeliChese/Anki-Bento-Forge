"""Strict source-grounded candidate manifests for Forge AI Workshop."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .ai_reliability import canonical_identity
from .ai_response_parser import AiResponseParseError, parse_ai_payload
from .language_identity import normalize_language


CANDIDATE_SCHEMA_VERSION = 1
MAX_SOURCE_CANDIDATES = 30
_PRIORITIES = frozenset({"high", "medium", "low"})
_CANDIDATE_FIELDS = frozenset({
    "kind", "surface", "target", "meaning_hint", "source_excerpt", "reason", "priority",
})


class CandidateOutputError(RuntimeError):
    """Categorized candidate failure without retaining raw provider output."""

    def __init__(self, category: str) -> None:
        self.category = str(category or "invalid_candidates")
        super().__init__(self.category)


@dataclass(frozen=True)
class CandidateValidationReport:
    valid_candidates: tuple[dict, ...]
    invalid: tuple[dict, ...]
    duplicate_count: int


def _clean(value: Any, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _source_form(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _candidate_id(
    language: str, lane: str, target: str, meaning_hint: str, excerpt: str,
) -> str:
    payload = f"{language}\0{lane}\0{target}\0{meaning_hint}\0{excerpt}".encode("utf-8")
    return "candidate_" + hashlib.sha256(payload).hexdigest()[:20]


def build_candidate_prompt(language: str, lane: str, *, english_ui: bool) -> str:
    """Return a compact strict schema prompt; SOURCE is supplied separately."""
    language = normalize_language(language)
    lane = str(lane or "").strip().casefold()
    if lane not in {"vocab", "grammar"}:
        raise ValueError("unsupported candidate lane")
    target = {
        "japanese": "Japanese", "chinese": "Chinese",
        "korean": "Korean", "english": "English",
    }[language]
    kind_label = "vocabulary" if lane == "vocab" else "grammar"
    schema = (
        '{"candidates":[{"kind":"' + lane + '","surface":"exact text copied from SOURCE",'
        '"target":"dictionary form or pattern","meaning_hint":"short contextual meaning",'
        '"source_excerpt":"exact short excerpt copied from SOURCE",'
        '"reason":"why this is worth learning","priority":"high|medium|low"}]}'
    )
    if english_ui:
        return (
            f"You select source-grounded {target} {kind_label} candidates for Forge AI Workshop.\n"
            "Return exactly one JSON object matching the schema below and no prose.\n"
            f"Select at most {MAX_SOURCE_CANDIDATES} useful items. Copy surface and source_excerpt exactly from SOURCE; "
            "do not invent cards, examples, fields, or facts outside SOURCE. Keep distinct senses separate.\n"
            f"SCHEMA: {schema}"
        )
    return (
        f"Bạn tuyển candidate {kind_label} {target} bám SOURCE cho Forge AI Workshop.\n"
        "Chỉ trả đúng một JSON object theo schema dưới đây, không thêm prose.\n"
        f"Chọn tối đa {MAX_SOURCE_CANDIDATES} mục đáng học. surface và source_excerpt phải chép nguyên văn từ SOURCE; "
        "không tạo thẻ, ví dụ, field hay dữ kiện ngoài SOURCE. Giữ riêng các nghĩa khác nhau.\n"
        f"SCHEMA: {schema}"
    )


def validate_source_candidates(
    items: Sequence[Any], *, source_text: str, language: str, lane: str,
) -> CandidateValidationReport:
    """Validate provenance and shape without semantic repair or source guessing."""
    language = normalize_language(language)
    lane = str(lane or "").strip().casefold()
    if lane not in {"vocab", "grammar"}:
        raise ValueError("unsupported candidate lane")
    source = _source_form(source_text)
    if not source:
        raise ValueError("candidate source is required")

    valid: list[dict] = []
    invalid: list[dict] = []
    seen: set[tuple[str, str]] = set()
    duplicate_count = 0
    for index, raw in enumerate(list(items)[:MAX_SOURCE_CANDIDATES * 2]):
        if not isinstance(raw, Mapping):
            invalid.append({"index": index, "category": "candidate_not_object"})
            continue
        kind = _clean(raw.get("kind"), 20).casefold()
        surface = _clean(raw.get("surface"), 180)
        target = _clean(raw.get("target"), 180)
        meaning_hint = _clean(raw.get("meaning_hint"), 280)
        excerpt = _clean(raw.get("source_excerpt"), 600)
        reason = _clean(raw.get("reason"), 360)
        priority = _clean(raw.get("priority"), 20).casefold()
        category = ""
        if set(raw) - _CANDIDATE_FIELDS:
            category = "candidate_unknown_field"
        elif kind != lane:
            category = "candidate_kind_mismatch"
        elif not surface or not target or not meaning_hint or not excerpt or not reason:
            category = "candidate_required_field_missing"
        elif priority not in _PRIORITIES:
            category = "candidate_priority_invalid"
        elif _source_form(excerpt) not in source or _source_form(surface) not in source:
            category = "candidate_not_grounded_in_source"
        identity = (canonical_identity(target), canonical_identity(meaning_hint))
        if not category and (not identity[0] or identity in seen):
            if identity in seen:
                duplicate_count += 1
                continue
            category = "candidate_identity_missing"
        if category:
            invalid.append({"index": index, "category": category})
            continue
        seen.add(identity)
        valid.append({
            "candidate_id": _candidate_id(language, lane, target, meaning_hint, excerpt),
            "kind": lane,
            "surface": surface,
            "target": target,
            "meaning_hint": meaning_hint,
            "source_excerpt": excerpt,
            "reason": reason,
            "priority": priority,
        })
        if len(valid) >= MAX_SOURCE_CANDIDATES:
            break
    return CandidateValidationReport(tuple(valid), tuple(invalid), duplicate_count)


def parse_source_candidate_response(
    response, *, source_text: str, language: str, lane: str,
) -> dict:
    """Parse one provider-neutral response into a bounded manifest."""
    if bool(getattr(response, "truncated", False)):
        raise CandidateOutputError("candidate_output_truncated")
    try:
        parsed = parse_ai_payload(
            getattr(response, "text", ""),
            structured_data=getattr(response, "structured_data", None),
        )
    except AiResponseParseError as error:
        raise CandidateOutputError(error.category) from error
    if parsed.truncated:
        raise CandidateOutputError("candidate_output_truncated")
    if parsed.residual_text.strip() or parsed.comment.strip():
        raise CandidateOutputError("candidate_output_contains_prose")
    report = validate_source_candidates(
        parsed.items, source_text=source_text, language=language, lane=lane,
    )
    if not report.valid_candidates:
        raise CandidateOutputError("candidate_output_has_no_valid_items")
    language = normalize_language(language)
    source_digest = hashlib.sha256(str(source_text).encode("utf-8")).hexdigest()
    return {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "language": language,
        "lane": str(lane).casefold(),
        "source_digest": source_digest,
        "candidates": [dict(item) for item in report.valid_candidates],
        "invalid_count": len(report.invalid),
        "duplicate_count": report.duplicate_count,
        "recovery": parsed.recovery,
    }


def mark_existing_candidate_surfaces(manifest: Mapping[str, Any], existing: Sequence[Any]) -> dict:
    """Annotate current-deck surface matches as advisory; never drop a sense."""
    identities = set()
    for entry in existing or ():
        if isinstance(entry, Mapping):
            value = entry.get("front") or entry.get("simplified") or entry.get("pattern")
        else:
            value = entry
        identity = canonical_identity(value)
        if identity:
            identities.add(identity)
    result = dict(manifest)
    result["candidates"] = [
        dict(item, existing_surface=canonical_identity(item.get("target")) in identities)
        for item in manifest.get("candidates", [])
        if isinstance(item, Mapping)
    ]
    result["existing_surface_count"] = sum(
        1 for item in result["candidates"] if item.get("existing_surface")
    )
    return result


def build_selected_candidate_instruction(
    manifest: Mapping[str, Any], selected_ids: Sequence[str], *, english_ui: bool,
) -> str:
    """Build the explicit next Card Mode request from selected manifest rows only."""
    selected = {str(value) for value in selected_ids if str(value)}
    candidates = [
        item for item in manifest.get("candidates", [])
        if isinstance(item, Mapping) and str(item.get("candidate_id")) in selected
    ]
    if not candidates:
        raise ValueError("at least one source candidate must be selected")
    lane = str(manifest.get("lane") or "").casefold()
    if lane not in {"vocab", "grammar"}:
        raise ValueError("unsupported candidate lane")
    payload = [{
        "candidate_id": item["candidate_id"],
        "surface": item["surface"],
        "target": item["target"],
        "meaning_hint": item.get("meaning_hint", ""),
        "source_excerpt": item["source_excerpt"],
    } for item in candidates[:MAX_SOURCE_CANDIDATES]]
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if english_ui:
        return (
            "Create Quality V2 cards only for the selected source candidates below. "
            "Preserve each contextual sense and candidate identity; do not add unselected items.\n"
            f"SELECTED_SOURCE_CANDIDATES={encoded}"
        )
    return (
        "Chỉ tạo thẻ Quality V2 cho các candidate từ source đã chọn dưới đây. "
        "Giữ đúng nghĩa ngữ cảnh và identity; không thêm mục chưa chọn.\n"
        f"SELECTED_SOURCE_CANDIDATES={encoded}"
    )


__all__ = [
    "CANDIDATE_SCHEMA_VERSION", "MAX_SOURCE_CANDIDATES", "CandidateOutputError",
    "CandidateValidationReport", "build_candidate_prompt",
    "build_selected_candidate_instruction", "mark_existing_candidate_surfaces",
    "parse_source_candidate_response", "validate_source_candidates",
]
