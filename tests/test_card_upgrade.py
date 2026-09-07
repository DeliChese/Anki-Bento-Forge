from utils.card_upgrade import (
    CURRENT_QUALITY_VERSION, QUALITY_FIELD, apply_card_upgrade, build_upgrade_source,
    detect_note_field, proposed_field_changes, select_upgrade_candidate,
    upgrade_is_available,
)


def test_upgrade_dialog_has_visible_result_area_and_pyqt6_check_states():
    from pathlib import Path

    source = (Path(__file__).parents[1] / "ui" / "card_upgrade_dialog.py").read_text(
        encoding="utf-8"
    )
    assert 't("card_upgrade_result_empty")' in source
    assert "Qt.CheckState.Checked" in source
    assert "name.setCheckState(2" not in source
    assert "dialog.raise_()" in source
    assert "dialog.activateWindow()" in source
    assert "def _apply_upgrade_with_current_template(" in source
    assert "ensure_model(" in source
    assert 'sync_cfg["model_name"] = str(note_type' in source
    assert "prune_extra_templates=False" in source


def _snapshot(**extra):
    data = {
        "language": "english", "card_kind": "vocabulary", "note_type": "AnkiTool English V18.3 (Add-on)",
        "current_target": "affect", "meaning": "ảnh hưởng", "note_id": 9,
    }
    data.update(extra)
    return data


def test_upgrade_only_targets_outdated_managed_language_notes():
    assert upgrade_is_available(_snapshot()) is True
    assert upgrade_is_available(_snapshot(
        note_type="Mẫu Từ Vựng Tiếng Nhật V14.0 (Add-on)", language="japanese",
    )) is True
    assert upgrade_is_available(_snapshot(quality_version=CURRENT_QUALITY_VERSION)) is False
    assert upgrade_is_available(_snapshot(note_type="My English Notes")) is False


def test_current_chinese_vocab_can_upgrade_when_radical_map_is_missing():
    chinese = _snapshot(
        language="chinese", current_target="学习", card_kind="vocabulary",
        note_type="AnkiTool Chinese V18.3 (Add-on)",
        quality_version=CURRENT_QUALITY_VERSION,
    )
    assert upgrade_is_available(chinese) is True
    assert upgrade_is_available({
        **chinese,
        "radical_mindmap": '{"characters":[{"character":"学"}]}',
    }) is False


def test_upgrade_candidate_must_keep_current_identity():
    card = select_upgrade_candidate([{"front": "affect", "meaning": "tác động"}], _snapshot())
    assert card["front"] == "affect"
    try:
        select_upgrade_candidate([{"front": "effect"}], _snapshot())
    except ValueError as error:
        assert str(error) == "card_upgrade_identity_mismatch"
    else:
        raise AssertionError("unexpected different target accepted")


def test_chinese_upgrade_accepts_prompt_native_simplified_identity():
    snapshot = _snapshot(
        language="chinese", card_kind="vocabulary", current_target="谁",
        note_type="AnkiTool Chinese V18.3 (Add-on)",
    )
    card = select_upgrade_candidate(
        [{
            "simplified": "谁",
            "traditional": "誰",
            "radical_mindmap": {
                "characters": [{
                    "character": "谁",
                    "components": [{"glyph": "讠", "name": "bộ Ngôn"}],
                }],
            },
        }],
        snapshot,
    )
    assert card["simplified"] == "谁"
    assert card["radical_mindmap"]["characters"][0]["character"] == "谁"


def test_upgrade_rejects_card_when_only_non_identity_content_matches_target():
    try:
        select_upgrade_candidate(
            [{"simplified": "哪", "meaning": "谁", "example": "谁来了？"}],
            _snapshot(language="chinese", current_target="谁"),
        )
    except ValueError as error:
        assert str(error) == "card_upgrade_identity_mismatch"
    else:
        raise AssertionError("unexpected non-identity field accepted")


def test_proposal_never_deletes_and_keeps_identity_immutable():
    cfg = {"detect_key": "Front", "json_field_map": {"front": "Front", "meaning": "Meaning", "usage_note": "Usage Note"}}
    changes = proposed_field_changes({"Front": "affect", "Meaning": "ảnh hưởng"}, {"front": "affect", "meaning": "tác động", "usage_note": "Dùng với tân ngữ."}, cfg)
    assert [item["field"] for item in changes] == ["Meaning", "Usage Note"]
    assert changes[-1]["missing"] is True
    assert "MỤC TIÊU CẦN GIỮ NGUYÊN: affect" in build_upgrade_source(_snapshot(), {"Front": "affect"})


def test_proposal_serializes_structured_radical_data_as_json_text():
    cfg = {
        "detect_key": "Front",
        "json_field_map": {"front": "Front", "radical_mindmap": "Radical Mindmap"},
    }
    changes = proposed_field_changes(
        {"Front": "学习", "Radical Mindmap": ""},
        {"front": "学习", "radical_mindmap": {"characters": [{"character": "学"}]}},
        cfg,
    )
    assert changes == [{
        "json_key": "radical_mindmap",
        "field": "Radical Mindmap",
        "current": "",
        "proposed": '{"characters":[{"character":"学"}]}',
        "missing": True,
    }]


def test_chinese_detect_key_resolves_to_real_anki_front_field():
    cfg = {
        "detect_key": "simplified",
        "front_field": "Front",
        "json_field_map": {"simplified": "Front", "radical_mindmap": "Radical Mindmap"},
    }
    assert detect_note_field(cfg) == "Front"
    assert proposed_field_changes(
        {"Front": "谁", "Radical Mindmap": ""},
        {"simplified": "谁", "radical_mindmap": {"characters": [{"character": "谁"}]}},
        cfg,
    ) == [{
        "json_key": "radical_mindmap",
        "field": "Radical Mindmap",
        "current": "",
        "proposed": '{"characters":[{"character":"谁"}]}',
        "missing": True,
    }]


def test_effective_language_config_marks_new_notes_at_current_quality_revision():
    from Language import LANG_CONFIG
    from utils.prompt_config import apply_field_map_to_cfg

    cfg = apply_field_map_to_cfg(dict(LANG_CONFIG["english"]), "english", "vocab")
    assert QUALITY_FIELD in cfg["all_fields"]
    assert cfg["note_defaults"][QUALITY_FIELD] == CURRENT_QUALITY_VERSION


def test_language_note_type_names_are_frozen_to_lts_schema_anchor():
    from Language import LANG_COLLOCATION_CONFIG, LANG_CONFIG, LANG_GRAMMAR_CONFIG
    from utils.model_lifecycle import LTS_NOTE_TYPE_SCHEMA

    for registry in (LANG_CONFIG, LANG_GRAMMAR_CONFIG, LANG_COLLOCATION_CONFIG):
        for cfg in registry.values():
            assert f"V{LTS_NOTE_TYPE_SCHEMA} (Add-on)" in cfg["model_name"]
    for cfg in LANG_CONFIG.values():
        assert cfg["legacy_template_aliases"]["1. Tổng hợp (5 chế độ)"] == (
            cfg["template_names"][0]
        )


class _Note(dict):
    def __init__(self):
        super().__init__({"Front": "affect", "Meaning": "ảnh hưởng"})
        self._model = {"flds": [{"name": "Front"}, {"name": "Meaning"}]}

    def model(self):
        return self._model


class _Models:
    def new_field(self, name):
        return {"name": name}

    def add_field(self, model, field):
        model["flds"].append(field)

    def save(self, _model):
        return None


class _Collection:
    def __init__(self):
        self.note, self.models, self.updated = _Note(), _Models(), 0

    def get_note(self, _note_id):
        return self.note

    def update_note(self, _note):
        self.updated += 1


def test_apply_upgrade_is_target_checked_additive_and_srs_free():
    col = _Collection()
    result = apply_card_upgrade(
        col, 9, "affect", "Front", [{"field": "Usage Note", "proposed": "Dùng với tân ngữ."}],
        {"Example Audio": "[sound:example.mp3]"}, True,
    )
    assert col.note["Usage Note"] == "Dùng với tân ngữ."
    assert col.note["Example Audio"] == "[sound:example.mp3]"
    assert col.note[QUALITY_FIELD] == CURRENT_QUALITY_VERSION
    assert col.updated == 1 and result["quality_current"] is True


def test_apply_confirmed_no_diff_can_mark_existing_card_as_current():
    col = _Collection()
    result = apply_card_upgrade(col, 9, "affect", "Front", [], {}, True)
    assert col.note[QUALITY_FIELD] == CURRENT_QUALITY_VERSION
    assert result["updated_fields"] == [QUALITY_FIELD]
