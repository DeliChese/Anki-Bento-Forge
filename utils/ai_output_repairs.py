"""Narrow, evidence-backed repairs for contradictory AI card output."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence


_ASK_TRANSLATION_RE = re.compile(
    r"(?<!câu )\bhỏi\b|\bask(?:ed|ing|s)?\b", re.IGNORECASE
)
_KIKU_QUESTION_ERROR = "質問を聞きました"
_KIKU_QUESTION_REPAIR = "質問しました"


def repair_vocabulary_cards(cards: Sequence[object], lang: str) -> list[object]:
    """Repair the one Japanese ``聞く`` construction contradicted by its translation.

    ``質問を聞きました`` means to hear a question; if its paired Vietnamese or
    English translation says "ask", the intended, natural construction is
    ``質問しました``.  No other wording, language, or card field is changed.
    """
    if lang != "japanese":
        return list(cards)

    repaired: list[object] = []
    for card in cards:
        if not isinstance(card, Mapping) or str(card.get("front") or "").strip() != "聞く":
            repaired.append(card)
            continue
        updated = dict(card)
        for example_field, translation_field in (
            ("example", "example_vn"),
            ("example_2", "example_2_vn"),
        ):
            example = str(updated.get(example_field) or "")
            translation = str(updated.get(translation_field) or "")
            if _KIKU_QUESTION_ERROR in example and _ASK_TRANSLATION_RE.search(translation):
                updated[example_field] = example.replace(
                    _KIKU_QUESTION_ERROR, _KIKU_QUESTION_REPAIR
                )
        repaired.append(updated)
    return repaired
