"""Tests for API-key migration to the OS credential store."""

from unittest.mock import patch


def test_save_never_writes_api_key_to_json():
    from utils.ai_extractor import save_api_config

    with patch("utils.ai_extractor.save_api_key", return_value=True), patch("utils.ai_extractor._save_config") as save:
        assert save_api_config("sk-secret", "https://api.example/v1", "model") is True

    persisted = save.call_args.args[0]
    assert persisted["api_key_storage"] == "keyring"
    assert "api_key" not in persisted


def test_keyring_failure_does_not_fall_back_to_xor_or_plaintext():
    from utils.ai_extractor import save_api_config

    with patch("utils.ai_extractor.save_api_key", return_value=False), patch("utils.ai_extractor._save_config") as save:
        assert save_api_config("sk-secret", "https://api.example/v1", "model") is False

    persisted = save.call_args.args[0]
    assert persisted["api_key_storage"] == "unavailable"
    assert "api_key" not in persisted


def test_legacy_key_is_migrated_and_removed_from_config():
    from utils.ai_extractor import get_api_config

    legacy_config = {"api_key": "sk-legacy", "model": "model"}
    with patch("utils.ai_extractor._load_config", return_value=legacy_config), patch(
        "utils.ai_extractor.save_api_key", return_value=True
    ), patch("utils.ai_extractor._save_config") as save:
        cfg = get_api_config()

    assert cfg["api_key"] == "sk-legacy"
    persisted = save.call_args.args[0]
    assert persisted["api_key_storage"] == "keyring"
    assert "api_key" not in persisted


def test_failed_legacy_migration_removes_reversible_value():
    from utils.ai_extractor import get_api_config

    legacy_config = {"api_key": "x:legacy-value", "model": "model"}
    with patch("utils.ai_extractor._load_config", return_value=legacy_config), patch(
        "utils.ai_extractor.save_api_key", return_value=False
    ), patch("utils.ai_extractor._save_config") as save:
        cfg = get_api_config()

    assert cfg["api_key"] == ""
    persisted = save.call_args.args[0]
    assert persisted["api_key_storage"] == "unavailable"
    assert "api_key" not in persisted
