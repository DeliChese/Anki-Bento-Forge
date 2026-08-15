"""Contract tests for AI provider presets (utils/ai_providers.py)."""

import pytest

from utils.ai_providers import (
    AI_PROVIDERS,
    PROVIDER_MAP,
    detect_provider,
    get_provider,
    get_providers,
)


def test_provider_presets_are_unique_and_complete():
    ids = [p["id"] for p in AI_PROVIDERS]
    assert len(ids) == len(set(ids)), "Provider ids must be unique"
    assert "gemini" in ids, "Gemini provider must exist"
    assert "deepseek" in ids
    assert "openai" in ids
    assert "anthropic" in ids
    assert "openrouter" in ids
    assert "ollama" in ids
    assert "lmstudio" in ids


def test_each_provider_has_valid_models_and_default():
    for provider in AI_PROVIDERS:
        assert provider["models"], f"{provider['id']} must have models"
        assert provider["default"] in provider["models"], (
            f"{provider['id']}.default must be one of its models"
        )
        assert provider["base"].startswith(("http://", "https://"))
        assert provider["color"].startswith("#") and len(provider["color"]) == 7


def test_provider_models_are_not_shared():
    """Mỗi provider phải có model riêng, không nhầm lẫn giữa các hãng."""
    for provider in AI_PROVIDERS:
        for model in provider["models"]:
            assert model, f"{provider['id']} has an empty model name"


def test_gemini_models_are_accurate():
    gemini = get_provider("gemini")
    assert gemini is not None
    assert "gemini-3.6-flash" in gemini["models"]
    assert "gemini-3.6-pro" in gemini["models"]
    assert "gemini-3.5-flash" in gemini["models"]
    # OpenAI/DeepSeek models must NOT appear in Gemini list
    assert "gpt-4o-mini" not in gemini["models"]
    assert "deepseek-chat" not in gemini["models"]
    # Gemini keys start with AIza → base URL must be Google
    assert "googleapis" in gemini["base"] or "generativelanguage" in gemini["base"]


def test_deepseek_models_are_accurate():
    provider = get_provider("deepseek")
    assert provider is not None
    assert "deepseek-chat" in provider["models"]
    assert "deepseek-reasoner" in provider["models"]
    assert "gpt-4o-mini" not in provider["models"]


def test_anthropic_models_are_accurate():
    provider = get_provider("anthropic")
    assert provider is not None
    assert any("claude" in m for m in provider["models"]), "All Anthropic models contain 'claude'"
    assert any("gpt-" in m for m in provider["models"]) is False


def test_openrouter_models_vendor_prefixed():
    provider = get_provider("openrouter")
    assert provider is not None
    for model in provider["models"]:
        assert "/" in model, "OpenRouter models must be vendor/model"


def test_detect_provider():
    assert detect_provider("https://api.deepseek.com/v1") == "deepseek"
    assert detect_provider("https://api.openai.com/v1") == "openai"
    assert detect_provider("https://generativelanguage.googleapis.com/v1beta/openai") == "gemini"
    assert detect_provider("https://api.anthropic.com/v1") == "anthropic"
    assert detect_provider("https://openrouter.ai/api/v1") == "openrouter"
    assert detect_provider("http://localhost:11434/v1") == "ollama"
    assert detect_provider("http://localhost:1234/v1") == "lmstudio"
    assert detect_provider("") == ""


def test_get_providers_returns_copies():
    p1 = get_providers()
    p2 = get_providers()
    assert p1 == p2
    assert p1 is not p2
    p1[0]["models"].append("__mutated__")
    assert "__mutated__" not in get_providers()[0]["models"]


def test_every_preset_detects_its_own_base():
    for provider in AI_PROVIDERS:
        assert detect_provider(provider["base"]) == provider["id"], (
            f"detect_provider failed for {provider['id']}"
        )