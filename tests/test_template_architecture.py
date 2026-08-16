"""Regression gates for the language-scoped card-template architecture."""

from pathlib import Path

import mode.templates as templates
from mode.templates import chinese, english, japanese, korean


def _template_functions(module, prefix):
    return {
        name: value
        for name, value in vars(module).items()
        if name.startswith(prefix) and callable(value)
    }


def test_templates_are_a_package_with_a_small_compatibility_facade():
    package_root = Path(templates.__file__)

    assert package_root.name == "__init__.py"
    assert package_root.parent.name == "templates"
    assert not package_root.parent.with_suffix(".py").exists()
    assert len(package_root.read_text(encoding="utf-8").splitlines()) < 500


def test_each_supported_language_owns_its_template_functions():
    expected_counts = {"tmpl_ja_": 16, "tmpl_zh_": 16, "tmpl_ko_": 14, "tmpl_en_": 14}

    for module, (prefix, expected_count) in zip(
        (japanese, chinese, korean, english), expected_counts.items()
    ):
        functions = _template_functions(module, prefix)
        assert len(functions) == expected_count
        assert all(callable(template) and template() for template in functions.values())


def test_registry_preserves_all_language_template_contracts():
    for language in ("japanese", "chinese", "korean", "english"):
        vocab_templates = templates.LANG_TEMPLATES[language]
        grammar_templates = templates.LANG_GRAMMAR_TEMPLATES[language]

        assert len(vocab_templates) == 10
        assert len(grammar_templates) == 4
        assert all("{{#SRS Independent}}" in template() for template in vocab_templates[2:])
        assert all(template() for template in (*vocab_templates, *grammar_templates))
