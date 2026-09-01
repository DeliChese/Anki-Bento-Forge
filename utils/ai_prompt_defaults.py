"""Compatibility facade for built-in AI prompt and JSON-schema defaults.

Language-specific prompt data lives in :mod:`utils.prompts`; runtime overrides
remain owned by :mod:`utils.prompt_config`.
"""

from .prompts import (
    _CHINESE_JSON_TEMPLATE,
    _CHINESE_SYSTEM_PROMPT,
    _JAPANESE_JSON_TEMPLATE,
    _JAPANESE_SYSTEM_PROMPT,
    _KOREAN_JSON_TEMPLATE,
    _KOREAN_SYSTEM_PROMPT,
    _ENGLISH_JSON_TEMPLATE,
    _ENGLISH_SYSTEM_PROMPT,
    _JAPANESE_JSON_TEMPLATE_EN,
    _JAPANESE_SYSTEM_PROMPT_EN,
    _CHINESE_JSON_TEMPLATE_EN,
    _CHINESE_SYSTEM_PROMPT_EN,
    _KOREAN_JSON_TEMPLATE_EN,
    _KOREAN_SYSTEM_PROMPT_EN,
    _ENGLISH_JSON_TEMPLATE_EN,
    _ENGLISH_SYSTEM_PROMPT_EN,
    _SYSTEM_PROMPTS,
    _JSON_TEMPLATES,
    _SYSTEM_PROMPTS_EN,
    _JSON_TEMPLATES_EN,
    _JAPANESE_GRAMMAR_JSON_TEMPLATE,
    _JAPANESE_GRAMMAR_SYSTEM_PROMPT,
    _CHINESE_GRAMMAR_JSON_TEMPLATE,
    _CHINESE_GRAMMAR_SYSTEM_PROMPT,
    _KOREAN_GRAMMAR_JSON_TEMPLATE,
    _KOREAN_GRAMMAR_SYSTEM_PROMPT,
    _ENGLISH_GRAMMAR_JSON_TEMPLATE,
    _ENGLISH_GRAMMAR_SYSTEM_PROMPT,
    _JAPANESE_GRAMMAR_JSON_TEMPLATE_EN,
    _JAPANESE_GRAMMAR_SYSTEM_PROMPT_EN,
    _CHINESE_GRAMMAR_JSON_TEMPLATE_EN,
    _CHINESE_GRAMMAR_SYSTEM_PROMPT_EN,
    _KOREAN_GRAMMAR_JSON_TEMPLATE_EN,
    _KOREAN_GRAMMAR_SYSTEM_PROMPT_EN,
    _ENGLISH_GRAMMAR_JSON_TEMPLATE_EN,
    _ENGLISH_GRAMMAR_SYSTEM_PROMPT_EN,
    _GRAMMAR_SYSTEM_PROMPTS,
    _GRAMMAR_JSON_TEMPLATES,
    _GRAMMAR_SYSTEM_PROMPTS_EN,
    _GRAMMAR_JSON_TEMPLATES_EN,
    _COLLOCATION_JSON_TEMPLATES,
    _COLLOCATION_SYSTEM_PROMPTS,
    _COLLOCATION_JSON_TEMPLATES_EN,
    _COLLOCATION_SYSTEM_PROMPTS_EN,
)

# Knowledge is intentionally independent from the language prompt registry:
# it has no language selector, pronunciation, or audio fields.
_KNOWLEDGE_JSON_TEMPLATE = """[
  {
    "type": "basic",
    "question": "...",
    "answer": "...",
    "explanation": "...",
    "source": "...",
    "tags": ["..."],
    "cloze_text": ""
  }
]"""

_KNOWLEDGE_SYSTEM_PROMPT = """You create study cards from the user's supplied material.
Return only a JSON array matching this schema exactly:
{{KNOWLEDGE_JSON_TEMPLATE}}

Rules:
- Use type "basic" only when question and answer are both present.
- Use type "cloze" only when cloze_text contains valid Anki cloze syntax such as {{c1::answer}}.
- Preserve a source only when it is explicitly supplied in the input. Never invent, infer, or fabricate a citation; otherwise use an empty string.
- Do not include pronunciation, audio, language-learning fields, Markdown fences, commentary, or extra keys.""".replace(
    "{{KNOWLEDGE_JSON_TEMPLATE}}", _KNOWLEDGE_JSON_TEMPLATE
)

# Separate cache boundary for the future Knowledge extraction workflow.  It does
# not invalidate V17 Language caches when this Knowledge-only prompt changes.
KNOWLEDGE_PROMPT_VERSION = 1


__all__ = [name for name in globals() if name.startswith("_") and not name.startswith("__")]
