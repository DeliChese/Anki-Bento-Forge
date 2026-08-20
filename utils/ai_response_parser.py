"""Deterministic extraction of card JSON from provider-neutral AI content.

Only syntax and known envelopes are recovered here. This module never fills a
card field, guesses a missing value, or closes a truncated object.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


_FENCE_START_RE = re.compile(r"^\s*```(?:json)?\s*(?:\r?\n)?", re.IGNORECASE)
_FENCE_END_RE = re.compile(r"(?:\r?\n)?\s*```\s*$")
_KNOWN_LIST_WRAPPERS = frozenset({
    "cards", "items", "results", "vocabulary", "vocab", "grammar",
})
_IDENTITY_KEYS = frozenset({"front", "simplified", "pattern"})


class AiResponseParseError(RuntimeError):
    """A bounded, categorized parse failure safe to show in diagnostics."""

    def __init__(self, category: str, preview: str = "") -> None:
        self.category = category
        self.preview = preview[:400]
        super().__init__(category)


@dataclass(frozen=True)
class ParsedAiPayload:
    items: tuple[Any, ...]
    comment: str = ""
    recovery: str = "direct"
    truncated: bool = False
    residual_text: str = ""


def _strip_safe_envelope(content: str) -> tuple[str, str]:
    original = str(content or "")
    text = original.lstrip("\ufeff").strip()
    recovery = "bom_or_whitespace" if text != original else "direct"
    if _FENCE_START_RE.match(text):
        text = _FENCE_START_RE.sub("", text, count=1)
        text = _FENCE_END_RE.sub("", text, count=1).strip()
        recovery = "markdown_fence"
    return text, recovery


def _separate_comment(items: list[Any], comment: str = "") -> tuple[list[Any], str]:
    if items and isinstance(items[-1], dict) and set(items[-1]) == {"_comment"}:
        comment = str(items.pop().get("_comment") or "")
    return items, comment


def _coerce_payload(data: Any) -> tuple[list[Any], str, str]:
    if isinstance(data, list):
        items, comment = _separate_comment(list(data))
        return items, comment, "array"

    if not isinstance(data, dict):
        raise AiResponseParseError("json_payload_not_cards")

    payload = dict(data)
    comment = str(payload.pop("_comment", "") or "")
    wrappers = [
        key for key in _KNOWN_LIST_WRAPPERS if isinstance(payload.get(key), list)
    ]
    if len(wrappers) == 1:
        extra_payload_keys = set(payload) - {wrappers[0]}
        if extra_payload_keys:
            raise AiResponseParseError("invalid_wrapper")
        items, comment = _separate_comment(list(payload[wrappers[0]]), comment)
        return items, comment, f"wrapper:{wrappers[0]}"
    if len(wrappers) > 1:
        raise AiResponseParseError("ambiguous_wrapper")

    # Keep the historical one-card response only when it is visibly a card,
    # never for an arbitrary object such as {"message": "done"}.
    if _IDENTITY_KEYS.intersection(payload):
        return [payload], comment, "single_card"
    raise AiResponseParseError("invalid_wrapper")


def _complete_json_candidates(
    text: str,
) -> list[tuple[list[Any], str, str, int, int]]:
    decoder = json.JSONDecoder()
    candidates = []
    index = 0
    while index < len(text):
        structural = [
            pos for pos in (text.find("[", index), text.find("{", index))
            if pos >= 0
        ]
        if not structural:
            break
        start = min(structural)
        try:
            data, consumed = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            index = start + 1
            continue
        try:
            items, comment, recovery = _coerce_payload(data)
            candidates.append((items, comment, recovery, start, start + consumed))
        except AiResponseParseError:
            pass
        index = start + consumed
    return candidates


def _parse_complete_array_prefix(text: str) -> tuple[list[Any], str] | None:
    """Return only fully decoded top-level items before an unfinished tail."""
    start = text.find("[")
    if start < 0:
        return None
    decoder = json.JSONDecoder()
    index = start + 1
    items: list[Any] = []
    while index < len(text):
        while index < len(text) and text[index] in " \t\r\n,":
            index += 1
        if index >= len(text) or text[index] == "]":
            return None
        try:
            value, consumed = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            break
        if not isinstance(value, dict):
            return None
        items.append(value)
        index += consumed
    if not items:
        return None
    items, comment = _separate_comment(items)
    return items, comment


def parse_ai_payload(content: str, *, structured_data: Any = None) -> ParsedAiPayload:
    """Extract one unambiguous card payload and retain truncation metadata."""
    if structured_data is not None:
        items, comment, recovery = _coerce_payload(structured_data)
        return ParsedAiPayload(
            tuple(items), comment, f"structured:{recovery}",
            residual_text=str(content or "").strip(),
        )

    text, envelope_recovery = _strip_safe_envelope(content)
    if not text:
        raise AiResponseParseError("empty_response")

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None
    if data is not None:
        items, comment, payload_recovery = _coerce_payload(data)
        recovery = envelope_recovery if envelope_recovery != "direct" else payload_recovery
        return ParsedAiPayload(tuple(items), comment, recovery)

    # Recover a truncated array before scanning nested objects; otherwise a
    # complete prefix object could masquerade as a one-card response.
    first_array = text.find("[")
    first_object = text.find("{")
    if first_array >= 0 and (first_object < 0 or first_array < first_object):
        prefix = _parse_complete_array_prefix(text)
        if prefix is not None:
            items, comment = prefix
            return ParsedAiPayload(
                tuple(items), comment, "partial_array_prefix", True, text,
            )

    candidates = _complete_json_candidates(text)
    if len(candidates) == 1:
        items, comment, recovery, start, end = candidates[0]
        residual_text = (text[:start] + text[end:]).strip()
        return ParsedAiPayload(
            tuple(items), comment, f"prose:{recovery}",
            residual_text=residual_text,
        )
    if len(candidates) > 1:
        raise AiResponseParseError("ambiguous_json_payloads", text[:400])
    raise AiResponseParseError("malformed_json", text[:400])


def parse_ai_json_with_comment(content: str, error_formatter=None) -> tuple:
    """Compatibility wrapper returning ``(items, comment)``."""
    try:
        parsed = parse_ai_payload(content)
    except AiResponseParseError as exc:
        preview = exc.preview or str(content or "")[:400]
        if error_formatter is not None:
            raise RuntimeError(error_formatter(preview)) from exc
        raise RuntimeError(
            "⚠️ Không parse được JSON AI an toàn. Phản hồi có thể bị cắt, "
            "không đúng schema, hoặc chứa nhiều payload mơ hồ.\n"
            "💡 Hệ thống không tự bịa phần còn thiếu; hãy retry với batch nhỏ hơn.\n"
            f"Nội dung nhận được:\n{preview}"
        ) from exc
    return list(parsed.items), parsed.comment


__all__ = [
    "AiResponseParseError", "ParsedAiPayload", "parse_ai_payload",
    "parse_ai_json_with_comment",
]
