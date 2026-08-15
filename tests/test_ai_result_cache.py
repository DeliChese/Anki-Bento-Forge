"""Tests for the isolated AI result cache owner."""

import ast
import hashlib
import json
from pathlib import Path

from utils import ai_result_cache as cache


def test_cache_owner_has_no_ai_workflow_anki_or_ui_dependency():
    source = Path(cache.__file__).read_text(encoding="utf-8")
    imports = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert not imports.intersection({"ai_extractor", "prompt_config", "aqt", "ui"})


def test_build_cache_key_preserves_legacy_format_and_dimensions():
    expected_raw = "5|sig|vocab|japanese|instruction|existing|text"
    expected = hashlib.md5(expected_raw.encode("utf-8")).hexdigest()

    actual = cache.build_cache_key(
        "text",
        "japanese",
        "instruction",
        "existing",
        prompt_version=5,
        prompt_signature="sig",
    )

    assert actual == expected
    assert cache.build_cache_key(
        "text",
        "japanese",
        "instruction",
        "existing",
        kind="grammar",
        prompt_version=5,
        prompt_signature="sig",
    ) != actual


def test_cache_round_trip_preserves_schema_and_provider_ttl(tmp_path):
    cache_dir = tmp_path / "cache"
    legacy_dir = tmp_path / "legacy"
    result = [{"front": "食べる", "meaning": "ăn"}]

    cache.set_cached_result(
        "text",
        "japanese",
        "",
        "existing",
        result,
        cache_dir=str(cache_dir),
        legacy_cache_dir=str(legacy_dir),
        prompt_signature="sig",
    )

    cache_file = next(cache_dir.glob("ai_*.json"))
    payload = json.loads(cache_file.read_text(encoding="utf-8"))
    assert payload["vocab"] == result
    assert payload["_kind"] == "vocab"
    assert payload["_lang"] == "japanese"

    cached_at = payload["_cached_at"]
    after_eight_days = lambda: cached_at + 8 * 24 * 3600
    common = {
        "cache_dir": str(cache_dir),
        "legacy_cache_dir": str(legacy_dir),
        "prompt_signature": "sig",
        "now": after_eight_days,
    }
    assert cache.get_cached_result(
        "text", "japanese", "", "existing", is_openrouter=lambda: False, **common
    ) is None
    assert cache.get_cached_result(
        "text", "japanese", "", "existing", is_openrouter=lambda: True, **common
    ) == result


def test_cache_miss_and_clear_are_scoped_to_cache_directory(tmp_path):
    cache_dir = tmp_path / "cache"
    legacy_dir = tmp_path / "legacy"
    persistent_file = tmp_path / "profile.json"
    persistent_file.write_text("keep", encoding="utf-8")

    provider_checks = []
    assert cache.get_cached_result(
        "missing",
        "korean",
        "",
        "none",
        cache_dir=str(cache_dir),
        legacy_cache_dir=str(legacy_dir),
        prompt_signature="sig",
        is_openrouter=lambda: provider_checks.append(True) or False,
    ) is None
    assert provider_checks == []

    cache.clear_result_cache(str(cache_dir))
    assert not cache_dir.exists()
    assert persistent_file.read_text(encoding="utf-8") == "keep"


def test_ai_extractor_keeps_cache_api_compatibility(monkeypatch, tmp_path):
    from utils import ai_extractor

    monkeypatch.setattr(ai_extractor, "_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(ai_extractor, "_LEGACY_CACHE_DIR", str(tmp_path / "legacy"))
    monkeypatch.setattr(ai_extractor, "get_prompt_signature", lambda: "sig")
    monkeypatch.setattr(ai_extractor, "is_openrouter", lambda api_base=None: False)

    expected = [{"front": "먹다"}]
    ai_extractor._ai_cache_set("text", "korean", "", "existing", expected)
    assert ai_extractor._ai_cache_get("text", "korean", "", "existing") == expected
    assert ai_extractor._PROMPT_VERSION == cache.DEFAULT_PROMPT_VERSION

    ai_extractor.clear_cache()
    assert not (tmp_path / "cache").exists()
