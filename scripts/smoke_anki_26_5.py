"""Headless compatibility smoke against Anki 26.5's real collection API.

Run this script with Anki's bundled Python, not the project's test Python::

    <anki>/.venv/Scripts/python.exe scripts/smoke_anki_26_5.py

It creates and removes a temporary collection.  No user profile is opened.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from anki.collection import Collection  # noqa: E402
from aqt import gui_hooks  # noqa: E402
from aqt.operations import CollectionOp, QueryOp  # noqa: E402

from mode.knowledge import KNOWLEDGE_MODEL_NAME  # noqa: E402
from utils.import_operations import apply_knowledge_import, rollback_knowledge_import  # noqa: E402


def _basic(answer: str = "Central Processing Unit") -> dict:
    return {
        "type": "basic",
        "question": "What is CPU?",
        "answer": answer,
        "explanation": "A processor term.",
        "source": "V18 smoke",
        "tags": ["v18", "basic"],
        "cloze_text": "",
    }


def _cloze() -> dict:
    return {
        "type": "cloze",
        "question": "",
        "answer": "",
        "explanation": "A memory term.",
        "source": "V18 smoke",
        "tags": ["v18", "cloze"],
        "cloze_text": "RAM is {{c1::volatile memory}}.",
    }


def _card_ids(col: Collection, note_id: int) -> list:
    return list(col.find_cards("nid:{}".format(note_id)))


def main() -> int:
    import hooks.overview_mode  # noqa: F401
    import hooks.reviewer  # noqa: F401
    import ui.factory_dialog  # noqa: F401

    assert CollectionOp is not None and QueryOp is not None
    for hook_name in (
        "overview_will_render_content",
        "reviewer_did_show_question",
        "webview_did_receive_js_message",
        "main_window_did_init",
    ):
        assert hasattr(gui_hooks, hook_name), hook_name

    # Keeping the database below the repository also lets restricted CI/sandbox
    # runners grant the Rust backend the same write scope as this process.
    with tempfile.TemporaryDirectory(
        prefix=".bento-v18-anki265-", dir=str(ROOT), ignore_cleanup_errors=True
    ) as temp_dir:
        collection_path = Path(temp_dir) / "collection.anki2"
        col = Collection(str(collection_path))
        try:
            assert col.models.by_name(KNOWLEDGE_MODEL_NAME) is None
            deck_id = col.decks.id("Bento V18 Anki 26.5 Smoke")
            initial = apply_knowledge_import(
                col,
                [
                    {"item": _basic(), "action": "add", "nid": None, "update_fields": []},
                    {"item": _cloze(), "action": "add", "nid": None, "update_fields": []},
                ],
                deck_id,
                lambda: False,
            )
            assert initial["errors"] == 0, initial
            assert initial["added"] == 2, initial
            assert len(initial["added_note_ids"]) == 2, initial
            basic_id, cloze_id = initial["added_note_ids"]
            assert len(_card_ids(col, basic_id)) == 1
            assert len(_card_ids(col, cloze_id)) == 1

            update_and_add = apply_knowledge_import(
                col,
                [
                    {
                        "item": _basic("CPU updated"),
                        "action": "update",
                        "nid": basic_id,
                        "update_fields": ["Answer"],
                    },
                    {
                        "item": {**_basic("Random Access Memory"), "question": "What is RAM?"},
                        "action": "add",
                        "nid": None,
                        "update_fields": [],
                    },
                ],
                deck_id,
                lambda: False,
            )
            assert update_and_add["errors"] == 0, update_and_add
            added_id = update_and_add["added_note_ids"][0]
            assert col.get_note(basic_id)["Answer"] == "CPU updated"
            assert len(_card_ids(col, added_id)) == 1

            undone = rollback_knowledge_import(col, update_and_add)
            assert undone == {"removed": 1, "restored": 1}
            assert col.get_note(basic_id)["Answer"] == "Central Processing Unit"
            assert not _card_ids(col, added_id)
            assert len(_card_ids(col, cloze_id)) == 1
            print("PASS: Anki 26.5 collection/import/update/rollback compatibility")
            return 0
        finally:
            col.close()


if __name__ == "__main__":
    raise SystemExit(main())
