"""Tests for advisory, deterministic AI-card quality checks."""

from utils.import_quality import evaluate_card_completeness


def test_vocab_completeness_accepts_chinese_front_and_html_example():
    result = evaluate_card_completeness({
        "simplified": "学习",
        "meaning": "học",
        "example": "<b>我</b>在学习。",
    })

    assert result == {"score": 100, "issues": (), "complete": True}


def test_vocab_completeness_reports_only_missing_required_structure():
    result = evaluate_card_completeness({"front": "食べる", "meaning": "ăn"})

    assert result["score"] == 75
    assert result["issues"] == ("missing_example",)
    assert result["complete"] is False


def test_grammar_completeness_accepts_pattern_or_front():
    result = evaluate_card_completeness({
        "pattern": "〜ながら",
        "meaning": "vừa... vừa...",
        "example": "音楽を聞きながら勉強する。",
    }, grammar=True)

    assert result["score"] == 100
    assert result["complete"] is True


def test_invalid_candidate_is_advisory_and_never_raises():
    result = evaluate_card_completeness(None)

    assert result == {"score": 0, "issues": ("invalid_card",), "complete": False}
