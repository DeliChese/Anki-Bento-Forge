"""Repeatable, provider-neutral evaluation for AI card-generation runs."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping, Sequence

from .ai_response_parser import parse_ai_json_with_comment
from .import_quality import evaluate_card_candidate, normalize_for_comparison


BENCHMARK_VERSION = "2"
AUTOMATED_GATE = 0.95
HUMAN_QUALITY_GATE = 0.90
QUALITY_V2_DIMENSIONS = frozenset({
    "basic_lexical", "polysemy", "near_synonym", "collocation_restriction",
    "multiple_patterns", "fixed_phrase", "register_sensitive",
    "ambiguous_function", "tricky_grammar", "two_examples",
    "three_four_examples", "zero_usage_note", "multiple_micro_notes",
    "zero_collocation", "multiple_collocations", "negative_overgeneration",
})
_QUALITY_ITEM_SPLIT_RE = re.compile(r"(?:<br\s*/?>|\r?\n)+", re.IGNORECASE)


def _quality_items(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        raw = [str(item).strip() for item in value]
    else:
        raw = _QUALITY_ITEM_SPLIT_RE.split(str(value or ""))
    return [item for item in raw if item.strip()]


def evaluate_quality_v2_card(card: Mapping[str, Any], *, grammar: bool = False) -> dict:
    """Check observable V2 structure without claiming semantic correctness."""
    issues = []
    examples = [str(card.get("example") or "").strip()]
    examples.extend(
        str(card.get(f"example_{index}") or card.get(f"example{index}") or "").strip()
        for index in (2, 3, 4)
    )
    present_examples = [example for example in examples if example]
    example_keys = [normalize_for_comparison(example) for example in present_examples]
    if len(present_examples) < 2:
        issues.append("fewer_than_two_examples")
    if len(example_keys) != len(set(example_keys)):
        issues.append("duplicate_examples")

    counts = {}
    if not grammar:
        for field in ("usage_pattern", "usage_note", "collocation"):
            items = _quality_items(card.get(field))
            counts[field] = len(items)
            keys = [normalize_for_comparison(item) for item in items]
            if len(items) > 3:
                issues.append(f"too_many_{field}")
            if len(keys) != len(set(keys)):
                issues.append(f"duplicate_{field}")
        if any(" — " not in item for item in _quality_items(card.get("collocation"))):
            issues.append("collocation_missing_meaning")

    for index in (2, 3, 4):
        example = str(card.get(f"example_{index}") or "").strip()
        companion_keys = [key for key in card if key.startswith(f"example_{index}_")]
        if not example and any(str(card.get(key) or "").strip() for key in companion_keys):
            issues.append(f"orphan_example_{index}_metadata")

    return {
        "valid": not issues,
        "issues": tuple(dict.fromkeys(issues)),
        "example_count": len(present_examples),
        "usage_pattern_count": counts.get("usage_pattern", 0),
        "usage_note_count": counts.get("usage_note", 0),
        "collocation_count": counts.get("collocation", 0),
        "human_review_required": (
            "sense_accuracy", "naturalness", "information_gain", "hallucination",
            "level_appropriateness",
        ),
    }


def summarize_quality_v2_cards(
    cards: Sequence[Mapping[str, Any]], *, grammar: bool = False,
) -> dict:
    """Report density/size without rewarding cards for filling optional quotas."""
    results = [evaluate_quality_v2_card(card, grammar=grammar) for card in cards]
    count = len(results)
    average = lambda key: round(sum(item[key] for item in results) / count, 3) if count else 0.0
    serialized_size = len(json.dumps(list(cards), ensure_ascii=False, separators=(",", ":")))
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "card_count": count,
        "automated_valid_count": sum(item["valid"] for item in results),
        "over_generation_count": sum(
            any(issue.startswith("too_many_") for issue in item["issues"])
            for item in results
        ),
        "average_examples": average("example_count"),
        "average_patterns": average("usage_pattern_count"),
        "average_micro_notes": average("usage_note_count"),
        "average_collocations": average("collocation_count"),
        "output_characters": serialized_size,
        "average_output_characters_per_card": round(serialized_size / count, 1) if count else 0.0,
        "results": results,
    }


def validate_quality_v2_corpus(corpus: Mapping[str, Any]) -> dict:
    """Require every language to cover the same benchmark dimensions."""
    cases = corpus.get("cases")
    if str(corpus.get("version")) != BENCHMARK_VERSION or not isinstance(cases, list):
        raise ValueError("quality corpus needs benchmark version 2 and a cases list")
    coverage = {}
    for language in ("english", "japanese", "chinese", "korean"):
        dimensions = {
            dimension
            for case in cases if case.get("language") == language
            for dimension in case.get("dimensions", ())
        }
        missing = sorted(QUALITY_V2_DIMENSIONS - dimensions)
        if missing:
            raise ValueError(f"{language} corpus misses dimensions: {', '.join(missing)}")
        coverage[language] = sorted(dimensions)
    return {"case_count": len(cases), "coverage": coverage}


def validate_case(case: Mapping[str, Any]) -> dict:
    """Validate and normalize a benchmark case before it is scored."""
    if not isinstance(case, Mapping):
        raise ValueError("benchmark case must be an object")
    case_id = str(case.get("id") or "").strip()
    language = str(case.get("language") or "").strip()
    terms = case.get("expected_terms")
    if not case_id or not language or not isinstance(terms, list) or not terms:
        raise ValueError("case needs id, language, and a non-empty expected_terms list")
    normalized = [normalize_for_comparison(term) for term in terms]
    if any(not term for term in normalized) or len(set(normalized)) != len(normalized):
        raise ValueError("expected_terms must be non-empty and unique after normalization")
    return {
        "id": case_id,
        "language": language,
        "grammar": bool(case.get("grammar", False)),
        "expected_terms": [str(term) for term in terms],
    }


def cards_from_payload(payload: Any) -> list[dict]:
    """Read cards from an array, JSON wrapper, or raw model-response string."""
    if isinstance(payload, str):
        cards, _comment = parse_ai_json_with_comment(payload)
    elif isinstance(payload, list):
        cards = payload
    elif isinstance(payload, Mapping):
        if isinstance(payload.get("cards"), list):
            cards = payload["cards"]
        elif isinstance(payload.get("content"), str):
            cards, _comment = parse_ai_json_with_comment(payload["content"])
        else:
            cards, _comment = parse_ai_json_with_comment(json.dumps(payload, ensure_ascii=False))
    else:
        raise ValueError("cards payload must be JSON text, an array, or an object")
    if not all(isinstance(card, Mapping) for card in cards):
        raise ValueError("every generated card must be a JSON object")
    return [dict(card) for card in cards]


def _term_for_card(card: Mapping[str, Any], grammar: bool) -> str:
    keys = ("pattern", "front") if grammar else ("front", "simplified")
    for key in keys:
        value = normalize_for_comparison(card.get(key))
        if value:
            return value
    return ""


def evaluate_cards(case: Mapping[str, Any], cards: Sequence[Mapping[str, Any]]) -> dict:
    """Measure deterministic factory-readiness; semantic correctness stays human-reviewed."""
    normalized_case = validate_case(case)
    expected = {
        normalize_for_comparison(term): term
        for term in normalized_case["expected_terms"]
    }
    first_card_by_term: dict[str, Mapping[str, Any]] = {}
    unexpected = []
    duplicate_count = 0
    for card in cards:
        term = _term_for_card(card, normalized_case["grammar"])
        if term not in expected:
            unexpected.append(term or "<missing_front>")
        elif term in first_card_by_term:
            duplicate_count += 1
        else:
            first_card_by_term[term] = card

    candidates = [
        evaluate_card_candidate(
            first_card_by_term[term],
            lang=normalized_case["language"],
            grammar=normalized_case["grammar"],
        )
        for term in expected
        if term in first_card_by_term
    ]
    expected_count = len(expected)
    coverage_rate = len(first_card_by_term) / expected_count
    completeness_rate = sum(item["score"] for item in candidates) / (expected_count * 100)
    factory_ready_count = sum(
        item["complete"] and not item["has_warnings"] for item in candidates
    )
    factory_ready_rate = factory_ready_count / expected_count
    warning_count = sum(len(item["warnings"]) for item in candidates)
    automated_score = round(
        100 * (0.50 * coverage_rate + 0.35 * completeness_rate + 0.15 * factory_ready_rate),
        1,
    )
    return {
        "expected_cards": expected_count,
        "returned_cards": len(cards),
        "matched_cards": len(first_card_by_term),
        "missing_terms": [term for key, term in expected.items() if key not in first_card_by_term],
        "unexpected_terms": unexpected,
        "duplicate_output_count": duplicate_count,
        "coverage_rate": round(coverage_rate, 4),
        "completeness_rate": round(completeness_rate, 4),
        "factory_ready_count": factory_ready_count,
        "factory_ready_rate": round(factory_ready_rate, 4),
        "warning_count": warning_count,
        "automated_score": automated_score,
        "automated_gate_passed": (
            coverage_rate >= AUTOMATED_GATE and factory_ready_rate >= AUTOMATED_GATE
        ),
    }


def _optional_nonnegative_number(metadata: Mapping[str, Any], key: str) -> float | None:
    value = metadata.get(key)
    if value is None:
        return None
    number = float(value)
    if number < 0:
        raise ValueError(f"{key} must be non-negative")
    return number


def build_run_report(
    case: Mapping[str, Any],
    cards_payload: Any,
    metadata: Mapping[str, Any],
    human_review: Mapping[str, Any] | None = None,
) -> dict:
    """Build a portable report from one provider run without storing API secrets."""
    normalized_case = validate_case(case)
    model = str(metadata.get("model") or "").strip()
    provider = str(metadata.get("provider") or "").strip()
    if not model or not provider:
        raise ValueError("run metadata needs model and provider")
    cards = cards_from_payload(cards_payload)
    metrics = evaluate_cards(normalized_case, cards)
    cost_usd = _optional_nonnegative_number(metadata, "cost_usd")
    latency_seconds = _optional_nonnegative_number(metadata, "latency_seconds")
    expected_cards = metrics["expected_cards"]
    run = {
        "provider": provider,
        "model": model,
        "cache_status": str(metadata.get("cache_status") or "miss"),
        "cost_usd": cost_usd,
        "latency_seconds": latency_seconds,
        "input_tokens": _optional_nonnegative_number(metadata, "input_tokens"),
        "output_tokens": _optional_nonnegative_number(metadata, "output_tokens"),
    }
    metrics["cost_per_expected_card_usd"] = (
        round(cost_usd / expected_cards, 8) if cost_usd is not None else None
    )
    metrics["seconds_per_expected_card"] = (
        round(latency_seconds / expected_cards, 4) if latency_seconds is not None else None
    )

    reviewed = None
    if human_review is not None:
        correct_meanings = int(human_review["correct_meanings"])
        natural_examples = int(human_review["natural_examples"])
        if not all(0 <= value <= expected_cards for value in (correct_meanings, natural_examples)):
            raise ValueError("human review counts must be between zero and expected_cards")
        meaning_rate = correct_meanings / expected_cards
        example_rate = natural_examples / expected_cards
        reviewed = {
            "correct_meanings": correct_meanings,
            "natural_examples": natural_examples,
            "meaning_accuracy_rate": round(meaning_rate, 4),
            "example_naturalness_rate": round(example_rate, 4),
            "human_quality_score": round(100 * (meaning_rate + example_rate) / 2, 1),
        }
        reviewed["human_gate_passed"] = min(meaning_rate, example_rate) >= HUMAN_QUALITY_GATE

    decision_ready = bool(metrics["automated_gate_passed"] and reviewed and reviewed["human_gate_passed"])
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "case": normalized_case,
        "run": run,
        "metrics": metrics,
        "human_review": reviewed,
        "decision_ready": decision_ready,
    }


def render_markdown_comparison(reports: Sequence[Mapping[str, Any]]) -> str:
    """Render a compact decision table, ranking eligible runs before cheaper ones."""
    if not reports:
        raise ValueError("at least one benchmark report is required")

    def rank(report):
        metrics = report["metrics"]
        cost = metrics.get("cost_per_expected_card_usd")
        return (
            not report.get("decision_ready", False),
            -metrics.get("automated_score", 0),
            float("inf") if cost is None else cost,
            report["run"]["model"],
        )

    ordered = sorted(reports, key=rank)
    rows = [
        "| Provider / model | Ready | Coverage | Factory-ready | Auto score | Human score | Cost/card | Seconds/card |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for report in ordered:
        run, metrics, human = report["run"], report["metrics"], report.get("human_review")
        human_score = "—" if not human else f"{human['human_quality_score']:.1f}"
        cost = metrics.get("cost_per_expected_card_usd")
        seconds = metrics.get("seconds_per_expected_card")
        rows.append(
            "| {provider} / {model} | {ready} | {coverage:.1%} | {factory:.1%} | "
            "{score:.1f} | {human_score} | {cost} | {seconds} |".format(
                provider=run["provider"],
                model=run["model"],
                ready="yes" if report.get("decision_ready") else "no",
                coverage=metrics["coverage_rate"],
                factory=metrics["factory_ready_rate"],
                score=metrics["automated_score"],
                human_score=human_score,
                cost="—" if cost is None else f"${cost:.6f}",
                seconds="—" if seconds is None else f"{seconds:.2f}",
            )
        )
    return "\n".join(rows)
