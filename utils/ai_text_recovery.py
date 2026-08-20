"""Bounded adaptive recovery for source text without candidate identities."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Callable, Optional

from .ai_reliability import (
    AiOutputFailure, canonical_identity, card_identity,
)
from .i18n import t


MAX_TEXT_RECOVERY_DEPTH = 2
MIN_TEXT_RECOVERY_CHARS = 1000


def _merge_recovered_cards(left: list, right: list, *, kind: str) -> list:
    """Merge child spans deterministically without collapsing distinct senses."""
    merged = []
    seen = set()
    for card in [*left, *right]:
        if not isinstance(card, Mapping):
            merged.append(card)
            continue
        identity = card_identity(card, kind)
        if not identity:
            merged.append(card)
            continue
        key = (identity, canonical_identity(card.get("meaning")))
        if key in seen:
            continue
        seen.add(key)
        merged.append(card)
    return merged


def _split_source_text(text: str) -> tuple[str, str]:
    midpoint = len(text) // 2
    candidates = [
        pos
        for pos in (text.rfind("\n", 0, midpoint + 1), text.find("\n", midpoint))
        if pos > 0
    ]
    split_at = (
        min(candidates, key=lambda pos: abs(pos - midpoint))
        if candidates else midpoint
    )
    if split_at <= 0 or split_at >= len(text):
        split_at = midpoint
    return text[:split_at].strip(), text[split_at:].strip()


def recover_text_chunk(
    call: Callable[[str], list],
    text: str,
    *,
    progress_callback: Optional[Callable[[str], None]],
    should_abort: Optional[Callable[[], bool]],
    kind: str = "vocab",
    depth: int = 0,
) -> tuple[list, int]:
    """Use split children as authoritative when a source call must be retried."""
    if should_abort and should_abort():
        raise RuntimeError(t("error_cancelled_by_user"))
    try:
        return call(text), 0
    except AiOutputFailure as exc:
        recovered = list(exc.cards)
        can_split = (
            depth < MAX_TEXT_RECOVERY_DEPTH
            and len(text) >= MIN_TEXT_RECOVERY_CHARS * 2
        )
        if not can_split:
            return recovered, 1
        left, right = _split_source_text(text)
        if not left or not right:
            return recovered, 1
        if progress_callback:
            progress_callback(t(
                "status_ai_recovery_split",
                reason=exc.category,
                first=len(left),
                second=len(right),
            ))
        left_cards, left_unresolved = recover_text_chunk(
            call, left, progress_callback=progress_callback,
            should_abort=should_abort, kind=kind, depth=depth + 1,
        )
        right_cards, right_unresolved = recover_text_chunk(
            call, right, progress_callback=progress_callback,
            should_abort=should_abort, kind=kind, depth=depth + 1,
        )
        return (
            _merge_recovered_cards(left_cards, right_cards, kind=kind),
            left_unresolved + right_unresolved,
        )


__all__ = [
    "MAX_TEXT_RECOVERY_DEPTH", "MIN_TEXT_RECOVERY_CHARS", "recover_text_chunk",
]
