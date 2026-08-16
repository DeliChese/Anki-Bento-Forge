import json

import pytest

from utils.ai_benchmark import (
    build_run_report,
    cards_from_payload,
    evaluate_cards,
    render_markdown_comparison,
)
from scripts.benchmark_ai_models import _parse_variant, _safe_run_name


CASE = {
    "id": "small-ja-vocab",
    "language": "japanese",
    "grammar": False,
    "expected_terms": ["食べる", "飲む"],
}

CARDS = [
    {"front": "食べる", "furigana": "たべる", "meaning": "ăn", "example": "私は毎日食べる。"},
    {"front": "飲む", "furigana": "のむ", "meaning": "uống", "example": "水を飲む。"},
]


def test_cards_from_payload_supports_deepseek_json_object_wrapper():
    cards = cards_from_payload(json.dumps({"items": CARDS}, ensure_ascii=False))

    assert cards == CARDS


def test_evaluate_cards_scores_coverage_completeness_and_factory_readiness():
    metrics = evaluate_cards(CASE, CARDS)

    assert metrics["coverage_rate"] == 1.0
    assert metrics["completeness_rate"] == 1.0
    assert metrics["factory_ready_rate"] == 1.0
    assert metrics["automated_gate_passed"] is True
    assert metrics["missing_terms"] == []


def test_evaluate_cards_penalizes_missing_terms_and_duplicate_outputs():
    metrics = evaluate_cards(CASE, [CARDS[0], CARDS[0]])

    assert metrics["coverage_rate"] == 0.5
    assert metrics["duplicate_output_count"] == 1
    assert metrics["missing_terms"] == ["飲む"]
    assert metrics["automated_gate_passed"] is False


def test_report_requires_human_gate_before_it_is_decision_ready():
    report = build_run_report(
        CASE,
        CARDS,
        {"provider": "deepseek", "model": "deepseek-chat", "cost_usd": 0.002, "latency_seconds": 4},
        {"correct_meanings": 2, "natural_examples": 2},
    )

    assert report["decision_ready"] is True
    assert report["metrics"]["cost_per_expected_card_usd"] == 0.001
    assert report["human_review"]["human_quality_score"] == 100.0


def test_report_rejects_incomplete_human_review_and_comparison_is_markdown():
    with pytest.raises(ValueError, match="human review counts"):
        build_run_report(
            CASE,
            CARDS,
            {"provider": "gemini", "model": "flash"},
            {"correct_meanings": 3, "natural_examples": 2},
        )

    report = build_run_report(
        CASE,
        CARDS,
        {"provider": "gemini", "model": "flash"},
    )
    table = render_markdown_comparison([report])
    assert "| Provider / model |" in table
    assert "gemini / flash" in table


def test_benchmark_variant_parses_thinking_mode_and_safe_name():
    assert _parse_variant("deepseek-v4-flash@enabled") == (
        "deepseek-v4-flash",
        "enabled",
    )
    assert _parse_variant("openai/gpt-5.6") == ("openai/gpt-5.6", None)
    assert _safe_run_name("openai/gpt-5.6", None) == "openai-gpt-5.6"


def test_benchmark_variant_rejects_unknown_thinking_mode():
    with pytest.raises(ValueError, match="thinking mode"):
        _parse_variant("deepseek-v4-pro@sometimes")
