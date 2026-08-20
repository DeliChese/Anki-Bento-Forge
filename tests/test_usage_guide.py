"""P1-05 Usage Guide V1 contract, migration, and output regressions."""

import json
from pathlib import Path

from Language import LANG_CONFIG
from mode.card_render import build_afmt, build_qfmt
from mode.templates import LANG_TEMPLATES
from utils.ai_output_repairs import repair_vocabulary_cards
from utils.model_lifecycle import ensure_model
from utils.usage_guide import evaluate_usage_guide_card, normalize_usage_guide_card


ROOT = Path(__file__).resolve().parents[1]
GUIDE_FIELDS = ("Usage Pattern", "Usage Note", "Collocation")
GUIDE_KEYS = ("usage_pattern", "usage_note", "collocation")


class _ModelManager:
    def __init__(self, model):
        self.model = model

    def by_name(self, name):
        return self.model if self.model["name"] == name else None

    def save(self, _model):
        return None

    @staticmethod
    def new_field(name):
        return {"name": name}

    @staticmethod
    def add_field(model, field):
        model["flds"].append(field)

    @staticmethod
    def new_template(name):
        return {"name": name, "qfmt": "", "afmt": ""}

    @staticmethod
    def add_template(model, template):
        model["tmpls"].append(template)

    @staticmethod
    def remove_template(model, template):
        model["tmpls"].remove(template)


def test_reference_corpus_has_five_reviewed_valid_cards_per_language():
    corpus = json.loads((ROOT / "benchmarks" / "usage_guide_v1.json").read_text(encoding="utf-8"))
    cards = corpus["cards"]

    assert corpus["rubric"]["threshold_percent"] == 90
    assert len(cards) == 20
    for language in LANG_CONFIG:
        language_cards = [card for card in cards if card["language"] == language]
        assert len(language_cards) == 5
        assert all(evaluate_usage_guide_card(card)["valid"] for card in language_cards)


def test_runnable_language_cases_match_the_usage_reference_corpus():
    from utils.ai_benchmark import validate_case

    corpus = json.loads((ROOT / "benchmarks" / "usage_guide_v1.json").read_text(encoding="utf-8"))
    for language in LANG_CONFIG:
        case_path = ROOT / "benchmarks" / f"usage_guide_{language}_5_v1.json"
        raw_case = json.loads(case_path.read_text(encoding="utf-8"))
        case = validate_case(raw_case)
        reference_terms = [card["front"] for card in corpus["cards"] if card["language"] == language]

        assert case["language"] == language
        assert case["expected_terms"] == reference_terms
        assert [item["front"] for item in raw_case["source_items"]] == reference_terms
        assert all(item.get("meaning") for item in raw_case["source_items"])


def test_reviewed_usage_gate_covers_the_corpus_and_passes_conservatively():
    corpus = json.loads((ROOT / "benchmarks" / "usage_guide_v1.json").read_text(encoding="utf-8"))
    review = json.loads((ROOT / "benchmarks" / "usage_guide_review_v1.json").read_text(encoding="utf-8"))
    expected = {(card["language"], card["front"]) for card in corpus["cards"]}
    reviewed = {(item["language"], item["front"]) for item in review["items"]}

    assert reviewed == expected
    assert review["total_items"] == len(expected) == 20
    assert review["passed_items"] == sum(item["passed"] for item in review["items"]) == 19
    assert review["pass_rate"] == 0.95
    assert review["pass_rate"] >= review["required_pass_rate"]
    assert review["final_cost_usd"] <= 0.005
    assert review["final_seconds_per_card"] <= 3
    assert review["gate_passed"] is True


def test_all_vocab_schemas_map_the_three_usage_guide_fields():
    from utils import prompt_config

    for language, cfg in LANG_CONFIG.items():
        template = json.loads(prompt_config.get_json_template(language, "vocab"))
        assert all(key in template for key in GUIDE_KEYS)
        assert all(field in cfg["all_fields"] for field in GUIDE_FIELDS)
        assert tuple(cfg["json_field_map"][key] for key in GUIDE_KEYS) == GUIDE_FIELDS


def test_usage_prompts_keep_language_specific_failure_boundaries():
    from utils.prompts import _SYSTEM_PROMPTS

    assert "觉得 không dùng trang trọng" in _SYSTEM_PROMPTS["chinese"]
    assert "KHÔNG 질문을 묻다" in _SYSTEM_PROMPTS["korean"]
    assert "N께 N을/를 드리다" in _SYSTEM_PROMPTS["korean"]
    assert "không lặp frame" in _SYSTEM_PROMPTS["english"]
    assert "genuinely interested" in _SYSTEM_PROMPTS["english"]
    assert "/ˈɡrɑːntɪd/" in _SYSTEM_PROMPTS["english"]
    assert "KHÔNG phải collocation" in _SYSTEM_PROMPTS["english"]


def test_normalizer_omits_empty_invalid_repeated_content_and_duplicate_example():
    original = {
        "front": "depend",
        "usage_pattern": "  depend on + N  ",
        "usage_note": "N/A",
        "collocation": ["depend heavily on — phụ thuộc nhiều vào", "second — hai"],
        "example": "It depends on timing.",
        "example_2": " It depends on timing. ",
        "example_2_vn": "Điều đó phụ thuộc thời điểm.",
    }

    normalized = normalize_usage_guide_card(original)

    assert original["usage_pattern"].startswith("  ")
    assert normalized["usage_pattern"] == "depend on + N"
    assert "usage_note" not in normalized
    assert normalized["collocation"].splitlines() == [
        "depend heavily on — phụ thuộc nhiều vào", "second — hai",
    ]
    assert "example_2" not in normalized and "example_2_vn" not in normalized


def test_normalizer_drops_collocation_without_a_meaning_and_repairs_every_language():
    for language in LANG_CONFIG:
        cards = repair_vocabulary_cards([{
            "front": "word", "collocation": "phrase only", "usage_note": "  useful note  "
        }], language)
        assert cards == [{"front": "word", "usage_note": "useful note"}]


def test_normalizer_accepts_an_explicitly_empty_optional_collocation():
    card = {"front": "take for granted", "collocation": ""}

    assert normalize_usage_guide_card(card) == {"front": "take for granted"}


def test_normalizer_drops_only_a_generic_note_that_repeats_the_pattern_preposition():
    generic = normalize_usage_guide_card({
        "usage_pattern": "depend on + something",
        "usage_note": "Thường dùng với giới từ 'on'.",
    })
    useful = normalize_usage_guide_card({
        "usage_pattern": "be interested in + something",
        "usage_note": "Interested mô tả người; interesting mô tả sự vật.",
    })

    assert "usage_note" not in generic
    assert useful["usage_note"].startswith("Interested")


def test_normalizer_drops_a_collocation_phrase_already_embedded_in_pattern():
    normalized = normalize_usage_guide_card({
        "usage_pattern": "Nと約束する／約束を守る",
        "collocation": "約束を守る — giữ lời hứa",
    })

    assert "collocation" not in normalized


def test_usage_guide_is_on_answer_side_only_for_all_default_vocab_templates():
    for language, cfg in LANG_CONFIG.items():
        templates = LANG_TEMPLATES[language]
        front = build_qfmt(cfg, templates, 0)
        back = build_afmt(cfg, templates, 1)
        for field in GUIDE_FIELDS:
            assert f"{{{{{field}}}}}" not in front
            assert f"{{{{#{field}}}}}" in back
            assert f"{{{{{field}}}}}" in back


def test_usage_guide_model_migration_is_idempotent_and_keeps_template_count():
    for language, cfg in LANG_CONFIG.items():
        templates = LANG_TEMPLATES[language]
        model = {
            "name": cfg["model_name"],
            "flds": [{"name": "Front"}, {"name": "Meaning"}],
            "tmpls": [{"name": "Legacy", "qfmt": "", "afmt": ""}],
            "css": "",
        }
        manager = _ModelManager(model)

        for _ in range(2):
            ensure_model(
                manager, cfg, templates, ".card{}", build_qfmt, build_afmt,
                rename_primary_template=True, prune_extra_templates=False,
            )

        field_names = [field["name"] for field in model["flds"]]
        assert len(field_names) == len(set(field_names))
        assert all(field in field_names for field in GUIDE_FIELDS)
        assert len(model["tmpls"]) == len(templates) // 2
