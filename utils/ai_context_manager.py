"""Token-aware, session-local context construction for AI Study Sessions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from .ai_providers import get_model_context_window
from .logger import redact_sensitive


DEFAULT_CONTEXT_WINDOW = 32_768
DEFAULT_OUTPUT_RESERVE = 2_048
SYSTEM_RESERVE = 768
SAFETY_MARGIN = 512
SUMMARY_MAX_CHARS = 4_000


@dataclass(frozen=True)
class PreparedStudyContext:
    messages: tuple[dict, ...]
    summary: str
    summary_through_message_id: str
    estimated_tokens: int
    hard_cap_tokens: int
    compacted_message_count: int


def estimate_tokens(value: Any) -> int:
    """Conservative deterministic estimate usable without a tokenizer package."""
    return max(1, (len(str(value or "")) + 2) // 3)


def compact_session_summary(
    messages: Sequence[Mapping[str, Any]],
    *,
    existing_summary: str = "",
    max_chars: int = SUMMARY_MAX_CHARS,
) -> str:
    """Keep learning decisions and corrections, omit incidental chat."""
    lines = []
    if existing_summary.strip():
        lines.append(existing_summary.strip())
    priority_terms = (
        "correct", "correction", "khác", "phân biệt", "meaning", "nghĩa",
        "usage", "collocation", "pattern", "grammar", "ngữ pháp", "artifact",
        "card", "thẻ", "remember", "ghi nhớ", "instruction", "yêu cầu",
    )
    for message in messages:
        if message.get("type") == "system_internal":
            continue
        content = str(redact_sensitive(message.get("content") or "")).strip()
        if not content:
            continue
        role = "Learner" if message.get("role") == "user" else "Tutor"
        compact = " ".join(content.split())[:500]
        important = any(term in compact.casefold() for term in priority_terms)
        if important or message.get("type") == "artifact_reference" or len(lines) < 4:
            lines.append(f"{role}: {compact}")
    summary = "\n".join(lines)
    return summary[-max(256, int(max_chars)):]


def minimal_card_context(snapshot: Optional[Mapping[str, Any]], *, include_answer: bool) -> dict:
    """Whitelist current-card data; never attach review history or another deck."""
    if not isinstance(snapshot, Mapping):
        return {}
    metadata_keys = {"language", "deck", "note_type", "side", "card_id", "study_mode"}
    target_keys = {
        "front", "simplified", "traditional", "pattern", "furigana", "pinyin",
        "romanization", "question", "concept", "usage_pattern", "collocation",
    }
    answer_keys = {
        "meaning", "usage_note", "usage", "explanation", "answer", "example",
        "example_vn", "example2", "example2_vn", "example3", "example3_vn",
        "example4", "example4_vn",
    }
    if include_answer:
        allowed = metadata_keys | target_keys | answer_keys
    else:
        # Legacy external snapshots predate study_mode and are forward cards.
        # Reviewer-owned snapshots always provide the explicit current mode.
        mode = str(snapshot.get("study_mode") or "qa").strip().casefold()
        mode_keys = {
            "qa": target_keys,
            "vn": {"meaning"},
            "wb": {"meaning"},
            "pron": {
                "front", "simplified", "traditional", "pattern", "meaning",
                "question", "concept",
            },
            "lg": {"meaning", "furigana", "pinyin", "romanization"},
        }
        # A missing/unknown mode owns no card-content fields. This is safer
        # than pretending every question is the forward qa direction.
        allowed = metadata_keys | mode_keys.get(mode, set())
    result = {}
    for key, value in snapshot.items():
        normalized = str(key).strip().lower().replace(" ", "_")
        if normalized in allowed and str(value or "").strip():
            result[normalized] = redact_sensitive(value)
    return result


def _context_system_message(card_context: Mapping[str, Any]) -> dict:
    side = str(card_context.get("side") or "question")
    lines = [f"CURRENT CARD CONTEXT (side={side}; use only when relevant):"]
    for key, value in card_context.items():
        if key != "side":
            lines.append(f"{key}: {value}")
    if side == "question":
        lines.append("Retrieval rule: do not reveal the answer unless the learner explicitly asks; hints must be indirect and limited to 1–2 cues.")
    return {"role": "system", "content": "\n".join(lines)}


def prepare_study_context(
    session: Mapping[str, Any],
    *,
    current_user_message: str,
    system_prompt: str,
    model: str,
    session_max_tokens: int,
    max_output_tokens: int = DEFAULT_OUTPUT_RESERVE,
    card_context: Optional[Mapping[str, Any]] = None,
    use_card_context: bool = False,
) -> PreparedStudyContext:
    """Build SYSTEM + SUMMARY + CARD + bounded RECENT + CURRENT USER."""
    context_window = get_model_context_window(model, DEFAULT_CONTEXT_WINDOW)
    hard_cap = min(max(1_000, int(session_max_tokens)), context_window)
    available = max(
        512,
        hard_cap - max(256, int(max_output_tokens)) - SYSTEM_RESERVE - SAFETY_MARGIN,
    )
    system = {"role": "system", "content": str(system_prompt).strip()}
    current = {"role": "user", "content": str(redact_sensitive(current_user_message)).strip()}
    fixed = [system]
    filtered_card = minimal_card_context(
        card_context,
        include_answer=str((card_context or {}).get("side") or "question") == "answer",
    ) if use_card_context else {}
    if filtered_card:
        fixed.append(_context_system_message(filtered_card))

    history = []
    for index, item in enumerate(session.get("messages", [])):
        if item.get("role") not in {"user", "assistant"} or not item.get("content"):
            continue
        history.append({
            "id": str(item.get("id") or f"legacy-message-{index}"),
            "role": item.get("role"),
            "content": str(redact_sensitive(item.get("content") or "")),
            "type": str(item.get("type") or item.get("role") or ""),
        })
    # The current message is normally autosaved before the request. Avoid
    # sending it twice when it is already the last persisted user message.
    if (
        history
        and history[-1]["role"] == current["role"]
        and history[-1]["content"] == current["content"]
    ):
        history.pop()

    fixed_tokens = sum(estimate_tokens(item["content"]) + 8 for item in fixed + [current])
    remaining = max(0, available - fixed_tokens)
    existing_summary = str(session.get("summary") or "").strip()
    persisted_marker = str(session.get("summary_through_message_id") or "").strip()
    marker_index = next(
        (index for index, item in enumerate(history) if item["id"] == persisted_marker),
        None,
    ) if persisted_marker else None

    # A persisted marker is the exclusive boundary for raw history. If its
    # message was pruned by retention, every retained message is newer and is
    # therefore unsummarized. Legacy summaries intentionally keep an empty
    # marker until a budget boundary can be inferred below.
    unsummarized_start = marker_index + 1 if marker_index is not None else 0
    unsummarized = history[unsummarized_start:]
    summary_reserve = min(256, remaining // 4) if existing_summary or unsummarized else 0
    recent_budget = max(0, remaining - summary_reserve)
    recent = []
    used = 0
    for message in reversed(unsummarized):
        cost = estimate_tokens(message["content"]) + 8
        if used + cost > recent_budget:
            break
        recent.append({"role": message["role"], "content": message["content"]})
        used += cost
    recent.reverse()
    fold_count = max(0, len(unsummarized) - len(recent))
    delta = unsummarized[:fold_count]
    summary = existing_summary
    marker = persisted_marker

    if existing_summary and not persisted_marker:
        # Schema-v1 sessions do not reveal which prefix produced their valid
        # summary. Treat the currently omitted prefix as that legacy boundary
        # once, preserving recent raw turns without recursively re-folding it.
        if delta:
            marker = delta[-1]["id"]
            delta = []
    elif delta:
        summary = compact_session_summary(
            delta,
            existing_summary=summary,
        )
        marker = delta[-1]["id"]
    compacted_count = len(delta)
    summary_message = None
    prompt_summary = ""
    if summary:
        summary_budget = max(0, remaining - used - 16)
        max_chars = min(SUMMARY_MAX_CHARS, summary_budget * 3)
        if max_chars >= 120:
            prompt_summary = summary[-max_chars:]
            summary_message = {
                "role": "system",
                "content": "SESSION SUMMARY:\n" + prompt_summary,
            }

    messages = [system]
    if summary_message:
        messages.append(summary_message)
    if filtered_card:
        messages.append(_context_system_message(filtered_card))
    messages.extend(recent)
    messages.append(current)
    estimated = sum(estimate_tokens(item["content"]) + 8 for item in messages)
    if estimated > available and summary_message:
        excess_chars = (estimated - available) * 3 + 24
        prompt_summary = (
            prompt_summary[:-excess_chars]
            if excess_chars < len(prompt_summary) else ""
        )
        messages = [item for item in messages if not item["content"].startswith("SESSION SUMMARY:")]
        if prompt_summary:
            messages.insert(1, {
                "role": "system",
                "content": "SESSION SUMMARY:\n" + prompt_summary,
            })
        estimated = sum(estimate_tokens(item["content"]) + 8 for item in messages)
    if estimated > available:
        raise ValueError("study session context exceeds the configured hard cap")
    return PreparedStudyContext(
        tuple(messages), summary, marker, estimated, hard_cap, compacted_count,
    )


__all__ = [
    "PreparedStudyContext", "compact_session_summary", "estimate_tokens",
    "minimal_card_context", "prepare_study_context",
]
