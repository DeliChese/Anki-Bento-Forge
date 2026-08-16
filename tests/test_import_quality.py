"""Tests for advisory, deterministic AI-card quality checks."""

from utils.import_quality import (
    detect_card_warnings,
    evaluate_card_candidate,
    evaluate_card_completeness,
)


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


def test_detect_card_warnings_flags_placeholder_and_wrong_example_script():
    warnings = detect_card_warnings({
        "front": "食べる",
        "meaning": "unknown",
        "example": "I eat at home.",
    }, lang="japanese")

    assert warnings == (
        "placeholder_meaning",
        "example_wrong_script",
        "missing_furigana",
    )


def test_cjk_candidates_warn_when_core_pronunciation_is_missing():
    japanese = detect_card_warnings(
        {"front": "食べる", "meaning": "ăn", "example": "毎日食べる。"},
        lang="japanese",
    )
    chinese = detect_card_warnings(
        {"simplified": "学习", "meaning": "học", "example": "我学习。"},
        lang="chinese",
    )
    korean = detect_card_warnings(
        {"front": "먹다", "meaning": "ăn", "example": "매일 먹어요."},
        lang="korean",
    )

    assert "missing_furigana" in japanese
    assert "missing_pinyin" in chinese
    assert "missing_romanization" in korean


def test_english_candidates_warn_when_ipa_is_missing():
    warnings = detect_card_warnings(
        {
            "front": "reliable",
            "meaning": "đáng tin cậy",
            "example": "This source is reliable.",
        },
        lang="english",
    )

    assert warnings == ("missing_pronunciation",)


def test_korean_romanization_must_not_use_a_hyphen():
    warnings = detect_card_warnings(
        {
            "front": "친구",
            "romanization": "chin-gu",
            "meaning": "bạn",
            "example": "친구를 만나요.",
        },
        lang="korean",
    )

    assert warnings == ("romanization_contains_hyphen",)


def test_chinese_target_check_is_exact_and_advisory():
    candidate = evaluate_card_candidate({
        "simplified": "学习",
        "meaning": "học",
        "example": "我每天读书。",
    }, lang="chinese")

    assert candidate["score"] == 100
    assert candidate["complete"] is True
    assert candidate["warnings"] == ("target_not_in_example", "missing_pinyin")
    assert candidate["issues"] == ("target_not_in_example", "missing_pinyin")
    assert candidate["has_warnings"] is True


def test_literal_grammar_pattern_must_appear_but_formula_pattern_is_not_guessed():
    valid = detect_card_warnings({
        "pattern": "ながら",
        "meaning": "while",
        "example": "音楽を聞きながら勉強する。",
    }, lang="japanese", grammar=True)
    literal = detect_card_warnings({
        "pattern": "ながら",
        "meaning": "while",
        "example": "音楽を聞いて勉強する。",
    }, lang="japanese", grammar=True)
    formula = detect_card_warnings({
        "pattern": "V-ながら",
        "meaning": "while",
        "example": "音楽を聞いて勉強する。",
    }, lang="japanese", grammar=True)

    assert valid == ()
    assert literal == ("pattern_not_in_example",)
    assert formula == ()
