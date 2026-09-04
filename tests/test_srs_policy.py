import sys
import types
from unittest.mock import MagicMock


class FakeNote(dict):
    def __init__(self, **fields):
        super().__init__(fields)
        self.flush_count = 0

    def flush(self):
        self.flush_count += 1


def test_layout_defaults_are_opt_in():
    from utils.srs_policy import SRS_FIELD, apply_srs_layout_to_config

    base = {"all_fields": ["Front", SRS_FIELD]}
    combo = apply_srs_layout_to_config(base, "invalid")
    independent = apply_srs_layout_to_config(base, "independent")
    assert combo["note_defaults"][SRS_FIELD] == ""
    assert independent["note_defaults"][SRS_FIELD] == "1"
    assert "note_defaults" not in base


def test_legacy_multi_card_migration_preserves_cards_and_marks_notes():
    from utils.srs_policy import (
        SRS_FIELD, needs_legacy_srs_migration, prepare_legacy_srs_model,
    )

    model = {"id": 7, "flds": [{"name": "Front"}], "tmpls": [{}, {}]}
    notes = {1: FakeNote(**{SRS_FIELD: ""}), 2: FakeNote(**{SRS_FIELD: ""})}
    manager = MagicMock()
    manager.new_field.side_effect = lambda name: {"name": name}
    manager.add_field.side_effect = lambda target, field: target["flds"].append(field)
    collection = MagicMock()
    collection.find_notes.return_value = [1, 2]
    collection.get_note.side_effect = notes.get

    assert needs_legacy_srs_migration(model) is True
    result = prepare_legacy_srs_model(collection, manager, model)
    assert result.changed_notes == 2
    assert all(note[SRS_FIELD] == "1" for note in notes.values())
    assert collection.update_note.call_count == 2
    assert all(note.flush_count == 0 for note in notes.values())
    assert not hasattr(collection, "remCards") or not collection.remCards.called


def test_deck_migration_is_idempotent_and_only_generates_new_directions():
    from utils.srs_policy import SRS_FIELD, migrate_deck_to_independent

    model = {
        "id": 9,
        "flds": [{"name": "Front"}, {"name": SRS_FIELD}],
        "tmpls": [{}, {}, {}, {}, {}],
    }
    notes = {
        11: FakeNote(**{SRS_FIELD: ""}),
        12: FakeNote(**{SRS_FIELD: "1"}),
    }
    collection = MagicMock()
    collection.db.list.return_value = [11, 12]
    collection.get_note.side_effect = notes.get

    first = migrate_deck_to_independent(collection, model, 123)
    second = migrate_deck_to_independent(collection, model, 123)
    assert first.matched_notes == 2
    assert first.changed_notes == 1
    assert second.changed_notes == 0
    collection.gen_cards.assert_called_once_with([11])
    assert notes[11].flush_count == 1
    assert notes[12].flush_count == 0


def test_model_lifecycle_can_preserve_unknown_extra_templates():
    from utils.model_lifecycle import ensure_model

    model = {
        "id": 2,
        "flds": [{"name": "Front"}, {"name": "SRS Independent"}],
        "tmpls": [{"name": f"old-{index}"} for index in range(6)],
    }
    manager = MagicMock()
    manager.by_name.return_value = model
    cfg = {
        "model_name": "Vocabulary",
        "old_model_names": [],
        "all_fields": ["Front", "SRS Independent"],
        "template_names": [f"new-{index}" for index in range(5)],
    }
    templates = tuple(lambda: "{{Front}}" for _ in range(10))

    result = ensure_model(
        manager, cfg, templates, "css", lambda *_args: "q", lambda *_args: "a",
        rename_primary_template=True, prune_extra_templates=False,
    )
    assert result.had_extra_templates is True
    assert len(model["tmpls"]) == 6
    manager.remove_template.assert_not_called()


def test_import_marks_only_new_independent_notes(monkeypatch):
    if "anki.notes" not in sys.modules:
        anki_module = types.ModuleType("anki")
        notes_module = types.ModuleType("anki.notes")
        notes_module.Note = object
        monkeypatch.setitem(sys.modules, "anki", anki_module)
        monkeypatch.setitem(sys.modules, "anki.notes", notes_module)
    import utils.import_operations as operations
    from utils.srs_policy import SRS_FIELD

    created = []

    class NewNote(FakeNote):
        def __init__(self, _collection, _model):
            super().__init__(Front="", **{SRS_FIELD: ""})
            self.id = 0
            created.append(self)

    collection = MagicMock()
    collection.models.by_name.return_value = {"name": "Vocabulary"}

    def add_note(note, _deck_id):
        note.id = 99

    collection.add_note.side_effect = add_note
    monkeypatch.setattr(operations, "Note", NewNote)
    cfg = {
        "model_name": "Vocabulary",
        "detect_key": "front",
        "front_field": "Front",
        "lang_code": "ja",
        "audio_fields": [],
        "json_field_map": {"front": "Front"},
        "all_fields": ["Front", SRS_FIELD],
        "note_defaults": {SRS_FIELD: "1"},
    }
    report = operations.apply_import(
        collection,
        [{"action": "add", "item": {"front": "食べる"}}],
        cfg,
        3,
        {},
        lambda: False,
    )
    assert report["added"] == 1
    assert created[0][SRS_FIELD] == "1"
