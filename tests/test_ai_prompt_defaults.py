"""Regression tests for the isolated built-in prompt owner."""

import ast
from pathlib import Path

from utils import ai_extractor
from utils import ai_prompt_defaults as defaults
from utils import prompt_config
from utils.prompts import chinese, english, japanese, korean


LANGS = {"japanese", "chinese", "korean", "english"}


def _imports(module) -> set:
    source = Path(module.__file__).read_text(encoding="utf-8")
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module)
            else:
                found.update(alias.name for alias in node.names)
    return found


def test_prompt_defaults_are_a_small_facade_over_pure_language_data():
    assert _imports(defaults) == {"prompts"}
    assert len(Path(defaults.__file__).read_text(encoding="utf-8").splitlines()) < 500
    assert all(_imports(module) == set() for module in (japanese, chinese, korean, english))


def test_each_language_module_owns_its_vocab_and_grammar_defaults():
    expected = {
        "japanese": (japanese, "JAPANESE"),
        "chinese": (chinese, "CHINESE"),
        "korean": (korean, "KOREAN"),
        "english": (english, "ENGLISH"),
    }

    for lang, (module, prefix) in expected.items():
        assert getattr(module, f"_{prefix}_SYSTEM_PROMPT") is defaults._SYSTEM_PROMPTS[lang]
        assert getattr(module, f"_{prefix}_JSON_TEMPLATE") is defaults._JSON_TEMPLATES[lang]
        assert getattr(module, f"_{prefix}_GRAMMAR_SYSTEM_PROMPT") is defaults._GRAMMAR_SYSTEM_PROMPTS[lang]
        assert getattr(module, f"_{prefix}_GRAMMAR_JSON_TEMPLATE") is defaults._GRAMMAR_JSON_TEMPLATES[lang]


def test_prompt_config_depends_on_defaults_not_ai_extractor():
    imports = _imports(prompt_config)
    assert "ai_prompt_defaults" in imports
    assert "ai_extractor" not in imports


def test_all_prompt_registries_cover_supported_languages():
    registries = (
        defaults._SYSTEM_PROMPTS,
        defaults._JSON_TEMPLATES,
        defaults._SYSTEM_PROMPTS_EN,
        defaults._JSON_TEMPLATES_EN,
        defaults._GRAMMAR_SYSTEM_PROMPTS,
        defaults._GRAMMAR_JSON_TEMPLATES,
        defaults._GRAMMAR_SYSTEM_PROMPTS_EN,
        defaults._GRAMMAR_JSON_TEMPLATES_EN,
    )
    assert all(set(registry) == LANGS for registry in registries)


def test_ai_extractor_reexports_legacy_prompt_symbols_by_identity():
    for name in defaults.__all__:
        assert getattr(ai_extractor, name) is getattr(defaults, name)
