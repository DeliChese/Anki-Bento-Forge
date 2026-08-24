"""
Unit tests for utils/i18n.py — translation system.
"""

import ast
import string
import sys
import os
from pathlib import Path
import pytest

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

from utils.i18n import (
    t, set_language, get_language, toggle_language, SUPPORTED_LANGUAGES,
    add_language_listener, remove_language_listener, study_mode_labels,
)


@pytest.fixture(autouse=True)
def isolated_language_config(tmp_path, monkeypatch):
    """Language changes must never touch a real profile or add-on file in tests."""
    import utils.i18n as i18n

    monkeypatch.setattr(i18n, "_CONFIG_PATH", str(tmp_path / "i18n_config.json"))
    i18n._current_lang = "vi"


class TestI18nBasics:
    """Basic translation tests."""

    def test_supported_languages(self):
        assert "vi" in SUPPORTED_LANGUAGES
        assert "en" in SUPPORTED_LANGUAGES

    def test_default_language_is_vi(self):
        set_language("vi")
        assert get_language() == "vi"

    def test_vi_translation(self):
        set_language("vi")
        assert isinstance(t("ai_extract_btn"), str)
        assert t("ai_extract_btn").strip()

    def test_en_translation(self):
        set_language("en")
        assert isinstance(t("ai_extract_btn"), str)
        assert t("ai_extract_btn").strip()

    def test_fallback_to_vi(self):
        """A translated UI key remains available in the selected language."""
        set_language("en")
        result = t("app_title", lang="en")
        assert isinstance(result, str)
        assert result.strip()

    def test_missing_key_returns_key(self):
        result = t("nonexistent_key_xyz")
        assert result == "nonexistent_key_xyz"

    def test_format_string(self):
        set_language("vi")
        result = t("filter_raw_count", count=5)
        assert "5" in result

    def test_format_string_en(self):
        set_language("en")
        result = t("filter_raw_count", count=10)
        assert "10" in result


class TestI18nPersistence:
    """Tests for language persistence."""

    def test_set_and_get(self):
        set_language("vi")
        assert get_language() == "vi"
        set_language("en")
        assert get_language() == "en"

    def test_invalid_language_raises(self):
        try:
            set_language("fr")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_explicit_lang_param(self):
        """Test that explicit lang parameter overrides global."""
        set_language("vi")
        assert t("ai_extract_btn", lang="en") != t("ai_extract_btn", lang="vi")
        assert get_language() == "vi"  # Global unchanged


class TestI18nLiveSwitch:
    """Tests for the smooth VI/EN toggle + live refresh listeners."""

    def test_toggle_language_cycles_vi_en(self):
        set_language("vi")
        assert get_language() == "vi"
        assert toggle_language() == "en"
        assert get_language() == "en"
        assert toggle_language() == "vi"
        assert get_language() == "vi"

    def test_language_listener_notified(self):
        calls = []
        def cb():
            calls.append(get_language())
        add_language_listener(cb)
        try:
            set_language("vi")
            set_language("en")
            assert calls == ["vi", "en"]
        finally:
            remove_language_listener(cb)

    def test_remove_language_listener_stops_notifications(self):
        calls = []
        def cb():
            calls.append(1)
        add_language_listener(cb)
        remove_language_listener(cb)
        set_language("vi")
        assert calls == []

    def test_toggle_is_persisted(self):
        set_language("vi")
        toggle_language()  # → en
        assert get_language() == "en"

    def test_english_study_modes_do_not_fall_back_to_japanese(self):
        set_language("vi")
        labels = study_mode_labels("english")
        assert labels["qa"] == "1. Anh→Việt"
        assert labels["pron"] == "4. IPA"

        set_language("en")
        assert study_mode_labels("english")["qa"] == "1. English→English"


class TestI18nAllKeys:
    """Verify all keys have both vi and en translations."""

    def test_all_keys_present(self):
        """Dynamically verify all keys exist in both languages."""
        from utils.i18n import _TRANSLATIONS
        missing = []
        for key, entry in _TRANSLATIONS.items():
            if "vi" not in entry:
                missing.append(f"{key}: missing vi")
            if "en" not in entry:
                missing.append(f"{key}: missing en")
        assert not missing, f"Missing translations: {missing}"

    def test_keys_are_strings(self):
        from utils.i18n import _TRANSLATIONS
        for key, entry in _TRANSLATIONS.items():
            assert isinstance(entry.get("vi", ""), str), f"{key}: vi not str"
            assert isinstance(entry.get("en", ""), str), f"{key}: en not str"

    def test_non_empty_translations(self):
        from utils.i18n import _TRANSLATIONS
        empty = []
        for key, entry in _TRANSLATIONS.items():
            if not entry.get("vi", "").strip():
                empty.append(f"{key}: empty vi")
            if not entry.get("en", "").strip():
                empty.append(f"{key}: empty en")
        assert not empty, f"Empty translations: {empty}"

    def test_vi_en_format_placeholders_match(self):
        """Switching languages must not break ``str.format`` call sites."""
        from utils.i18n import _TRANSLATIONS

        formatter = string.Formatter()

        def fields(text):
            return {
                field.split(".")[0].split("[")[0]
                for _, field, _, _ in formatter.parse(text)
                if field
            }

        mismatched = {
            key: (fields(entry["vi"]), fields(entry["en"]))
            for key, entry in _TRANSLATIONS.items()
            if fields(entry["vi"]) != fields(entry["en"])
        }
        assert not mismatched, f"Placeholder mismatch: {mismatched}"

        reserved = {
            key: fields(entry["vi"]) & {"key", "lang"}
            for key, entry in _TRANSLATIONS.items()
            if fields(entry["vi"]) & {"key", "lang"}
        }
        assert not reserved, f"Placeholders collide with t() parameters: {reserved}"

    def test_every_static_t_call_has_a_catalog_entry(self):
        """Catch a new ``t('key')`` call before it falls back to the raw key."""
        from utils.i18n import _TRANSLATIONS

        missing = []
        for path in _addon_python_files():
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "t"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    continue
                key = node.args[0].value
                if key not in _TRANSLATIONS:
                    missing.append(f"{path.relative_to(Path(_addon_root))}:{node.lineno}: {key}")

        assert not missing, "Missing i18n keys:\n" + "\n".join(missing)


def _addon_python_files():
    root = Path(_addon_root)
    for path in root.rglob("*.py"):
        if "tests" in path.parts or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        yield path
