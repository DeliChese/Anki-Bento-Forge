"""V18 Knowledge note-type lifecycle and import-boundary helpers.

No Anki or Qt modules are imported here.  Collection operations will call
these helpers in V18-05 through their existing adapter boundary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Mapping

from mode.knowledge import KNOWLEDGE_MODEL_CONFIG, KNOWLEDGE_MODEL_NAME, KNOWLEDGE_TEMPLATES, knowledge_css

from .import_quality import normalize_for_comparison
from .knowledge_schema import validate_knowledge_card
from .model_lifecycle import ensure_model


_CLOZE_CONTENT_RE = re.compile(r"\{\{c[1-9]\d*::(.*?)(?:::[^{}]*)?\}\}")


@dataclass(frozen=True)
class KnowledgeDuplicateScope:
    """A duplicate key which can only be compared inside one deck/model."""

    deck_id: object
    model_name: str
    key: str


def _template_at(_cfg, templates, index):
    template = templates[index]
    return template() if callable(template) else template


def ensure_knowledge_model(model_manager):
    """Create/update the dedicated Knowledge model without touching Language models."""
    return ensure_model(
        model_manager,
        KNOWLEDGE_MODEL_CONFIG,
        KNOWLEDGE_TEMPLATES,
        knowledge_css(),
        _template_at,
        _template_at,
        rename_primary_template=False,
        # Never silently delete a user-created Knowledge card template.
        prune_extra_templates=False,
    )


def knowledge_duplicate_key(card: Mapping[str, Any]) -> str:
    """Build the model-local duplicate key from Question or visible cloze content."""
    normalized = validate_knowledge_card(card)
    if normalized["type"] == "basic":
        value = normalized["question"]
    else:
        value = _CLOZE_CONTENT_RE.sub(r"\1", normalized["cloze_text"])
    return normalize_for_comparison(value)


def knowledge_duplicate_scope(card: Mapping[str, Any], deck_id: object) -> KnowledgeDuplicateScope:
    """Bind a normalized Knowledge key to its only valid comparison scope."""
    if deck_id is None:
        raise ValueError("Knowledge duplicate checks require a selected deck")
    key = knowledge_duplicate_key(card)
    if not key:
        raise ValueError("Knowledge duplicate key must not be empty")
    return KnowledgeDuplicateScope(deck_id=deck_id, model_name=KNOWLEDGE_MODEL_NAME, key=key)


def knowledge_note_payload(card: Mapping[str, Any]) -> Dict[str, Any]:
    """Map a validated card into Note fields plus Anki tags for V18-05 import."""
    normalized = validate_knowledge_card(card)
    return {
        "fields": {
            "Type": normalized["type"],
            "Question": normalized["question"],
            "Answer": normalized["answer"],
            "Explanation": normalized["explanation"],
            "Source": normalized["source"],
            "Cloze Text": normalized["cloze_text"],
            "Duplicate Key": knowledge_duplicate_key(normalized),
        },
        "tags": list(normalized["tags"]),
    }
