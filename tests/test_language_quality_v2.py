"""Language Card Quality V2 schema, normalization, rendering, and guard gates."""

import json
from pathlib import Path
import pytest

from Language import LANG_CONFIG, LANG_GRAMMAR_CONFIG
from mode.card_render import build_afmt, build_qfmt
from mode.templates import LANG_GRAMMAR_TEMPLATES, LANG_TEMPLATES
from utils import prompt_config
from utils.ai_benchmark import (
    evaluate_quality_v2_card,
    summarize_quality_v2_cards,
    validate_quality_v2_corpus,
)
from utils.ai_output_validation import validate_ai_cards
from utils.import_quality import evaluate_card_candidate, find_confusion_candidates
from utils.model_lifecycle import ensure_model
from utils.usage_guide import normalize_language_card


ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_KEYS = (
    "semantic_group", "relationship_note", "register_nuance", "related_terms",
)
SEMANTIC_FIELDS = (
    "Semantic Group", "Relationship Note", "Register / Nuance", "Related Terms",
)


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


def test_all_language_schemas_support_example_3_and_4_with_vocab_samples():
    for kind, configs in (("vocab", LANG_CONFIG), ("grammar", LANG_GRAMMAR_CONFIG)):
        for language, cfg in configs.items():
            schema = json.loads(prompt_config.get_json_template(language, kind))
            for index in (3, 4):
                assert f"example_{index}" in schema
                assert f"example_{index}_vn" in schema
                if kind == "vocab":
                    assert schema[f"example_{index}"]
                    assert schema[f"example_{index}_vn"]
                else:
                    assert schema[f"example_{index}"] == ""
                    assert schema[f"example_{index}_vn"] == ""
                assert cfg["json_field_map"][f"example_{index}"] == f"Example{index}"
                assert f"Example{index}" in cfg["all_fields"]
                assert f"Example{index} Audio" in cfg["all_fields"]
                assert (f"Example{index} Audio", f"Example{index}") in cfg["audio_fields"]
            if language == "chinese":
                assert all(f"example_{index}_pinyin" in schema for index in (3, 4))
            if language == "korean":
                assert all(f"example_{index}_romanization" in schema for index in (3, 4))


def test_prompts_require_four_examples_and_grounded_usage_nuance_for_every_language():
    from utils.prompts import _GRAMMAR_SYSTEM_PROMPTS, _SYSTEM_PROMPTS

    for prompt in _SYSTEM_PROMPTS.values():
        assert "1–3 pattern" in prompt
        assert "0–3 micro-note" in prompt
        assert "0–3" in prompt and "collocation —" in prompt
        assert "example_3" in prompt and "example_4" in prompt
        assert "Bắt buộc đủ Ex1–Ex4" in prompt
        assert "sắc thái/mức độ dùng" in prompt
        assert "relationship_note" in prompt
    for prompt in _GRAMMAR_SYSTEM_PROMPTS.values():
        assert "Function → Form → Constraint → Contrast/Error → Variants" in prompt
        assert "Ex3/4" in prompt


def test_normalizer_serializes_up_to_three_unique_guide_items_and_keeps_old_shape():
    old = {
        "front": "depend", "usage_pattern": "depend on + N",
        "example": "It depends on timing.", "example_2": "Success depends on practice.",
    }
    assert normalize_language_card(old) == old

    normalized = normalize_language_card({
        "usage_pattern": ["depend on + N", "depend on sb to + V", "depend upon + N", "fourth"],
        "usage_note": "Constraint: often stative.\nConstraint: often stative.\nContrast: rely on stresses support.",
        "collocation": [
            "depend heavily on — phụ thuộc nhiều vào",
            "largely depend on — phần lớn phụ thuộc vào",
            "depend entirely on — hoàn toàn phụ thuộc vào",
            "extra — thừa",
        ],
    })
    assert normalized["usage_pattern"].count("\n") == 2
    assert normalized["usage_note"].splitlines() == [
        "Constraint: often stative.", "Contrast: rely on stresses support.",
    ]
    assert len(normalized["collocation"].splitlines()) == 3


def test_normalizer_removes_duplicate_and_orphan_optional_example_bundles():
    normalized = normalize_language_card({
        "example": "Canonical example.",
        "example_2": "Transfer example.",
        "example_3": "Canonical example.",
        "example_3_vn": "duplicate",
        "example_4": "",
        "example_4_vn": "orphan",
    })
    assert normalized["example_2"] == "Transfer example."
    assert all(not key.startswith("example_3") for key in normalized)
    assert all(not key.startswith("example_4") for key in normalized)


def test_example_3_and_4_render_directly_on_answers_without_comparison_labels():
    for language, cfg in LANG_CONFIG.items():
        front = build_qfmt(cfg, LANG_TEMPLATES[language], 0)
        back = build_afmt(cfg, LANG_TEMPLATES[language], 1)
        assert "{{Example3}}" not in front and "{{Example4}}" not in front
        assert "{{#Example3}}" in back and "{{#Example4}}" in back
        assert back.count("quality-v2-example") == 2
        assert "{{Example3 Audio}}" in back and "{{Example4 Audio}}" in back
        assert "<details" not in back
        assert "Đối chiếu" not in back
        assert "VÍ DỤ 3" in back and "VÍ DỤ 4" in back

    for language, cfg in LANG_GRAMMAR_CONFIG.items():
        back = build_afmt(cfg, LANG_GRAMMAR_TEMPLATES[language], 1)
        assert "{{#Example3}}" in back and "{{#Example4}}" in back


def test_vocab_import_contract_requires_all_four_examples_but_grammar_does_not():
    partial_vocab = {
        "front": "advice", "meaning": "lời khuyên", "example": "Ask for advice.",
        "example_2": "She gave advice.",
    }
    report = validate_ai_cards(
        [partial_vocab], lang="english", kind="vocab", require_example=True,
    )
    assert report.invalid[0].category == "missing_example_3"

    grammar = {
        "pattern": "used to + V", "meaning": "thói quen cũ",
        "usage": "S + used to + V", "example": "I used to walk home.",
    }
    assert validate_ai_cards(
        [grammar], lang="english", kind="grammar", require_example=True,
    ).valid_cards


def test_semantic_context_schema_migrates_and_renders_only_on_vocab_answers():
    for language, cfg in LANG_CONFIG.items():
        schema = json.loads(prompt_config.get_json_template(language, "vocab"))
        assert all(key in schema for key in SEMANTIC_KEYS)
        assert tuple(cfg["json_field_map"][key] for key in SEMANTIC_KEYS) == SEMANTIC_FIELDS
        assert all(field in cfg["all_fields"] for field in SEMANTIC_FIELDS)

        back = build_afmt(cfg, LANG_TEMPLATES[language], 1)
        for field, label in zip(SEMANTIC_FIELDS, (
            "Nhóm nghĩa", "Quan hệ / ghi chú", "Sắc thái / mức độ", "Từ liên quan",
        )):
            assert f"{{{{#{field}}}}}" in back
            assert label in back


def test_example_field_migration_is_additive_idempotent_and_keeps_card_count():
    for language, cfg in LANG_CONFIG.items():
        model = {
            "name": cfg["model_name"],
            "flds": [{"name": "Front"}, {"name": "Meaning"}],
            "tmpls": [{"name": "Legacy", "qfmt": "", "afmt": ""}],
            "css": "",
        }
        manager = _ModelManager(model)
        for _ in range(2):
            ensure_model(
                manager, cfg, LANG_TEMPLATES[language], ".card{}",
                build_qfmt, build_afmt,
                rename_primary_template=True, prune_extra_templates=False,
            )
        names = [field["name"] for field in model["flds"]]
        assert len(names) == len(set(names))
        assert all(field in names for field in ("Example3", "Example4"))
        assert len(model["tmpls"]) == len(LANG_TEMPLATES[language]) // 2

    for language, cfg in LANG_GRAMMAR_CONFIG.items():
        model = {
            "name": cfg["model_name"],
            "flds": [{"name": "Pattern"}, {"name": "Meaning"}],
            "tmpls": [{"name": "Legacy", "qfmt": "", "afmt": ""}],
            "css": "",
        }
        manager = _ModelManager(model)
        for _ in range(2):
            ensure_model(
                manager, cfg, LANG_GRAMMAR_TEMPLATES[language], ".card{}",
                build_qfmt, build_afmt,
                rename_primary_template=False, prune_extra_templates=True,
            )
        names = [field["name"] for field in model["flds"]]
        assert len(names) == len(set(names))
        assert all(field in names for field in ("Example3", "Example4"))
        assert len(model["tmpls"]) == len(LANG_GRAMMAR_TEMPLATES[language]) // 2


def test_confusion_guard_has_exact_positive_and_negative_fixtures_for_four_languages():
    fixtures = {
        "english": ("affect", ["effect"], ["effective"]),
        "japanese": ("気になる", ["気にする"], ["気づく"]),
        "chinese": ("了解", ["理解"], ["理想"]),
        "korean": ("늘다", ["늘리다"], ["느리다"]),
    }
    for language, (target, positive, negative) in fixtures.items():
        assert find_confusion_candidates(target, positive, lang=language) == tuple(positive)
        assert find_confusion_candidates(target, negative, lang=language) == ()

        result = evaluate_card_candidate(
            {"front": target, "meaning": "meaning", "example": f"context {target}"},
            lang=language, existing_terms=positive,
        )
        assert "confusion_candidate" in result["warnings"]
        assert result["confusion_candidates"] == tuple(positive)
        assert result["complete"] is True


def test_quality_v2_benchmark_covers_every_dimension_without_rewarding_quota():
    corpus = json.loads((ROOT / "benchmarks" / "language_quality_v2.json").read_text(encoding="utf-8"))
    validation = validate_quality_v2_corpus(corpus)
    assert validation["case_count"] == 24
    assert set(validation["coverage"]) == {"english", "japanese", "chinese", "korean"}

    two_example_card = {
        "front": "window", "meaning": "cửa sổ",
        "example": "Open the window.", "example_2": "Rain hit the window.",
    }
    rich_card = {
        **two_example_card,
        "usage_pattern": "pattern one\npattern two",
        "usage_note": "Constraint: one.\nContrast: two.",
        "collocation": "open a window — mở cửa sổ\nwindow frame — khung cửa sổ",
        "example_3": "The transfer window closes tomorrow.",
    }
    assert evaluate_quality_v2_card(two_example_card)["valid"] is True
    report = summarize_quality_v2_cards([two_example_card, rich_card])
    assert report["automated_valid_count"] == 2
    assert report["average_examples"] == 2.5
    assert report["over_generation_count"] == 0


def test_prompt_and_preview_boundaries_are_versioned_and_editable():
    from utils.ai_result_cache import DEFAULT_PROMPT_VERSION
    from utils.prompt_config import PROMPT_CONFIG_VERSION

    assert DEFAULT_PROMPT_VERSION >= 22
    assert PROMPT_CONFIG_VERSION >= 7
    preview_source = (ROOT / "ui" / "ai_preview.py").read_text(encoding="utf-8")
    for key in ("example_3", "example_3_vn", "example_4", "example_4_vn"):
        assert key in preview_source


@pytest.mark.skip(reason="large Batch production was removed")
def test_batch_cache_key_tracks_prompt_override_signature(monkeypatch):
    from utils import batch_processor

    words = [{"front": "window"}]
    monkeypatch.setattr(batch_processor, "get_signature", lambda: "before")
    before = batch_processor._batch_cache_key(words, "english", "", "deck")
    monkeypatch.setattr(batch_processor, "get_signature", lambda: "after")
    after = batch_processor._batch_cache_key(words, "english", "", "deck")
    assert before != after
