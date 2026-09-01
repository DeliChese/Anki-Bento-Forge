"""Regression contract for the standalone Collocation/Idiom Language subtype."""

import json


LANGS = {"japanese", "chinese", "korean", "english"}


def _card(lang):
    level_key, level = {
        "japanese": ("jlptlevel", "N3"),
        "chinese": ("hsk_level", "HSK3"),
        "korean": ("topik_level", "TOPIK II"),
        "english": ("cefr_level", "B1"),
    }[lang]
    card = {
        "chunk": {
            "japanese": "約束を守る", "chinese": "做出决定",
            "korean": "약속을 지키다", "english": "make a decision",
        }[lang],
        "meaning": "nghĩa theo ngữ cảnh",
        "phrase_type": "collocation",
        "pattern_slots": "phần cố định + khe thay thế",
        "register_nuance": "trung tính",
        "constraint": "không thay tùy ý động từ chính",
        "source_word": "",
        "related_terms": "",
        level_key: level,
        "topic": "daily life",
    }
    for index in range(1, 5):
        suffix = "" if index == 1 else f"_{index}"
        card[f"example{suffix}"] = f"Ví dụ đích {index}: {card['chunk']}"
        card[f"example{suffix}_vn"] = f"Bản dịch {index}"
    return card


def test_collocation_has_four_separate_language_note_types():
    from Language import LANG_COLLOCATION_CONFIG, LANG_CONFIG, LANG_GRAMMAR_CONFIG

    assert set(LANG_COLLOCATION_CONFIG) == LANGS
    for lang, cfg in LANG_COLLOCATION_CONFIG.items():
        assert "Collocation V18.3" in cfg["model_name"]
        assert cfg["model_name"] not in {
            LANG_CONFIG[lang]["model_name"], LANG_GRAMMAR_CONFIG[lang]["model_name"],
        }
        assert cfg["detect_key"] == "chunk"
        assert len(cfg["template_names"]) == 2
        assert all(field in cfg["all_fields"] for field in (
            "Phrase Type", "Pattern / Slots", "Constraint", "Source Word",
        ))
        assert cfg["json_field_map"]["chunk"] == "Front"


def test_collocation_prompts_are_source_grounded_and_schema_valid():
    from utils import prompt_config

    for lang in LANGS:
        schema = json.loads(prompt_config.get_json_template(lang, "collocation"))
        prompt = prompt_config.get_system_prompt(lang, "collocation")
        assert all(key in schema for key in (
            "chunk", "meaning", "phrase_type", "pattern_slots",
            "register_nuance", "constraint", "source_word",
            "example", "example_2", "example_3", "example_4",
        ))
        assert "không bịa" in prompt
        ok, error, _ = prompt_config.validate_json_template(
            json.dumps(schema, ensure_ascii=False), lang=lang, kind="collocation",
        )
        assert ok, error


def test_collocation_validation_requires_type_and_four_contexts():
    from utils.ai_output_validation import validate_ai_cards

    for lang in LANGS:
        valid = validate_ai_cards(
            [_card(lang)], lang=lang, kind="collocation", require_example=True,
        )
        assert len(valid.valid_cards) == 1

        missing = _card(lang)
        missing.pop("example_4")
        report = validate_ai_cards(
            [missing], lang=lang, kind="collocation", require_example=True,
        )
        assert report.invalid[0].category == "missing_example_4"

        wrong_type = _card(lang)
        wrong_type["phrase_type"] = "word"
        report = validate_ai_cards([wrong_type], lang=lang, kind="collocation")
        assert report.invalid[0].category == "invalid_phrase_type"


def test_collocation_templates_are_two_deliberate_directions():
    from Language import LANG_COLLOCATION_CONFIG
    from mode import LANG_COLLOCATION_TEMPLATES
    from utils.model_lifecycle import collect_template_fields

    assert set(LANG_COLLOCATION_TEMPLATES) == LANGS
    for lang, templates in LANG_COLLOCATION_TEMPLATES.items():
        assert len(templates) == 4
        rendered = "\n".join(template() for template in templates)
        assert "{{Front}}" in rendered
        assert "{{Meaning}}" in rendered
        assert "{{Pattern / Slots}}" in rendered
        assert "{{Constraint}}" in rendered
        assert collect_template_fields(templates) <= set(LANG_COLLOCATION_CONFIG[lang]["all_fields"])


def test_collocation_draft_state_is_isolated_from_vocab_and_grammar(tmp_path):
    from utils.factory_state import FactoryStateStore

    store = FactoryStateStore(
        legacy_path=str(tmp_path / "legacy.json"),
        path=str(tmp_path / "state.json"),
    )
    state = {"language": {"english": {
        "vocab": {"text": "word"},
        "grammar": {"text": "rule"},
        "collocation": {"text": "make a decision"},
    }}}
    clean = store.sanitize(state)
    assert clean["language"]["english"]["vocab"]["text"] == "word"
    assert clean["language"]["english"]["grammar"]["text"] == "rule"
    assert clean["language"]["english"]["collocation"]["text"] == "make a decision"
