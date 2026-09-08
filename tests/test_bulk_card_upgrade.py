"""Contracts for the opt-in collection-wide existing-card updater."""

from utils.bulk_card_upgrade import (
    apply_bulk_upgrade_candidate, build_bulk_upgrade_plan,
)
from utils.card_upgrade import CURRENT_QUALITY_VERSION


_CFG = {
    "model_name": "AnkiTool English V18.3 (Add-on)",
    "detect_key": "front",
    "front_field": "Front",
    "json_field_map": {"front": "Front", "meaning": "Meaning"},
}


class _Note(dict):
    def __init__(self, note_id, values, model_name=_CFG["model_name"]):
        super().__init__(values)
        self.id = note_id
        self._model = {
            "name": model_name,
            "flds": [{"name": name} for name in values],
        }

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
    def __init__(self, note):
        self.note = note
        self.models = _Models()
        self.updated = 0

    def get_note(self, _note_id):
        return self.note

    def update_note(self, _note):
        self.updated += 1


def test_plan_only_sends_outdated_notes_to_ai_and_keeps_current_template_notes_free():
    old = _Note(1, {"Front": "affect", "Meaning": "ảnh hưởng"})
    current = _Note(2, {
        "Front": "effect", "Meaning": "hiệu ứng",
        "Bento Quality Version": CURRENT_QUALITY_VERSION,
    })
    plan = build_bulk_upgrade_plan([old, current], _CFG, language="english", kind="vocab")
    assert plan["total"] == 2
    assert plan["ai_required"] == 1
    assert plan["template_only"] == 1
    assert plan["snapshots"][0]["note_id"] == 1
    assert plan["snapshots"][0]["current_target"] == "affect"


def test_plan_includes_current_chinese_card_when_radical_map_is_missing():
    cfg = {
        "model_name": "AnkiTool Chinese V18.3 (Add-on)",
        "detect_key": "simplified",
        "front_field": "Front",
        "json_field_map": {
            "simplified": "Front", "meaning": "Meaning", "radical_mindmap": "Radical Mindmap",
        },
    }
    note = _Note(3, {
        "Front": "谁", "Meaning": "ai", "Radical Mindmap": "",
        "Bento Quality Version": CURRENT_QUALITY_VERSION,
    }, cfg["model_name"])
    plan = build_bulk_upgrade_plan([note], cfg, language="chinese", kind="vocab")
    assert plan["ai_required"] == 1
    assert plan["snapshots"][0]["current_target"] == "谁"


def test_apply_bulk_candidate_is_additive_identity_safe_and_marks_current():
    note = _Note(4, {"Front": "affect", "Meaning": "ảnh hưởng"})
    col = _Collection(note)
    snapshot = build_bulk_upgrade_plan([note], _CFG, language="english", kind="vocab")["snapshots"][0]
    result = apply_bulk_upgrade_candidate(
        col, snapshot, {"front": "affect", "meaning": "tác động"}, _CFG,
    )
    assert note["Front"] == "affect"
    assert note["Meaning"] == "tác động"
    assert note["Bento Quality Version"] == CURRENT_QUALITY_VERSION
    assert col.updated == 1
    assert result["quality_current"] is True


def test_factory_exposes_bulk_upgrade_for_the_active_language_and_kind():
    from pathlib import Path

    source = (Path(__file__).parents[1] / "ui" / "factory_dialog.py").read_text(encoding="utf-8")
    assert "self.btn_bulk_upgrade" in source
    assert "def _open_bulk_card_upgrade(self):" in source
    assert "language=self._current_lang" in source
    assert "kind=self._current_card_kind()" in source


def test_bulk_dialog_processes_one_note_at_a_time_with_provider_pacing():
    from pathlib import Path

    source = (Path(__file__).parents[1] / "ui" / "bulk_card_upgrade_dialog.py").read_text(
        encoding="utf-8"
    )
    assert "CardUpgradeAiWorker(" in source
    assert "QTimer.singleShot(1_500, self._next)" in source
    assert "self.worker.stop()" in source
