"""Reference-language policy shared by card generation and Reviewer AI."""

from __future__ import annotations

from collections.abc import MutableMapping

from .language_identity import normalize_language


REFERENCE_LANGUAGE_CONF_KEY = "bento_forge_reference_language_by_deck"
REFERENCE_LANGUAGE_CHOICES = ("ui", "target", "vi", "en", "ja", "zh", "ko")
_TARGET_CODES = {
    "japanese": "ja",
    "chinese": "zh",
    "korean": "ko",
    "english": "en",
}
_LANGUAGE_NAMES = {
    "vi": "Vietnamese",
    "en": "English",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
}


def normalize_reference_language(value, default="ui") -> str:
    """Return a stable stored choice while tolerating missing legacy state."""
    value = str(value or "").strip().lower()
    return value if value in REFERENCE_LANGUAGE_CHOICES else default


def resolve_reference_language(choice, target_language, ui_language="vi") -> str:
    """Resolve ``ui``/``target`` into one concrete output-language code."""
    choice = normalize_reference_language(choice)
    if choice == "ui":
        return "en" if str(ui_language or "").strip().lower() == "en" else "vi"
    if choice == "target":
        try:
            return _TARGET_CODES[normalize_language(target_language)]
        except (KeyError, ValueError):
            return "en"
    return choice


def reference_language_name(code) -> str:
    """Return the English name used in provider-neutral system prompts."""
    return _LANGUAGE_NAMES.get(str(code or "").strip().lower(), "English")


def get_reference_language(config, deck_id, default="ui") -> str:
    """Read a per-deck choice without mutating Anki collection config."""
    if deck_id is None or not isinstance(config, MutableMapping):
        return normalize_reference_language(default)
    stored = config.get(REFERENCE_LANGUAGE_CONF_KEY, {})
    if not isinstance(stored, dict):
        return normalize_reference_language(default)
    return normalize_reference_language(stored.get(str(deck_id)), default=default)


def set_reference_language(config, deck_id, choice) -> str:
    """Persist a per-deck choice; the legacy-compatible ``ui`` default is sparse."""
    if deck_id is None or not isinstance(config, MutableMapping):
        return normalize_reference_language(choice)
    choice = normalize_reference_language(choice)
    stored = config.get(REFERENCE_LANGUAGE_CONF_KEY, {})
    stored = dict(stored) if isinstance(stored, dict) else {}
    if choice == "ui":
        stored.pop(str(deck_id), None)
    else:
        stored[str(deck_id)] = choice
    if stored:
        config[REFERENCE_LANGUAGE_CONF_KEY] = stored
    else:
        config.pop(REFERENCE_LANGUAGE_CONF_KEY, None)
    return choice


def apply_reference_language_instruction(system_prompt, reference_language) -> str:
    """Make learner-facing output language explicit without changing JSON keys."""
    code = resolve_reference_language(reference_language, "english", "en")
    language = reference_language_name(code)
    instruction = (
        "REFERENCE LANGUAGE (mandatory): Write every learner-facing explanatory "
        f"value in {language}: meaning, topic labels, usage/explanation notes, "
        "collocation glosses, relationship/register notes, and all example "
        "translations. Keep the target expression, target-language examples, "
        "readings/romanization/IPA, level codes, and JSON keys in their required "
        "forms. The legacy key example_vn means example translation; it does not "
        "require Vietnamese. Prefer natural definitions over circular paraphrases."
    )
    return f"{str(system_prompt or '').rstrip()}\n\n{instruction}"


__all__ = [
    "REFERENCE_LANGUAGE_CONF_KEY",
    "REFERENCE_LANGUAGE_CHOICES",
    "apply_reference_language_instruction",
    "get_reference_language",
    "normalize_reference_language",
    "reference_language_name",
    "resolve_reference_language",
    "set_reference_language",
]
