"""Provider-neutral response validation and requested/received reconciliation."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .ai_response_guard import AdaptedAiResponse
from .ai_response_parser import AiResponseParseError, parse_ai_payload
from .ai_output_validation import CardValidationIssue, validate_ai_cards
from .ai_output_repairs import repair_vocabulary_cards
from .i18n import t
from .logger import get_logger
from .usage_guide import normalize_language_cards


logger = get_logger()


def canonical_identity(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE)


def card_identity(card: Mapping[str, Any], kind: str) -> str:
    keys = ("pattern", "front") if kind == "grammar" else ("front", "simplified")
    for key in keys:
        identity = canonical_identity(card.get(key))
        if identity:
            return identity
    return ""


@dataclass(frozen=True)
class AiCardResponse:
    cards: tuple[dict, ...]
    invalid: tuple[CardValidationIssue, ...]
    duplicate_count: int
    raw_count: int
    comment: str
    recovery: str
    truncated: bool
    finish_reason: str
    provider: str
    model: str
    residual_text: str = ""


@dataclass(frozen=True)
class OptionalCardPayload:
    """Validated optional card data plus the prose safe to display in Chat."""

    cards: tuple[dict, ...]
    reply: str
    rejection_category: str | None = None
    recovery: str = ""


@dataclass(frozen=True)
class CompletenessReport:
    requested: int
    valid: int
    invalid: int
    duplicates: int
    missing: int
    unexpected: int
    truncated: bool
    cards: tuple[dict, ...]
    unresolved: tuple[dict, ...]


class AiOutputFailure(RuntimeError):
    """Categorized failure that may retain only independently valid cards."""

    def __init__(
        self, category: str, *, cards: Sequence[dict] = (), message: str | None = None,
        source_category: str | None = None,
    ) -> None:
        self.category = category
        self.cards = tuple(dict(card) for card in cards)
        self.source_category = source_category or category
        super().__init__(message or category)


def process_ai_card_response(
    response: AdaptedAiResponse, *, lang: str, kind: str,
) -> AiCardResponse:
    """Parse then validate; no normalization occurs before schema identity."""
    try:
        parsed = parse_ai_payload(
            response.text, structured_data=response.structured_data,
        )
    except AiResponseParseError as exc:
        category = "truncation" if response.truncated else exc.category
        message = t("error_model_output_truncated") if category == "truncation" else None
        raise AiOutputFailure(
            category, message=message, source_category=exc.category,
        ) from exc

    validation = validate_ai_cards(parsed.items, lang=lang, kind=kind)
    truncated = response.truncated or parsed.truncated
    result = AiCardResponse(
        validation.valid_cards,
        validation.invalid,
        validation.duplicate_count,
        len(parsed.items),
        parsed.comment,
        parsed.recovery,
        truncated,
        response.finish_reason,
        response.provider,
        response.model,
        parsed.residual_text,
    )
    if truncated:
        raise AiOutputFailure(
            "truncation", cards=result.cards,
            message=t("error_model_output_truncated"),
        )
    if not result.cards and result.invalid:
        categories = {issue.category for issue in result.invalid}
        category = (
            "schema_mismatch"
            if any("mismatch" in item or "_flow" in item for item in categories)
            else "semantic_validation"
        )
        raise AiOutputFailure(category)
    return result


def extract_optional_card_payload(
    response: AdaptedAiResponse, *, lang: str, kind: str = "vocab",
) -> OptionalCardPayload:
    """Treat prose as prose and admit only a wholly validated card payload."""
    try:
        result = process_ai_card_response(response, lang=lang, kind=kind)
    except AiOutputFailure as exc:
        if exc.source_category in {"empty_response", "malformed_json"} and not exc.cards:
            logger.debug(
                "AI chat prose provider=%s model=%s lang=%s kind=%s",
                response.provider, response.model, lang, kind,
            )
            return OptionalCardPayload((), response.text.strip())
        logger.warning(
            "AI chat card payload rejected category=%s provider=%s model=%s lang=%s kind=%s",
            exc.category, response.provider, response.model, lang, kind,
        )
        return OptionalCardPayload(
            (), response.text.strip(), exc.category,
        )

    if not result.cards:
        logger.warning(
            "AI chat card payload rejected category=empty_card_payload provider=%s model=%s lang=%s kind=%s",
            response.provider, response.model, lang, kind,
        )
        return OptionalCardPayload(
            (), response.text.strip(), "empty_card_payload", result.recovery,
        )
    if result.invalid:
        categories = {issue.category for issue in result.invalid}
        category = (
            "schema_mismatch"
            if any("mismatch" in item or "_flow" in item for item in categories)
            else "semantic_validation"
        )
        logger.warning(
            "AI chat card payload rejected category=%s provider=%s model=%s lang=%s kind=%s invalid=%d",
            category, response.provider, response.model, lang, kind,
            len(result.invalid),
        )
        return OptionalCardPayload(
            (), response.text.strip(), category, result.recovery,
        )

    cards = list(result.cards)
    cards = (
        repair_vocabulary_cards(cards, lang)
        if kind == "vocab" else normalize_language_cards(cards)
    )
    logger.info(
        "AI chat card payload validated provider=%s model=%s lang=%s kind=%s raw=%d valid=%d duplicates=%d recovery=%s",
        response.provider, response.model, lang, kind, result.raw_count,
        len(cards), result.duplicate_count, result.recovery,
    )
    return OptionalCardPayload(
        tuple(cards), result.residual_text, None, result.recovery,
    )


def validated_cards_from_result(
    result: dict,
    cfg: dict,
    *,
    lang: str,
    kind: str,
    progress_callback=None,
) -> tuple[list, str]:
    """Extraction facade: adapt, validate, normalize, and reject partial cache input."""
    from .ai_response_guard import adapt_chat_completion_response

    adapted = adapt_chat_completion_response(result, cfg)
    try:
        response = process_ai_card_response(adapted, lang=lang, kind=kind)
    except AiOutputFailure as exc:
        valid = list(exc.cards)
        valid = (
            repair_vocabulary_cards(valid, lang)
            if kind == "vocab" else normalize_language_cards(valid)
        )
        logger.warning(
            "AI output rejected category=%s provider=%s model=%s lang=%s kind=%s valid_prefix=%d",
            exc.category, adapted.provider, adapted.model, lang, kind, len(valid),
        )
        raise AiOutputFailure(exc.category, cards=valid, message=str(exc)) from exc

    cards = list(response.cards)
    cards = (
        repair_vocabulary_cards(cards, lang)
        if kind == "vocab" else normalize_language_cards(cards)
    )
    logger.info(
        "AI output provider=%s model=%s lang=%s kind=%s raw=%d valid=%d invalid=%d duplicates=%d recovery=%s",
        response.provider, response.model, lang, kind, response.raw_count,
        len(cards), len(response.invalid), response.duplicate_count, response.recovery,
    )
    if response.invalid and progress_callback:
        progress_callback(t(
            "status_ai_invalid_ignored",
            valid=len(cards), invalid=len(response.invalid),
        ))
    if response.invalid:
        raise AiOutputFailure("semantic_validation", cards=cards)
    return cards, response.comment


def reconcile_expected_candidates(
    candidates: Sequence[Mapping[str, Any]],
    cards: Sequence[Mapping[str, Any]],
    *,
    kind: str,
    invalid_count: int = 0,
    duplicate_count: int = 0,
    truncated: bool = False,
) -> CompletenessReport:
    """Match exact candidate identities and preserve requested source order."""
    by_identity: dict[str, list[dict]] = {}
    unexpected = 0
    seen_card_keys = set()
    for card in cards:
        identity = card_identity(card, kind)
        if not identity:
            unexpected += 1
            continue
        card_key = (identity, canonical_identity(card.get("meaning")))
        if card_key in seen_card_keys:
            duplicate_count += 1
            continue
        seen_card_keys.add(card_key)
        by_identity.setdefault(identity, []).append(dict(card))

    resolved = []
    unresolved = []
    matched_ids = set()
    for candidate in candidates:
        identity = canonical_identity(candidate.get("front"))
        choices = by_identity.get(identity, [])
        if choices:
            requested_meaning = canonical_identity(candidate.get("meaning"))
            match_index = 0
            if requested_meaning:
                match_index = next(
                    (
                        index for index, card in enumerate(choices)
                        if canonical_identity(card.get("meaning")) == requested_meaning
                    ),
                    0,
                )
            resolved.append(choices.pop(match_index))
            matched_ids.add(identity)
        else:
            unresolved.append(dict(candidate))

    for identity, remaining in by_identity.items():
        if remaining:
            unexpected += len(remaining)
    return CompletenessReport(
        requested=len(candidates),
        valid=len(resolved),
        invalid=invalid_count,
        duplicates=duplicate_count,
        missing=len(unresolved),
        unexpected=unexpected,
        truncated=truncated,
        cards=tuple(resolved),
        unresolved=tuple(unresolved),
    )


__all__ = [
    "AiCardResponse", "AiOutputFailure", "CompletenessReport", "OptionalCardPayload",
    "canonical_identity", "card_identity", "process_ai_card_response",
    "extract_optional_card_payload", "reconcile_expected_candidates",
    "validated_cards_from_result",
]
