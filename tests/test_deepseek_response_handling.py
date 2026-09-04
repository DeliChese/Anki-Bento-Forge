"""Regression coverage for DeepSeek reasoning-model response boundaries."""

import json

import pytest

from utils import ai_extractor
from utils.ai_response_guard import enable_deepseek_json_output
from utils.i18n import t


_DEEPSEEK_CONFIG = {
    "api_key": "test-key",
    "api_base": "https://api.deepseek.com/v1",
    "model": "deepseek-reasoner",
    "temperature": 0.3,
    "max_tokens": 8192,
}


def _mock_extractor_response(monkeypatch, response):
    monkeypatch.setattr(ai_extractor, "get_api_config", lambda: dict(_DEEPSEEK_CONFIG))
    monkeypatch.setattr(ai_extractor, "_ai_cache_get", lambda *args, **kwargs: None)
    monkeypatch.setattr(ai_extractor, "_ai_cache_set", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        ai_extractor,
        "_http_post_json",
        lambda *args, **kwargs: json.dumps(response),
    )


def _response(content, reasoning="", finish_reason="stop"):
    return {
        "choices": [{
            "finish_reason": finish_reason,
            "message": {"content": content, "reasoning_content": reasoning},
        }]
    }


def test_vocab_uses_final_content_not_reasoning_content(monkeypatch):
    _mock_extractor_response(
        monkeypatch,
        _response('{"items":[{"front":"taberu","meaning":"eat"}]}', reasoning="not JSON"),
    )

    cards = ai_extractor.extract_vocabulary_with_ai("eat", "japanese")

    assert cards == [{"front": "taberu", "meaning": "eat"}]


def test_direct_card_generation_marks_learner_request_as_not_source_material(monkeypatch):
    payloads = []
    monkeypatch.setattr(ai_extractor, "get_api_config", lambda: dict(_DEEPSEEK_CONFIG))
    monkeypatch.setattr(ai_extractor, "_ui_lang_en", lambda: True)
    monkeypatch.setattr(ai_extractor, "_ai_cache_get", lambda *args, **kwargs: None)
    monkeypatch.setattr(ai_extractor, "_ai_cache_set", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        ai_extractor,
        "_http_post_json",
        lambda _url, payload, *_args, **_kwargs: (
            payloads.append(payload)
            or json.dumps(_response('{"items":[{"front":"taberu","meaning":"eat"}]}'))
        ),
    )

    cards = ai_extractor.extract_vocabulary_with_ai(
        "Tạo từ vựng nhà hàng", "japanese", generation_request=True,
    )

    assert cards == [{"front": "taberu", "meaning": "eat"}]
    assert "not source material" in payloads[0]["messages"][-1]["content"]


def test_json_mode_is_enabled_only_for_direct_deepseek_requests():
    payload = {}
    enable_deepseek_json_output(payload, _DEEPSEEK_CONFIG)
    assert payload["response_format"] == {"type": "json_object"}

    gemini_payload = {}
    enable_deepseek_json_output(
        gemini_payload,
        {"api_base": "https://generativelanguage.googleapis.com/v1beta/openai"},
    )
    assert "response_format" not in gemini_payload


def test_v4_card_requests_default_to_benchmarked_non_thinking_mode():
    payload = {}
    enable_deepseek_json_output(
        payload,
        dict(_DEEPSEEK_CONFIG, model="deepseek-v4-flash"),
    )

    assert payload["thinking"] == {"type": "disabled"}


def test_v4_thinking_mode_can_be_explicitly_enabled():
    payload = {}
    enable_deepseek_json_output(
        payload,
        dict(_DEEPSEEK_CONFIG, model="deepseek-v4-pro", thinking_mode="enabled"),
    )

    assert payload["thinking"] == {"type": "enabled"}


def test_vocab_rejects_reasoning_only_response(monkeypatch):
    _mock_extractor_response(monkeypatch, _response("", reasoning="internal thinking"))

    with pytest.raises(RuntimeError, match="reasoning|suy luận"):
        ai_extractor.extract_vocabulary_with_ai("eat", "japanese")


def test_grammar_reports_token_limit_before_parsing(monkeypatch):
    _mock_extractor_response(
        monkeypatch,
        _response('[{"pattern":"partial"}]', finish_reason="length"),
    )

    with pytest.raises(RuntimeError) as exc_info:
        ai_extractor.extract_grammar_with_ai("partial", "japanese")

    assert str(exc_info.value) == t("error_model_output_truncated")


@pytest.mark.skip(reason="large Batch production was removed")
def test_batch_rejects_reasoning_only_response(monkeypatch):
    monkeypatch.setattr(batch_processor, "get_api_config", lambda: dict(_DEEPSEEK_CONFIG))
    monkeypatch.setattr(batch_processor, "get_system_prompt", lambda *args: "system")
    monkeypatch.setattr(
        batch_processor,
        "_http_post_json",
        lambda *args, **kwargs: json.dumps(_response("", reasoning="internal thinking")),
    )

    with pytest.raises(RuntimeError, match="reasoning|suy luận"):
        batch_processor._call_ai_for_batch(
            [{"front": "taberu", "meaning": "eat"}], "japanese", []
        )
