"""V18-05 strict Knowledge AI/cancel/cache boundary tests."""

import json

import pytest

from utils import knowledge_extractor as extractor
from utils import ai_extractor
from utils.ai_prompt_defaults import KNOWLEDGE_PROMPT_VERSION


def _response(cards):
    return json.dumps({"choices": [{"message": {"content": json.dumps(cards)}}]})


def _card(question="What is CPU?"):
    return {
        "type": "basic", "question": question, "answer": "Central Processing Unit",
        "explanation": "", "source": "", "tags": [], "cloze_text": "",
    }


def test_knowledge_ai_uses_strict_parser_and_never_fills_missing_source(monkeypatch):
    monkeypatch.setattr(extractor, "get_api_config", lambda: {
        "api_key": "test", "api_base": "https://example.invalid", "model": "test",
        "temperature": 0, "max_tokens": 1000, "max_chars": 10000,
    })
    monkeypatch.setattr(extractor, "_ai_cache_get", lambda *a, **k: None)
    saved = {}
    monkeypatch.setattr(extractor, "_ai_cache_set", lambda *a, **k: saved.setdefault("cards", a[4]))
    monkeypatch.setattr(extractor, "post_json", lambda *a, **k: _response([_card()]))

    cards = extractor.extract_knowledge_with_ai("CPU notes")
    assert cards[0]["source"] == ""
    assert saved["cards"] == cards


def test_knowledge_ai_rejects_ambiguous_or_partial_response(monkeypatch):
    monkeypatch.setattr(extractor, "get_api_config", lambda: {
        "api_key": "test", "api_base": "https://example.invalid", "model": "test",
        "temperature": 0, "max_tokens": 1000, "max_chars": 10000,
    })
    monkeypatch.setattr(extractor, "_ai_cache_get", lambda *a, **k: None)
    monkeypatch.setattr(extractor, "post_json", lambda *a, **k: _response([{"type": "basic"}]))
    with pytest.raises(ValueError):
        extractor.extract_knowledge_with_ai("bad")


def test_knowledge_long_text_cancel_stops_before_network(monkeypatch):
    monkeypatch.setattr(extractor, "ensure_ai_session_budget", lambda text: {})
    monkeypatch.setattr(extractor, "get_api_config", lambda: {"chunk_size": 2})
    monkeypatch.setattr(
        extractor, "extract_knowledge_with_ai",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network must not run")),
    )
    with pytest.raises(RuntimeError):
        extractor.extract_knowledge_long_text("abcd", should_abort=lambda: True)


def test_knowledge_cache_uses_its_own_prompt_version_and_no_language_override(monkeypatch):
    captured = {}

    def fake_key(*args, **kwargs):
        captured.update(kwargs)
        return "key"

    monkeypatch.setattr(ai_extractor, "_build_ai_cache_key", fake_key)
    assert ai_extractor._ai_cache_key("text", "knowledge", "", "hash", kind="knowledge") == "key"
    assert captured["prompt_version"] == KNOWLEDGE_PROMPT_VERSION
    assert captured["prompt_signature"] == ""
