from utils.card_upgrade import (
    CURRENT_QUALITY_VERSION, QUALITY_FIELD, apply_card_upgrade, build_upgrade_source,
    proposed_field_changes, select_upgrade_candidate, upgrade_is_available,
)


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


def test_upgrade_candidate_must_keep_current_identity():
    card = select_upgrade_candidate([{"front": "affect", "meaning": "tác động"}], _snapshot())
    assert card["front"] == "affect"
    try:
        select_upgrade_candidate([{"front": "effect"}], _snapshot())
    except ValueError as error:
        assert str(error) == "card_upgrade_identity_mismatch"
    else:
        raise AssertionError("unexpected different target accepted")


def test_proposal_never_deletes_and_keeps_identity_immutable():
    cfg = {"detect_key": "Front", "json_field_map": {"front": "Front", "meaning": "Meaning", "usage_note": "Usage Note"}}
    changes = proposed_field_changes({"Front": "affect", "Meaning": "ảnh hưởng"}, {"front": "affect", "meaning": "tác động", "usage_note": "Dùng với tân ngữ."}, cfg)
    assert [item["field"] for item in changes] == ["Meaning", "Usage Note"]
    assert changes[-1]["missing"] is True
    assert "MỤC TIÊU CẦN GIỮ NGUYÊN: affect" in build_upgrade_source(_snapshot(), {"Front": "affect"})


def test_effective_language_config_marks_new_notes_at_current_quality_revision():
    from Language import LANG_CONFIG
    from utils.prompt_config import apply_field_map_to_cfg

    cfg = apply_field_map_to_cfg(dict(LANG_CONFIG["english"]), "english", "vocab")
    assert QUALITY_FIELD in cfg["all_fields"]
    assert cfg["note_defaults"][QUALITY_FIELD] == CURRENT_QUALITY_VERSION


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
