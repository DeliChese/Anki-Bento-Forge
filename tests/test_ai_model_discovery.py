"""Model catalog discovery remains provider-aware and secret-safe."""

import json
from pathlib import Path
from unittest.mock import patch

from utils.ai_model_discovery import (
    build_model_catalog_request,
    fetch_provider_models,
    load_cached_models,
    model_cache_is_fresh,
    parse_model_catalog,
    save_cached_models,
)


def test_openai_compatible_catalog_uses_bearer_header_not_query_string():
    url, headers = build_model_catalog_request(
        "openai", "https://api.openai.com/v1", "sk-secret",
    )
    assert url == "https://api.openai.com/v1/models"
    assert "sk-secret" not in url
    assert headers["Authorization"] == "Bearer sk-secret"


def test_gemini_catalog_uses_official_endpoint_and_filters_non_generation_models():
    url, headers = build_model_catalog_request(
        "gemini", "https://generativelanguage.googleapis.com/v1beta/openai", "AIza-secret",
    )
    assert url == "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000"
    assert "AIza-secret" not in url
    assert headers["x-goog-api-key"] == "AIza-secret"

    payload = {"models": [
        {"name": "models/gemini-flash-latest", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-embedding-001", "supportedGenerationMethods": ["embedContent"]},
    ]}
    assert parse_model_catalog(payload, "gemini") == ["gemini-flash-latest"]


def test_ollama_catalog_uses_tags_and_parses_installed_models():
    url, headers = build_model_catalog_request("ollama", "http://localhost:11434/v1")
    assert url == "http://localhost:11434/api/tags"
    assert "Authorization" not in headers
    assert parse_model_catalog({"models": [{"name": "qwen3.5:latest"}]}, "ollama") == [
        "qwen3.5:latest"
    ]


def test_anthropic_catalog_uses_native_versioned_auth_headers():
    url, headers = build_model_catalog_request(
        "anthropic", "https://api.anthropic.com/v1", "sk-ant-secret",
    )
    assert url == "https://api.anthropic.com/v1/models"
    assert headers["x-api-key"] == "sk-ant-secret"
    assert headers["anthropic-version"] == "2023-06-01"
    assert "Authorization" not in headers


def test_model_parser_deduplicates_and_drops_obvious_non_chat_models():
    payload = {"data": [
        {"id": "gpt-5"}, {"id": "GPT-5"}, {"id": "text-embedding-3-small"},
        {"id": "gpt-4o-realtime-preview"}, {"id": "o4-mini"},
    ]}
    assert parse_model_catalog(payload, "openai") == ["gpt-5", "o4-mini"]


def test_fetch_models_reads_bounded_json_response():
    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size):
            return json.dumps({"data": [{"id": "model-new"}]}).encode("utf-8")

    with patch("utils.ai_model_discovery.urllib.request.urlopen", return_value=_Response()) as opened:
        models = fetch_provider_models("openai", "https://api.openai.com/v1", "secret")

    assert models == ["model-new"]
    request = opened.call_args.args[0]
    assert request.full_url == "https://api.openai.com/v1/models"
    assert request.get_header("Authorization") == "Bearer secret"


def test_model_catalog_cache_is_profile_scoped_and_never_contains_key(tmp_path, monkeypatch):
    monkeypatch.setenv("BENTO_FORGE_DATA_DIR", str(tmp_path))
    save_cached_models("openai", "https://api.openai.com/v1", ["gpt-new", "gpt-new"])

    assert load_cached_models("openai", "https://api.openai.com/v1") == ["gpt-new"]
    assert model_cache_is_fresh("openai", "https://api.openai.com/v1") is True
    raw = (tmp_path / "ai_model_catalog.json").read_text(encoding="utf-8")
    assert "api_key" not in raw
    assert "secret" not in raw


def test_ai_settings_refreshes_catalog_in_background_and_keeps_manual_retry():
    source = Path("ui/ai_settings.py").read_text(encoding="utf-8")
    assert "mw.taskman.run_in_background(task, on_done, uses_collection=False)" in source
    assert "_schedule_model_refresh(" in source
    assert "btn_refresh_models.clicked.connect(_refresh_current_models)" in source
    assert "txt_key.editingFinished.connect(_refresh_current_models)" in source
