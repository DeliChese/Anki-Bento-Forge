"""Release-gate regressions for deterministic AI output reliability."""

import json

import pytest

from utils import ai_extractor, ai_study_prompts, batch_processor
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


def _chat_result(
    monkeypatch, *, content="", parsed=None, finish_reason="stop",
    reasoning_content="", lang="english", card_kind="vocab", card_mode="__selected__",
):
    message = {"content": content}
    if parsed is not None:
        message["parsed"] = parsed
    if reasoning_content:
        message["reasoning_content"] = reasoning_content
    provider_result = {
        "choices": [{"finish_reason": finish_reason, "message": message}],
    }
    monkeypatch.setattr(ai_extractor, "get_api_config", lambda: {
        "api_key": "test-key",
        "api_base": "https://api.openai.com/v1",
        "model": "test-model",
        "temperature": 0.3,
        "max_tokens": 8192,
    })
    monkeypatch.setattr(ai_extractor, "ensure_ai_session_budget", lambda _text: {})
    monkeypatch.setattr(
        ai_extractor, "_http_post_json",
        lambda *args, **kwargs: json.dumps(provider_result),
    )
    selected_mode = card_kind if card_mode == "__selected__" else card_mode
    return ai_extractor.chat_with_ai(
        "test request", lang=lang, quick=True, card_kind=card_kind,
        card_mode=selected_mode,
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


def test_chat_prose_only_remains_a_normal_reply(monkeypatch):
    result = _chat_result(
        monkeypatch,
        content="Opportunity is broader than chance in many contexts.",
        card_mode=None,
    )
    assert result["reply"].startswith("Opportunity is broader")
    assert result["vocab_json"] is None
    assert result["card_error"] is None
    assert result["card_warning"] is None
    assert result["error"] is None


def test_chat_fenced_vocab_uses_shared_parser_and_removes_raw_json(monkeypatch):
    card = _card("opportunity", cefr_level="B1")
    result = _chat_result(
        monkeypatch, content=f"```json\n{json.dumps([card])}\n```",
    )
    assert result["vocab_json"] == [card]
    assert result["reply"] == ""
    assert result["card_error"] is None


def test_chat_prose_plus_json_preserves_only_surrounding_prose(monkeypatch):
    card = _card("chance", cefr_level="A2")
    result = _chat_result(
        monkeypatch,
        content=f"Here are your cards:\n\n{json.dumps([card])}\n\nImport them now.",
    )
    assert result["vocab_json"] == [card]
    assert result["reply"] == "Here are your cards:\n\n\n\nImport them now."
    assert json.dumps([card]) not in result["reply"]


def test_chat_known_cards_wrapper_is_accepted(monkeypatch):
    card = _card("reliable", cefr_level="B2")
    result = _chat_result(
        monkeypatch, content=json.dumps({"cards": [card]}),
    )
    assert result["vocab_json"] == [card]
    assert result["card_error"] is None


def test_chat_provider_structured_cards_are_accepted(monkeypatch):
    card = _card("structured", cefr_level="B1")
    result = _chat_result(
        monkeypatch, content="Cards are ready.", parsed={"cards": [card]},
    )
    assert result["reply"] == "Cards are ready."
    assert result["vocab_json"] == [card]


def test_chat_english_cefr_card_is_accepted(monkeypatch):
    card = _card("precise", cefr_level="C1")
    result = _chat_result(monkeypatch, content=json.dumps([card]))
    assert result["vocab_json"] == [card]


def test_chat_english_hsk_card_never_reaches_factory(monkeypatch):
    result = _chat_result(
        monkeypatch,
        content=json.dumps([_card("opportunity", hsk_level="B1")]),
    )
    assert result["vocab_json"] is None
    assert result["card_error"] == "schema_mismatch"
    assert result["card_warning"]
    assert result["error"] is None


def test_chat_grammar_shape_is_rejected_in_vocab_flow(monkeypatch):
    result = _chat_result(monkeypatch, content=json.dumps([{
        "pattern": "used to + V",
        "meaning": "past habit",
        "usage": "S + used to + V",
    }]))
    assert result["vocab_json"] is None
    assert result["card_error"] == "schema_mismatch"


def test_chat_grammar_mode_returns_validated_raw_cards(monkeypatch):
    card = {
        "pattern": "used to + V",
        "meaning": "past habit",
        "usage": "S + used to + V",
        "cefr_level": "B1",
    }
    result = _chat_result(
        monkeypatch, content=json.dumps([card]), card_kind="grammar",
    )
    assert result["card_kind"] == "grammar"
    assert result["card_json"] == [card]
    assert result["vocab_json"] == [card]
    assert result["card_error"] is None


def test_chat_prompt_requests_only_the_selected_grammar_schema(monkeypatch):
    requested = []
    monkeypatch.setattr(ai_extractor, "_ui_lang_en", lambda: True)
    monkeypatch.setattr(
        ai_study_prompts, "get_json_template",
        lambda lang, kind: requested.append((lang, kind)) or f"{kind.upper()}_SCHEMA",
    )
    prompt = ai_extractor._get_chat_system_prompt("english", "grammar")
    assert requested == [("english", "grammar")]
    assert "GRAMMAR_SCHEMA" in prompt
    assert "VOCAB_SCHEMA" not in prompt


def test_study_chat_prompt_never_loads_a_card_schema(monkeypatch):
    requested = []
    monkeypatch.setattr(ai_study_prompts, "get_json_template", lambda *args: requested.append(args))
    prompt = ai_extractor._get_study_chat_system_prompt("english", None)
    assert requested == []
    assert "Card Mode" in prompt


def test_study_chat_treats_unsolicited_json_as_prose(monkeypatch):
    card = _card("unsolicited", cefr_level="B1")
    result = _chat_result(monkeypatch, content=json.dumps([card]), card_mode=None)
    assert result["card_json"] is None
    assert "unsolicited" in result["reply"]
    assert result["card_mode"] is None


def test_chat_prose_with_ordinary_braces_is_not_a_card_error(monkeypatch):
    result = _chat_result(
        monkeypatch, content="Use {braces} when describing a placeholder.", card_mode=None,
    )
    assert result["reply"] == "Use {braces} when describing a placeholder."
    assert result["vocab_json"] is None
    assert result["card_error"] is None


def test_chat_two_json_payloads_are_not_auto_selected(monkeypatch):
    result = _chat_result(
        monkeypatch,
        content=(
            f"First option:\n{json.dumps([_card('first', cefr_level='A1')])}\n"
            f"Second option:\n{json.dumps([_card('second', cefr_level='A1')])}"
        ),
    )
    assert result["vocab_json"] is None
    assert result["card_error"] == "ambiguous_json_payloads"
    assert result["card_warning"]


def test_chat_truncated_card_prefix_is_not_imported(monkeypatch):
    result = _chat_result(
        monkeypatch,
        content='[{"front":"safe","meaning":"ok","cefr_level":"A1"},{"front":"cut"',
        finish_reason="length",
    )
    assert result["vocab_json"] is None
    assert result["card_error"] == "truncation"
    assert result["card_warning"]


def test_chat_reasoning_only_never_becomes_card_data(monkeypatch):
    result = _chat_result(
        monkeypatch, content="", reasoning_content='[{"front":"private"}]',
    )
    assert result["vocab_json"] is None
    assert result["reply"] == ""
    assert result["error"]


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


def test_text_recovery_discards_parent_prefix_when_split_is_authoritative(monkeypatch):
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
        "abc", "def", "ghi", "jkl",
    ]


def test_text_recovery_deduplicates_overlapping_child_identity(monkeypatch):
    monkeypatch.setattr(ai_text_recovery, "MIN_TEXT_RECOVERY_CHARS", 1)

    def overlap(source):
        if len(source) > 3:
            raise AiOutputFailure("truncation", cards=[_card("provisional")])
        return [_card("shared", meaning="same sense"), _card(source)]

    cards, unresolved = ai_text_recovery.recover_text_chunk(
        overlap, "abcdef", progress_callback=None, should_abort=None,
    )
    assert unresolved == 0
    assert [card["front"] for card in cards] == ["shared", "abc", "def"]


def test_text_recovery_preserves_same_lemma_with_distinct_senses(monkeypatch):
    monkeypatch.setattr(ai_text_recovery, "MIN_TEXT_RECOVERY_CHARS", 1)

    def distinct_senses(source):
        if len(source) > 3:
            raise AiOutputFailure("truncation")
        meaning = "illumination" if source == "abc" else "not heavy"
        return [_card("light", meaning=meaning)]

    cards, unresolved = ai_text_recovery.recover_text_chunk(
        distinct_senses, "abcdef", progress_callback=None, should_abort=None,
    )
    assert unresolved == 0
    assert [card["meaning"] for card in cards] == ["illumination", "not heavy"]


def test_text_recovery_depth_remains_bounded(monkeypatch):
    monkeypatch.setattr(ai_text_recovery, "MIN_TEXT_RECOVERY_CHARS", 1)
    calls = []

    def always_truncated(source):
        calls.append(source)
        raise AiOutputFailure("truncation", cards=[_card(source)])

    cards, unresolved = ai_text_recovery.recover_text_chunk(
        always_truncated, "abcdefghijkl", progress_callback=None,
        should_abort=None,
    )
    assert len(calls) == 7
    assert unresolved == 4
    assert [card["front"] for card in cards] == ["abc", "def", "ghi", "jkl"]


def test_text_recovery_cancellation_between_children_still_works(monkeypatch):
    monkeypatch.setattr(ai_text_recovery, "MIN_TEXT_RECOVERY_CHARS", 1)
    state = {"calls": 0}

    def cancel_after_left(source):
        state["calls"] += 1
        if len(source) > 3:
            raise AiOutputFailure("truncation")
        return [_card(source)]

    with pytest.raises(RuntimeError):
        ai_text_recovery.recover_text_chunk(
            cancel_after_left, "abcdef", progress_callback=None,
            should_abort=lambda: state["calls"] >= 2,
        )


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
