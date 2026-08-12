"""Unit tests for the narrow, safe rollback boundary of import batches."""

import os
import sys

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

from utils.import_safety import rollback_added_notes, summarize_import_batch


class FakeCollection:
    def __init__(self):
        self.removed_ids = None

    def remove_notes(self, note_ids):
        self.removed_ids = list(note_ids)


def test_summarize_import_batch_counts_only_new_and_updates():
    summary = summarize_import_batch([
        {"action": "add"},
        {"action": "add_partial"},
        {"action": "update"},
        {"action": "dup_diff"},
        {},
    ])

    assert summary == {"new": 2, "updates": 1}


def test_rollback_removes_only_valid_unique_note_ids():
    collection = FakeCollection()

    removed = rollback_added_notes(collection, [42, "43", 42, 0, -1, "bad", None])

    assert removed == 2
    assert collection.removed_ids == [42, 43]


def test_rollback_with_no_valid_ids_does_not_call_collection():
    collection = FakeCollection()

    removed = rollback_added_notes(collection, [None, "bad", 0, -1])

    assert removed == 0
    assert collection.removed_ids is None
