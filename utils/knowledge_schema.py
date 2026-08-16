"""Strict, pure-Python schema contract for V18 Knowledge cards."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List


KNOWLEDGE_CARD_FIELDS = frozenset((
    "type", "question", "answer", "explanation", "source", "tags", "cloze_text",
))
KNOWLEDGE_CARD_TYPES = frozenset(("basic", "cloze"))
_CLOZE_RE = re.compile(r"\{\{c([1-9]\d*)::([^{}]+?)(?:::[^{}]*)?\}\}")


class KnowledgeSchemaError(ValueError):
    """An AI/manual Knowledge payload does not satisfy the V18 contract."""


def _string(value: Any, field: str, *, required: bool = False) -> str:
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise KnowledgeSchemaError("%s must be a string" % field)
    value = value.strip()
    if required and not value:
        raise KnowledgeSchemaError("%s is required" % field)
    return value


def _tags(value: Any) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(tag, str) for tag in value):
        raise KnowledgeSchemaError("tags must be a list of strings")
    return [tag.strip() for tag in value if tag.strip()]


def has_valid_cloze(cloze_text: str) -> bool:
    """Return whether text contains at least one valid, non-empty Anki cloze."""
    if not isinstance(cloze_text, str) or not cloze_text.strip():
        return False
    matches = _CLOZE_RE.findall(cloze_text)
    return bool(matches) and cloze_text.count("{{c") == len(matches)


def validate_knowledge_card(card: Any) -> Dict[str, Any]:
    """Validate and canonicalize one Basic or Cloze card without inventing data."""
    if not isinstance(card, dict):
        raise KnowledgeSchemaError("each Knowledge card must be an object")
    unknown = set(card).difference(KNOWLEDGE_CARD_FIELDS)
    if unknown:
        raise KnowledgeSchemaError("unknown Knowledge fields: %s" % ", ".join(sorted(unknown)))

    card_type = card.get("type")
    if card_type not in KNOWLEDGE_CARD_TYPES:
        raise KnowledgeSchemaError("type must be basic or cloze")
    question = _string(card.get("question"), "question", required=card_type == "basic")
    answer = _string(card.get("answer"), "answer", required=card_type == "basic")
    cloze_text = _string(card.get("cloze_text"), "cloze_text", required=card_type == "cloze")
    if card_type == "basic" and cloze_text:
        raise KnowledgeSchemaError("basic cards must not contain cloze_text")
    if card_type == "cloze" and not has_valid_cloze(cloze_text):
        raise KnowledgeSchemaError("cloze_text must contain valid Anki cloze syntax")

    return {
        "type": card_type,
        "question": question,
        "answer": answer,
        "explanation": _string(card.get("explanation"), "explanation"),
        # A missing source is explicit unknown data, not permission to fabricate one.
        "source": _string(card.get("source"), "source"),
        "tags": _tags(card.get("tags")),
        "cloze_text": cloze_text,
    }


def parse_knowledge_cards(content: str) -> List[Dict[str, Any]]:
    """Parse a complete JSON array and reject ambiguous AI response shapes.

    Language extraction retains its lenient parser for backward compatibility.
    Knowledge deliberately accepts no wrappers, prose, single objects, or
    partial batches: callers must never import an unclear response.
    """
    if not isinstance(content, str):
        raise KnowledgeSchemaError("Knowledge response must be JSON text")
    try:
        payload = json.loads(content.strip())
    except (TypeError, ValueError) as error:
        raise KnowledgeSchemaError("Knowledge response must be valid JSON") from error
    if not isinstance(payload, list):
        raise KnowledgeSchemaError("Knowledge response must be a JSON array")
    return [validate_knowledge_card(card) for card in payload]
