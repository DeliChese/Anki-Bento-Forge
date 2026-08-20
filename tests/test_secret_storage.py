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


def test_get_api_config_loads_key_from_credential_store():
    """Khi config khai báo keyring, key phải được đọc lại từ credential store.

    Regression: "api_key" từng nằm trong `defaults` của get_api_config(), khiến
    `if "api_key" in cfg` luôn đúng và keyring branch không bao giờ chạy → key
    đã lưu biến mất khi mở lại cài đặt.
    """
    from utils.ai_extractor import get_api_config

    stored = {"api_key_storage": "keyring", "model": "model", "api_base": "https://x/v1"}
    with patch("utils.ai_extractor._load_config", return_value=stored), patch(
        "utils.ai_extractor.load_api_key", return_value="sk-stored"
    ):
        cfg = get_api_config()

    assert cfg["api_key"] == "sk-stored"
    assert cfg["api_key_storage"] == "keyring"


def test_get_api_config_keyring_branch_not_blocked_by_empty_api_key():
    """Đảm bảo khóa `api_key` không bị defaults chèn vào khiến nhánh keyring bị bỏ qua."""
    from utils.ai_extractor import get_api_config

    stored = {"api_key_storage": "keyring", "model": "model"}
    with patch("utils.ai_extractor._load_config", return_value=stored), patch(
        "utils.ai_extractor.load_api_key", return_value="sk-live"
    ):
        cfg = get_api_config()

    assert cfg["api_key"] == "sk-live"


def test_provider_keys_use_distinct_credential_scopes():
    """Saving OpenAI never overwrites the credential belonging to DeepSeek."""
    from utils.ai_extractor import save_api_config

    with patch("utils.ai_extractor.save_api_key", return_value=True) as save, patch(
        "utils.ai_extractor._save_config"
    ):
        save_api_config("deepseek-key", "https://api.deepseek.com/v1", "deepseek-chat", provider="deepseek")
        save_api_config("openai-key", "https://api.openai.com/v1", "gpt-4o-mini", provider="openai")

    assert save.call_args_list[0].args == ("deepseek-key", "deepseek")
    assert save.call_args_list[1].args == ("openai-key", "openai")


def test_get_api_key_for_provider_reads_only_its_own_key():
    from utils.ai_extractor import get_api_key_for_provider

    with patch("utils.ai_extractor.load_api_key", side_effect=lambda scope: {
        "deepseek": "deepseek-key", "openai": "openai-key",
    }.get(scope, "")):
        assert get_api_key_for_provider("deepseek", "https://api.deepseek.com/v1") == "deepseek-key"
        assert get_api_key_for_provider("openai", "https://api.openai.com/v1") == "openai-key"


def test_generic_key_migrates_once_to_the_active_provider():
    from utils.ai_extractor import get_api_config

    stored = {
        "api_key_storage": "keyring", "provider": "deepseek",
        "api_base": "https://api.deepseek.com/v1", "model": "deepseek-chat",
    }
    with patch("utils.ai_extractor._load_config", return_value=stored), patch(
        "utils.ai_extractor.load_api_key", side_effect=["", "legacy-key"]
    ), patch("utils.ai_extractor.save_api_key", return_value=True) as save, patch(
        "utils.ai_extractor.delete_api_key"
    ) as delete, patch("utils.ai_extractor._save_config") as save_config:
        cfg = get_api_config()

    assert cfg["api_key"] == "legacy-key"
    assert save.call_args.args == ("legacy-key", "deepseek")
    delete.assert_called_once_with()
    assert save_config.call_args.args[0]["api_key_provider_migration_done"] is True


def test_config_path_is_resolved_after_active_profile_changes(tmp_path):
    from utils import ai_extractor

    active = {"root": tmp_path / "profile-a"}
    seen_paths = []
    with patch.object(ai_extractor, "_CONFIG_PATH", None), patch.object(
        ai_extractor, "get_user_data_path",
        side_effect=lambda name: str(active["root"] / name),
    ), patch.object(ai_extractor, "migrate_legacy_json"), patch.object(
        ai_extractor, "read_json",
        side_effect=lambda path, default, validator: seen_paths.append(path) or {},
    ):
        ai_extractor.get_api_config()
        active["root"] = tmp_path / "profile-b"
        ai_extractor.get_api_config()

    assert seen_paths == [
        str(tmp_path / "profile-a" / "ai_config.json"),
        str(tmp_path / "profile-b" / "ai_config.json"),
    ]


def test_explicit_default_provider_and_model_are_persisted():
    from utils.ai_extractor import save_api_config

    existing = {
        "default_provider": "deepseek",
        "default_models": {"deepseek": "deepseek-chat"},
    }
    with patch("utils.ai_extractor._load_config", return_value=existing), patch(
        "utils.ai_extractor.save_api_key", return_value=True,
    ), patch("utils.ai_extractor._save_config") as save:
        save_api_config(
            "openai-key", "https://api.openai.com/v1", "gpt-5.6-luna",
            provider="openai", make_default=True,
        )

    persisted = save.call_args.args[0]
    assert persisted["provider"] == "openai"
    assert persisted["model"] == "gpt-5.6-luna"
    assert persisted["default_provider"] == "openai"
    assert persisted["default_models"] == {
        "deepseek": "deepseek-chat", "openai": "gpt-5.6-luna",
    }
    assert "api_key" not in persisted


def test_normal_save_preserves_explicit_defaults():
    from utils.ai_extractor import save_api_config

    existing = {
        "default_provider": "deepseek",
        "default_models": {"deepseek": "deepseek-v4-flash"},
    }
    with patch("utils.ai_extractor._load_config", return_value=existing), patch(
        "utils.ai_extractor.save_api_key", return_value=True,
    ), patch("utils.ai_extractor._save_config") as save:
        save_api_config(
            "openai-key", "https://api.openai.com/v1", "gpt-5.6-luna",
            provider="openai",
        )

    persisted = save.call_args.args[0]
    assert persisted["default_provider"] == "deepseek"
    assert persisted["default_models"] == {"deepseek": "deepseek-v4-flash"}
