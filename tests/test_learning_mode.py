"""V18-01 contract tests: deck defaults and legacy draft-state readability."""

from utils.factory_state import FactoryStateStore
from utils.learning_mode import (
    DEFAULT_LEARNING_MODE,
    LEARNING_MODE_CONFIG_KEY,
    LEARNING_MODE_REGISTRY,
    get_learning_mode,
    is_learning_mode_available,
    set_learning_mode,
)
from utils.i18n import t


def test_learning_mode_registry_keeps_language_subtypes_under_language():
    assert set(LEARNING_MODE_REGISTRY) == {"language", "knowledge"}
    assert LEARNING_MODE_REGISTRY["language"].kinds == ("vocab", "grammar", "collocation")
    assert LEARNING_MODE_REGISTRY["knowledge"].uses_language is False


def test_learning_mode_defaults_to_language_and_persists_per_deck():
    conf = {}

    assert get_learning_mode(conf, 10) == DEFAULT_LEARNING_MODE
    assert set_learning_mode(conf, "knowledge", 10) == "knowledge"
    assert get_learning_mode(conf, 10) == "knowledge"
    assert get_learning_mode(conf, 20) == DEFAULT_LEARNING_MODE
    assert conf[LEARNING_MODE_CONFIG_KEY] == {"10": "knowledge"}


def test_knowledge_beta_is_retained_but_not_available_in_the_ui():
    assert get_learning_mode({LEARNING_MODE_CONFIG_KEY: {"10": "knowledge"}}, 10) == "knowledge"
    assert is_learning_mode_available("language") is True
    assert is_learning_mode_available("knowledge") is False


def test_learning_mode_invalid_or_legacy_config_preserves_language_default():
    assert get_learning_mode({}, 10) == "language"
    assert get_learning_mode({LEARNING_MODE_CONFIG_KEY: {"10": "unknown"}}, 10) == "language"
    conf = {}
    assert set_learning_mode(conf, "unknown", 10) == "language"
    assert conf[LEARNING_MODE_CONFIG_KEY] == {"10": "language"}


def test_knowledge_ai_action_is_an_explicit_send_and_generate_cards_action():
    assert "GỬI" in t("knowledge_generate_btn", "vi")
    assert "Knowledge" in t("knowledge_generate_tip", "en")
    assert "Yêu cầu" in t("knowledge_instruction_label", "vi")


def test_factory_state_reads_legacy_language_namespace_and_saves_explicit_mode(tmp_path):
    legacy = tmp_path / "legacy.json"
    target = tmp_path / "factory_state.json"
    legacy.write_text(
        '{"japanese": {"vocab": {"text": "draft"}}}', encoding="utf-8"
    )
    store = FactoryStateStore(legacy_path=str(legacy), path=str(target))

    state = store.load()
    assert state["language"]["japanese"]["vocab"]["text"] == "draft"
    assert "japanese" not in state

    saved = store.save(state)
    assert saved["language"]["japanese"]["vocab"]["text"] == "draft"
    assert "japanese" not in saved
