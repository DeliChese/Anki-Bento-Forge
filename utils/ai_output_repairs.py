"""Narrow, evidence-backed repairs for contradictory AI card output."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from .usage_guide import normalize_usage_guide_cards


_ASK_TRANSLATION_RE = re.compile(
    r"(?<!câu )\bhỏi\b|\bask(?:ed|ing|s)?\b", re.IGNORECASE
)
_KIKU_QUESTION_RE = re.compile(r"質問を聞(いて|いた|きました|きます|く)")
_KIKU_QUESTION_REPAIRS = {
    "いて": "して",
    "いた": "した",
    "きました": "しました",
    "きます": "します",
    "く": "する",
}


def _repair_kiku_question(match: re.Match) -> str:
    return "質問" + _KIKU_QUESTION_REPAIRS[match.group(1)]


def repair_vocabulary_cards(cards: Sequence[object], lang: str) -> list[object]:
    """Repair narrow Japanese ``聞く`` constructions contradicted by translation.

    ``質問を聞く`` means to hear a question; if its paired Vietnamese or English
    translation says "ask", the intended construction is ``質問する`` with the
    same supported inflection. Other wording/languages remain unchanged.
    """
    cards = normalize_usage_guide_cards(cards)
    if lang != "japanese":
        return cards

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
            if _KIKU_QUESTION_RE.search(example) and _ASK_TRANSLATION_RE.search(translation):
                updated[example_field] = _KIKU_QUESTION_RE.sub(
                    _repair_kiku_question, example
                )
        repaired.append(updated)
    return repaired
