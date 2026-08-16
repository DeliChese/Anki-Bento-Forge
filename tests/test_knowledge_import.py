"""V18-05 CollectionOp-side Knowledge import/update/undo regressions."""

import importlib
import sys
import types

from mode.knowledge import KNOWLEDGE_FIELDS, KNOWLEDGE_MODEL_NAME


class FakeNote(dict):
    _next_id = 100

    def __init__(self, _col=None, _model=None, **fields):
        super().__init__({field: "" for field in KNOWLEDGE_FIELDS})
        self.update(fields)
        self.id = 0
        self.tags = []
        self.flushed = 0

    def flush(self):
        self.flushed += 1


def _operations(monkeypatch):
    notes = types.ModuleType("anki.notes")
    notes.Note = FakeNote
    anki = types.ModuleType("anki")
    anki.notes = notes
    monkeypatch.setitem(sys.modules, "anki", anki)
    monkeypatch.setitem(sys.modules, "anki.notes", notes)
    module = importlib.import_module("utils.import_operations")
    return importlib.reload(module)


def _card(answer="Central Processing Unit"):
    return {
        "type": "basic", "question": "What is CPU?", "answer": answer,
        "explanation": "", "source": "", "tags": ["computing"], "cloze_text": "",
    }


class Collection:
    def __init__(self):
        model = {
            "id": 18, "name": KNOWLEDGE_MODEL_NAME,
            "flds": [{"name": field} for field in KNOWLEDGE_FIELDS],
            "tmpls": [
                {"name": "Basic Q&A", "qfmt": "", "afmt": ""},
                {"name": "Cloze", "qfmt": "", "afmt": ""},
            ],
            "css": "",
        }
        self.models = types.SimpleNamespace(by_name=lambda name: model, save=lambda _model: None)
        self.notes = {7: FakeNote(**{
            "Type": "basic", "Question": "What is CPU?", "Answer": "old",
            "Duplicate Key": "whatiscpu",
        })}
        self.notes[7].id = 7
        self.removed = []
        self.updated = []

    def add_note(self, note, deck_id):
        assert deck_id == 42
        note.id = FakeNote._next_id
        FakeNote._next_id += 1
        self.notes[note.id] = note

    def get_note(self, nid):
        return self.notes[nid]

    def update_note(self, note):
        self.updated.append(note.id)

    def remove_notes(self, ids):
        self.removed.extend(ids)
        for nid in ids:
            self.notes.pop(nid, None)


def test_knowledge_import_updates_adds_and_undoes_only_its_batch(monkeypatch):
    operations = _operations(monkeypatch)
    col = Collection()
    batch = [
        {"item": _card("new"), "action": "update", "nid": 7, "update_fields": ["Answer"]},
        {"item": {**_card(), "question": "What is RAM?", "answer": "Memory"},
         "action": "add", "nid": None, "update_fields": []},
    ]
    report = operations.apply_knowledge_import(col, batch, 42, lambda: False)
    added_id = report["added_note_ids"][0]

    assert report["learning_mode"] == "knowledge"
    assert (report["added"], report["updated"], report["audio_gen"]) == (1, 1, 0)
    assert col.notes[7]["Answer"] == "new"
    assert col.notes[added_id]["Source"] == ""
    assert col.updated == [7, added_id]

    undone = operations.rollback_knowledge_import(col, report)
    assert undone == {"removed": 1, "restored": 1}
    assert col.notes[7]["Answer"] == "old"
    assert added_id not in col.notes
    assert col.updated == [7, added_id, 7]


def test_save_note_falls_back_to_flush_for_legacy_collection(monkeypatch):
    operations = _operations(monkeypatch)
    note = FakeNote()

    operations._save_note(object(), note)

    assert note.flushed == 1


def test_knowledge_import_honors_cancel_before_mutation(monkeypatch):
    operations = _operations(monkeypatch)
    col = Collection()
    report = operations.apply_knowledge_import(
        col,
        [{"item": _card(), "action": "add", "nid": None, "update_fields": []}],
        42,
        lambda: True,
    )
    assert report["cancelled"] is True
    assert report["added"] == report["updated"] == 0


def test_knowledge_cancel_mid_batch_rolls_back_partial_mutation(monkeypatch):
    operations = _operations(monkeypatch)
    col = Collection()
    calls = {"count": 0}

    def cancelled():
        calls["count"] += 1
        return calls["count"] > 1

    report = operations.apply_knowledge_import(
        col,
        [
            {"item": {**_card(), "question": "One?"}, "action": "add", "nid": None, "update_fields": []},
            {"item": {**_card(), "question": "Two?"}, "action": "add", "nid": None, "update_fields": []},
        ],
        42,
        cancelled,
    )
    assert report["cancelled"] is True
    assert report["cancel_rollback"] == {"removed": 1, "restored": 0}
    assert report["added_note_ids"] == []
