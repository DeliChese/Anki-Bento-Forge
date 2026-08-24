"""Source-grounded Forge candidate manifest contracts."""

import json

import pytest

from utils import ai_candidate_extractor, ai_extractor
from utils.ai_response_guard import AdaptedAiResponse
from utils.ai_source_candidates import (
    CandidateOutputError,
    build_candidate_prompt,
    build_selected_candidate_instruction,
    mark_existing_candidate_surfaces,
    parse_source_candidate_response,
    validate_source_candidates,
)
from utils.ai_workspace import build_workspace_request_context


SOURCE = "The meeting was postponed, but the opportunity remained."


def _candidate(**overrides):
    item = {
        "kind": "vocab",
        "surface": "opportunity",
        "target": "opportunity",
        "meaning_hint": "a favorable chance",
        "source_excerpt": "the opportunity remained",
        "reason": "Useful B1 word in a clear contextual sense",
        "priority": "high",
    }
    item.update(overrides)
    return item


def _response(content, *, truncated=False, structured_data=None):
    return AdaptedAiResponse(
        text=content,
        structured_data=structured_data,
        finish_reason="length" if truncated else "stop",
        truncated=truncated,
        usage={},
        provider="custom",
        model="test-model",
    )


def _forge_request(source=SOURCE, *, lane="vocab", learning_mode="language"):
    return build_workspace_request_context(
        workspace="forge",
        language="english",
        user_instruction="Mine useful candidates",
        request_token="candidate-request",
        learning_mode=learning_mode,
        lane=lane,
        source_text=source,
    )


def test_candidate_prompt_is_strict_source_selection_not_card_generation():
    prompt = build_candidate_prompt("english", "vocab", english_ui=True)

    assert '"candidates"' in prompt
    assert "exactly from SOURCE" in prompt
    assert "do not invent cards" in prompt
    assert "source_excerpt" in prompt
    with pytest.raises(ValueError, match="lane"):
        build_candidate_prompt("english", "knowledge", english_ui=True)


def test_validation_keeps_grounded_items_stable_and_drops_internal_duplicates():
    report = validate_source_candidates(
        [_candidate(), _candidate(reason="Same identity again")],
        source_text=SOURCE,
        language="english",
        lane="vocab",
    )
    repeated = validate_source_candidates(
        [_candidate()], source_text=SOURCE, language="english", lane="vocab",
    )

    assert len(report.valid_candidates) == 1
    assert report.duplicate_count == 1
    assert not report.invalid
    assert report.valid_candidates[0]["candidate_id"] == repeated.valid_candidates[0]["candidate_id"]


@pytest.mark.parametrize(
    ("changes", "category"),
    [
        ({"surface": "invented"}, "candidate_not_grounded_in_source"),
        ({"source_excerpt": "not in source"}, "candidate_not_grounded_in_source"),
        ({"kind": "grammar"}, "candidate_kind_mismatch"),
        ({"target": ""}, "candidate_required_field_missing"),
        ({"meaning_hint": ""}, "candidate_required_field_missing"),
        ({"reason": ""}, "candidate_required_field_missing"),
        ({"priority": "urgent"}, "candidate_priority_invalid"),
        ({"unexpected": "metadata"}, "candidate_unknown_field"),
    ],
)
def test_validation_rejects_unproven_or_wrong_shape_candidates(changes, category):
    report = validate_source_candidates(
        [_candidate(**changes)], source_text=SOURCE, language="english", lane="vocab",
    )

    assert not report.valid_candidates
    assert report.invalid[0]["category"] == category


def test_parser_accepts_only_clean_complete_candidate_payloads():
    direct = parse_source_candidate_response(
        _response(json.dumps({"candidates": [_candidate()]})),
        source_text=SOURCE,
        language="english",
        lane="vocab",
    )
    structured = parse_source_candidate_response(
        _response("", structured_data={"candidates": [_candidate()]}),
        source_text=SOURCE,
        language="english",
        lane="vocab",
    )

    assert direct["schema_version"] == 1
    assert direct["source_digest"] == structured["source_digest"]
    assert len(direct["candidates"]) == 1


def test_distinct_contextual_senses_receive_distinct_candidate_ids():
    report = validate_source_candidates(
        [
            _candidate(meaning_hint="a favorable chance"),
            _candidate(meaning_hint="a suitable time"),
        ],
        source_text=SOURCE,
        language="english",
        lane="vocab",
    )

    assert len(report.valid_candidates) == 2
    assert len({item["candidate_id"] for item in report.valid_candidates}) == 2


@pytest.mark.parametrize(
    ("response", "category"),
    [
        (_response('{"candidates":['), "malformed_json"),
        (_response(json.dumps({"candidates": [_candidate()]}), truncated=True), "candidate_output_truncated"),
        (_response('Before {"candidates":[' + json.dumps(_candidate()) + "]} after"), "candidate_output_contains_prose"),
        (_response(json.dumps({"candidates": [_candidate()], "_comment": "extra"})), "candidate_output_contains_prose"),
        (_response(json.dumps({"candidates": [_candidate(surface="invented")]})), "candidate_output_has_no_valid_items"),
    ],
)
def test_parser_fails_closed_for_malformed_truncated_prose_or_ungrounded(response, category):
    with pytest.raises(CandidateOutputError) as exc_info:
        parse_source_candidate_response(
            response, source_text=SOURCE, language="english", lane="vocab",
        )
    assert exc_info.value.category == category


def test_existing_deck_match_is_advisory_and_selected_instruction_is_exact():
    manifest = parse_source_candidate_response(
        _response(json.dumps({"candidates": [
            _candidate(),
            _candidate(
                surface="postponed", target="postpone",
                meaning_hint="delay until later",
                source_excerpt="meeting was postponed",
                reason="Common verb in passive form",
                priority="medium",
            ),
        ]})),
        source_text=SOURCE,
        language="english",
        lane="vocab",
    )
    annotated = mark_existing_candidate_surfaces(manifest, ["opportunity"])
    chosen_id = annotated["candidates"][1]["candidate_id"]
    instruction = build_selected_candidate_instruction(
        annotated, [chosen_id], english_ui=True,
    )

    assert len(annotated["candidates"]) == 2
    assert annotated["existing_surface_count"] == 1
    assert annotated["candidates"][0]["existing_surface"] is True
    assert "postpone" in instruction
    assert "opportunity" not in instruction
    assert "do not add unselected items" in instruction


def test_candidate_ai_orchestration_uses_request_source_and_strict_mode(monkeypatch):
    captured = {}

    def fake_post(_url, payload, _headers, **_kwargs):
        captured["payload"] = payload
        return json.dumps({
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": json.dumps({"candidates": [_candidate()]})},
            }],
        })

    monkeypatch.setattr(ai_extractor, "ensure_ai_session_budget", lambda _text: {})
    monkeypatch.setattr(ai_extractor, "_ui_lang_en", lambda: True)
    monkeypatch.setattr(ai_extractor, "_http_post_json", fake_post)
    result = ai_candidate_extractor.extract_source_candidates_with_ai(
        "Mine useful candidates",
        lang="english",
        workspace_request=_forge_request(),
        runtime_config={
            "api_key": "test-key",
            "api_base": "https://example.test/v1",
            "model": "test-model",
            "temperature": 0.7,
            "max_tokens": 8192,
        },
    )
    message_text = "\n".join(item["content"] for item in captured["payload"]["messages"])

    assert result["error"] is None
    assert len(result["candidate_manifest"]["candidates"]) == 1
    assert SOURCE in message_text
    assert "do not invent cards" in message_text
    assert captured["payload"]["temperature"] == 0.2
    assert captured["payload"]["max_tokens"] == 4096


def test_candidate_ai_boundary_rejects_reviewer_missing_source_and_knowledge():
    reviewer = build_workspace_request_context(
        workspace="reviewer", language="english", user_instruction="Mine",
        request_token="reviewer-candidate",
    )
    with pytest.raises(ValueError, match="ownership"):
        ai_candidate_extractor.extract_source_candidates_with_ai(
            "Mine", lang="english", workspace_request=reviewer,
        )
    with pytest.raises(ValueError, match="source"):
        ai_candidate_extractor.extract_source_candidates_with_ai(
            "Mine", lang="english", workspace_request=_forge_request(""),
        )
    with pytest.raises(ValueError, match="language workflow"):
        ai_candidate_extractor.extract_source_candidates_with_ai(
            "Mine", lang="english",
            workspace_request=_forge_request("Facts", learning_mode="knowledge"),
        )
