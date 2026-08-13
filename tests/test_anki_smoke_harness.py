"""Release smoke harness for the public Anki integration boundary.

This is not a replacement for manual testing in Anki. It verifies the add-on's
contracts with the public APIs that a release relies on, without importing an
installed Anki runtime.
"""

import importlib
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _Hook:
    def __init__(self):
        self.callbacks = []

    def append(self, callback):
        self.callbacks.append(callback)


class _Operation:
    instances = []

    def __init__(self, *, parent, op):
        self.parent = parent
        self.op = op
        self.success_callback = None
        self.failure_callback = None
        self.ran = False
        self.__class__.instances.append(self)

    def success(self, callback):
        self.success_callback = callback
        return self

    def failure(self, callback):
        self.failure_callback = callback
        return self

    def run_in_background(self):
        self.ran = True
        return self


def test_import_and_undo_use_the_managed_collection_operation(monkeypatch):
    """A release import must enter Anki through CollectionOp, not a worker."""
    aqt_module = types.ModuleType("aqt")
    aqt_module.__path__ = []
    operations_module = types.ModuleType("aqt.operations")
    operations_module.QueryOp = _Operation
    operations_module.CollectionOp = _Operation
    monkeypatch.setitem(sys.modules, "aqt", aqt_module)
    monkeypatch.setitem(sys.modules, "aqt.operations", operations_module)

    class FakeNote(dict):
        def __init__(self, *_args):
            super().__init__()
            self.id = 0
            self.flushed = False

        def flush(self):
            self.flushed = True

    anki_module = types.ModuleType("anki")
    notes_module = types.ModuleType("anki.notes")
    notes_module.Note = FakeNote
    monkeypatch.setitem(sys.modules, "anki", anki_module)
    monkeypatch.setitem(sys.modules, "anki.notes", notes_module)

    from utils import anki_ops

    importlib.reload(anki_ops)
    _Operation.instances.clear()
    operation = anki_ops.run_collection("parent", lambda col: {"added": 1}, lambda _: None, lambda _: None)

    assert isinstance(operation, _Operation)
    assert operation.ran is True
    assert operation.parent == "parent"
    assert operation.op(MagicMock()) == {"added": 1}

    import_operations = importlib.import_module("utils.import_operations")
    importlib.reload(import_operations)

    class FakeCollection:
        def __init__(self):
            self.models = MagicMock()
            self.models.by_name.return_value = {"name": "Smoke model"}
            self.added_notes = []

        def add_note(self, note, _deck_id):
            note.id = 42
            self.added_notes.append(note)

    report = import_operations.apply_import(
        FakeCollection(),
        [{"item": {"front": "smoke"}, "action": "add"}],
        {
            "lang_code": "ja", "audio_fields": [],
            "json_field_map": {"front": "Front"}, "all_fields": ["Front"],
            "model_name": "Smoke model", "front_field": "Front", "detect_key": "front",
        },
        1,
        {},
        lambda: False,
    )
    assert report["added"] == 1
    assert report["added_note_ids"] == [42]


def test_combo_and_reviewer_hooks_register_through_public_gui_hooks(monkeypatch):
    """Reviewer and WebView enhancements must be independently optional."""
    from hooks import overview_mode, reviewer

    gui_hooks = types.SimpleNamespace(
        reviewer_did_show_question=_Hook(),
        reviewer_did_show_answer=_Hook(),
        webview_did_receive_js_message=_Hook(),
    )
    monkeypatch.setattr(reviewer, "gui_hooks", gui_hooks)
    monkeypatch.setattr(overview_mode, "gui_hooks", gui_hooks)
    reviewer._REGISTERED_HOOKS.clear()
    overview_mode._REGISTERED_HOOKS.clear()

    assert reviewer.register_hooks() is True
    assert overview_mode.register_overview_hooks() is True
    assert gui_hooks.reviewer_did_show_question.callbacks == [reviewer._on_reviewer_question]
    assert gui_hooks.reviewer_did_show_answer.callbacks == [reviewer._on_reviewer_answer]
    assert gui_hooks.webview_did_receive_js_message.callbacks == [overview_mode._on_js_message]

    from mode.shared import _COMBO_MODE_JS

    assert "ai_factory_set_mode" in _COMBO_MODE_JS


def test_config_migration_preserves_a_recoverable_backup():
    """A migration must be reversible before a release can claim safety."""
    from utils import user_data

    root = Path(os.environ["BENTO_FORGE_DATA_DIR"]) / "smoke-migration"
    root.mkdir(parents=True, exist_ok=True)
    legacy = root / "legacy.json"
    target = root / "profile" / "config.json"
    legacy.write_text('{"language": "en"}', encoding="utf-8")

    assert user_data.migrate_legacy_json(
        str(legacy), str(target), lambda value: value.get("language") == "en"
    )
    assert Path(f"{target}.legacy-backup").is_file()
    assert user_data.rollback_migration(str(target)) is True
