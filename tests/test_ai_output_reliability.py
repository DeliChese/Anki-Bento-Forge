"""Release-gate regressions for deterministic AI output reliability."""

import json

import pytest

from utils import batch_processor
from utils.ai_output_validation import validate_ai_cards
from utils.ai_reliability import (
    AiCardResponse,
    AiOutputFailure,
    process_ai_card_response,
    reconcile_expected_candidates,
)
from utils.ai_response_guard import adapt_chat_completion_response
from utils.ai_response_parser import AiResponseParseError, parse_ai_payload
from utils.ai_reliability_benchmark import simulate_reliability_policy
from utils import ai_text_recovery


def _card(front, **extra):
    return {"front": front, "meaning": f"meaning {front}", **extra}


def _adapted(content, *, finish_reason="stop", parsed=None):
    message = {"content": content}
    if parsed is not None:
        message["parsed"] = parsed
    return adapt_chat_completion_response(
        {"choices": [{"finish_reason": finish_reason, "message": message}]},
        {"api_base": "https://api.openai.com/v1", "model": "test-model"},
    )


@pytest.mark.parametrize(
    ("content", "recovery"),
    [
        ('[{"front":"a"}]', "array"),
        ('```json\n[{"front":"a"}]\n```', "markdown_fence"),
        ('Here are cards:\n[{"front":"a"}]\nDone.', "prose:array"),
        ('{"cards":[{"front":"a"}]}', "wrapper:cards"),
        ('\ufeff  [{"front":"a"}]  ', "bom_or_whitespace"),
    ],
)
def test_safe_json_extraction_matrix(content, recovery):
    parsed = parse_ai_payload(content)
    assert list(parsed.items) == [{"front": "a"}]
    assert parsed.recovery == recovery
    assert parsed.truncated is False


def test_comment_sentinel_is_metadata_not_a_card():
    parsed = parse_ai_payload('[{"front":"a"},{"_comment":"ok"}]')
    assert list(parsed.items) == [{"front": "a"}]
    assert parsed.comment == "ok"


@pytest.mark.parametrize(
    ("content", "category"),
    [
        ("{broken", "malformed_json"),
        ("This is only prose.", "malformed_json"),
        ('[{"front":"a"}] and [{"front":"b"}]', "ambiguous_json_payloads"),
        ('Text with {random braces} only.', "malformed_json"),
        ('{"payload":[{"front":"a"}]}', "invalid_wrapper"),
    ],
)
def test_unsafe_or_ambiguous_payloads_are_rejected(content, category):
    with pytest.raises(AiResponseParseError) as exc_info:
        parse_ai_payload(content)
    assert exc_info.value.category == category


def test_truncated_last_object_keeps_only_complete_prefix():
    parsed = parse_ai_payload('[{"front":"a"},{"front":"cut"')
    assert list(parsed.items) == [{"front": "a"}]
    assert parsed.truncated is True
    assert parsed.recovery == "partial_array_prefix"


def test_provider_structured_content_bypasses_prose_parsing():
    response = _adapted("", parsed={"cards": [_card("safe")]})
    result = process_ai_card_response(response, lang="english", kind="vocab")
    assert list(result.cards) == [_card("safe")]
    assert result.recovery == "structured:wrapper:cards"


def test_provider_finish_reason_marks_complete_json_as_truncated():
    response = _adapted(json.dumps([_card("a")]), finish_reason="length")
    with pytest.raises(AiOutputFailure) as exc_info:
        process_ai_card_response(response, lang="english", kind="vocab")
    assert exc_info.value.category == "truncation"
    assert list(exc_info.value.cards) == [_card("a")]


def test_language_level_identity_accepts_en_and_zh_contracts():
    en = validate_ai_cards([_card("reliable", cefr_level="B1")], lang="english", kind="vocab")
    zh = validate_ai_cards(
        [{"simplified": "学习", "meaning": "study", "hsk_level": "HSK1"}],
        lang="chinese", kind="vocab",
    )
    assert len(en.valid_cards) == len(zh.valid_cards) == 1


def test_english_hsk_is_schema_mismatch_not_silently_coerced():
    report = validate_ai_cards(
        [_card("opportunity", hsk_level="B1")], lang="english", kind="vocab",
    )
    assert not report.valid_cards
    assert report.invalid[0].category == "schema_language_mismatch"


def test_vocab_and_grammar_flows_reject_each_others_shapes():
    grammar_in_vocab = validate_ai_cards(
        [{"pattern": "used to + V", "meaning": "past habit", "usage": "S + used to + V"}],
        lang="english", kind="vocab",
    )
    vocab_in_grammar = validate_ai_cards(
        [_card("advice", usage_pattern="advice on + N")],
        lang="english", kind="grammar",
    )
    assert grammar_in_vocab.invalid[0].category == "grammar_in_vocab_flow"
    assert vocab_in_grammar.invalid[0].category == "vocab_in_grammar_flow"


def test_quality_v2_optional_and_multiline_fields_remain_valid():
    report = validate_ai_cards([_card(
        "advice",
        cefr_level="B1",
        usage_pattern="advice on + N\na piece of advice",
        usage_note="Uncountable\nNo *an advice*",
        collocation="seek advice — ask for guidance\nprofessional advice — expert guidance",
        example_3="",
        example_4="",
    )], lang="english", kind="vocab")
    assert len(report.valid_cards) == 1


def test_wrong_level_value_is_invalid():
    report = validate_ai_cards([_card("a", cefr_level="HSK3")], lang="english", kind="vocab")
    assert report.invalid[0].category == "invalid_level"


def test_completeness_reconciles_requested_valid_missing_and_duplicates():
    candidates = [{"front": f"w{i}"} for i in range(10)]
    cards = [_card(f"w{i}") for i in range(8)] + [_card("w0")]
    report = reconcile_expected_candidates(candidates, cards, kind="vocab")
    assert (report.requested, report.valid, report.missing, report.duplicates) == (10, 8, 2, 1)


def test_reconciliation_preserves_distinct_senses_of_one_identity():
    candidates = [
        {"front": "light", "meaning": "not heavy"},
        {"front": "light", "meaning": "illumination"},
    ]
    cards = [
        _card("light", meaning="illumination"),
        _card("light", meaning="not heavy"),
    ]
    report = reconcile_expected_candidates(candidates, cards, kind="vocab")
    assert [card["meaning"] for card in report.cards] == ["not heavy", "illumination"]
    assert report.missing == report.duplicates == 0


def _attempt(cards, *, invalid=(), duplicates=0):
    return AiCardResponse(
        tuple(cards), tuple(invalid), duplicates, len(cards), "", "array", False,
        "stop", "test", "test-model",
    )


def test_partial_retry_requests_only_unresolved_candidates(monkeypatch):
    calls = []

    def fake(batch, *args, **kwargs):
        fronts = [item["front"] for item in batch]
        calls.append(fronts)
        selected = fronts[:8] if len(fronts) == 10 else fronts
        return _attempt([_card(front) for front in selected])

    monkeypatch.setattr(batch_processor, "_call_ai_for_batch_response", fake)
    candidates = [{"front": f"w{i}"} for i in range(10)]
    result = batch_processor._resolve_batch_adaptively(
        candidates, "english", [], "", 1, 1, None,
        grammar=False, should_abort=None,
    )
    assert len(result.cards) == 10
    assert not result.unresolved
    assert calls == [[f"w{i}" for i in range(10)], ["w8", "w9"]]


def test_partial_retry_failure_is_bounded(monkeypatch):
    calls = []

    def fail(batch, *args, **kwargs):
        calls.append(len(batch))
        raise AiOutputFailure("truncation")

    monkeypatch.setattr(batch_processor, "_call_ai_for_batch_response", fail)
    candidates = [{"front": f"w{i}"} for i in range(4)]
    result = batch_processor._resolve_batch_adaptively(
        candidates, "english", [], "", 1, 1, None,
        grammar=False, should_abort=None,
    )
    assert len(result.unresolved) == 4
    assert result.attempts == 7
    assert calls == [4, 2, 1, 1, 2, 1, 1]


def test_large_truncated_batch_adaptively_splits_until_complete(monkeypatch):
    calls = []

    def size_limited(batch, *args, **kwargs):
        calls.append(len(batch))
        if len(batch) > 3:
            raise AiOutputFailure("truncation")
        return _attempt([_card(item["front"]) for item in batch])

    monkeypatch.setattr(batch_processor, "_call_ai_for_batch_response", size_limited)
    candidates = [{"front": f"w{i}"} for i in range(12)]
    result = batch_processor._resolve_batch_adaptively(
        candidates, "english", [], "", 1, 1, None,
        grammar=False, should_abort=None,
    )
    assert len(result.cards) == 12
    assert not result.unresolved
    assert calls == [12, 6, 3, 3, 6, 3, 3]


def test_retry_merge_drops_duplicate_without_losing_missing_card(monkeypatch):
    calls = 0

    def fake(batch, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _attempt([_card("a")])
        return _attempt([_card("a"), _card("b")])

    monkeypatch.setattr(batch_processor, "_call_ai_for_batch_response", fake)
    result = batch_processor._resolve_batch_adaptively(
        [{"front": "a"}, {"front": "b"}], "english", [], "", 1, 1, None,
        grammar=False, should_abort=None,
    )
    assert [card["front"] for card in result.cards] == ["a", "b"]
    assert result.unresolved == ()


def test_cancellation_is_checked_before_recovery_retry(monkeypatch):
    state = {"cancelled": False}

    def fail(batch, *args, **kwargs):
        state["cancelled"] = True
        raise AiOutputFailure("truncation")

    monkeypatch.setattr(batch_processor, "_call_ai_for_batch_response", fail)
    with pytest.raises(RuntimeError):
        batch_processor._resolve_batch_adaptively(
            [{"front": "a"}, {"front": "b"}], "english", [], "", 1, 1, None,
            grammar=False, should_abort=lambda: state["cancelled"],
        )


def test_text_extraction_retries_failed_source_spans_without_losing_prefix(monkeypatch):
    monkeypatch.setattr(ai_text_recovery, "MIN_TEXT_RECOVERY_CHARS", 1)

    def size_limited(source):
        if len(source) > 3:
            raise AiOutputFailure("truncation", cards=[_card(f"prefix-{len(source)}")])
        return [_card(source)]

    cards, unresolved = ai_text_recovery.recover_text_chunk(
        size_limited, "abcdefghijkl", progress_callback=None, should_abort=None,
    )
    assert unresolved == 0
    assert [card["front"] for card in cards] == [
        "prefix-12", "prefix-6", "abc", "def", "prefix-6", "ghi", "jkl",
    ]


def test_grammar_batch_merge_uses_pattern_identity(monkeypatch):
    monkeypatch.setattr(
        batch_processor, "get_api_config",
        lambda: {"max_tokens": 8192, "api_base": "https://api.openai.com/v1"},
    )
    monkeypatch.setattr(batch_processor, "_batch_cache_get", lambda *args, **kwargs: None)
    monkeypatch.setattr(batch_processor, "_batch_cache_set", lambda *args, **kwargs: None)
    monkeypatch.setattr(batch_processor, "is_openrouter", lambda: False)
    monkeypatch.setattr(
        batch_processor,
        "_call_ai_for_batch_response",
        lambda *args, **kwargs: _attempt([{
            "pattern": "used to + V",
            "meaning": "past habit",
            "usage": "S + used to + V",
        }]),
    )
    reports = []
    result = batch_processor.process_large_word_list(
        "used to + V : past habit : B1",
        "english",
        grammar=True,
        report_callback=reports.append,
    )
    assert result[0]["pattern"] == "used to + V"
    assert reports[0]["valid"] == reports[0]["requested"] == 1
    assert reports[0]["missing"] == 0


@pytest.mark.parametrize(
    ("lang", "grammar", "expected"),
    [
        ("english", False, 12),
        ("japanese", False, 10),
        ("chinese", False, 8),
        ("korean", True, 8),
    ],
)
def test_quality_v2_batch_policy_is_conservative_and_testable(lang, grammar, expected):
    assert batch_processor.recommended_quality_v2_batch_size(
        lang, grammar=grammar, max_output_tokens=8192,
    ) == expected


def test_reliability_benchmark_covers_5_10_20_30_cards():
    report = simulate_reliability_policy()
    scenarios = report["scenarios"]
    assert [item["requested_cards"] for item in scenarios] == [5, 10, 20, 30]
    assert all(item["success"] and item["complete_card_rate"] == 1.0 for item in scenarios)
    assert scenarios[-1]["retry_calls"] == 6
    assert scenarios[-1]["output_tokens"] is None


def test_batch_cache_key_preserves_candidate_sense_and_order(monkeypatch):
    monkeypatch.setattr(batch_processor, "get_signature", lambda: "sig")
    base = [{"front": "light", "meaning": "not heavy", "level": "A2", "topic": "adjective"}]
    other_sense = [{**base[0], "meaning": "illumination"}]
    assert batch_processor._batch_cache_key(base, "english", "", "deck") != (
        batch_processor._batch_cache_key(other_sense, "english", "", "deck")
    )
    assert batch_processor._batch_cache_key(
        [*base, *other_sense], "english", "", "deck",
    ) != batch_processor._batch_cache_key(
        [*other_sense, *base], "english", "", "deck",
    )
