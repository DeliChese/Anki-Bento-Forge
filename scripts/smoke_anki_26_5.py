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

from Language import LANG_CONFIG  # noqa: E402
from mode import LANG_CSS, LANG_TEMPLATES  # noqa: E402
from mode.card_render import build_afmt, build_qfmt  # noqa: E402
from mode.knowledge import KNOWLEDGE_MODEL_NAME  # noqa: E402
from utils.import_operations import (  # noqa: E402
    apply_import,
    apply_knowledge_import,
    rollback_knowledge_import,
)
from utils.import_safety import rollback_added_notes  # noqa: E402
from utils.model_lifecycle import ensure_model  # noqa: E402


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


_LANGUAGE_SMOKE_ITEMS = {
    "japanese": {
        "front": "頼る",
        "meaning": "dựa vào; trông cậy vào",
        "usage_pattern": "Nに頼る",
        "usage_note": "Người hoặc nguồn lực được dựa vào đi với に.",
        "collocation": "友達に頼る",
    },
    "chinese": {
        "simplified": "依靠",
        "meaning": "dựa vào; nương tựa",
        "usage_pattern": "依靠 + 人/资源",
        "usage_note": "Dùng khi một người cần sự hỗ trợ từ người hoặc nguồn lực khác.",
        "collocation": "依靠朋友",
    },
    "korean": {
        "front": "의지하다",
        "meaning": "dựa vào; nương tựa",
        "usage_pattern": "N에게/에 의지하다",
        "usage_note": "Người thường đi với 에게; sự vật hoặc nguồn lực thường đi với 에.",
        "collocation": "친구에게 의지하다",
    },
    "english": {
        "front": "depend",
        "meaning": "phụ thuộc; dựa vào",
        "usage_pattern": "depend on + noun/pronoun",
        "usage_note": "Không dùng depend of trong nghĩa này.",
        "collocation": "depend heavily on",
    },
}


def _ensure_language_model(col: Collection, language: str):
    cfg = LANG_CONFIG[language]
    templates = LANG_TEMPLATES[language]
    return ensure_model(
        col.models,
        cfg,
        templates,
        LANG_CSS[language](),
        build_qfmt,
        build_afmt,
        rename_primary_template=True,
        prune_extra_templates=False,
    ).model


def _smoke_usage_guide(col: Collection) -> None:
    """Exercise P1-05 through Anki's real model, renderer, and undo backend."""
    guide_fields = ("Usage Pattern", "Usage Note", "Collocation")
    for language, item in _LANGUAGE_SMOKE_ITEMS.items():
        cfg = LANG_CONFIG[language]
        model = _ensure_language_model(col, language)

        # Simulate a pre-P1-05 model, then run the same additive migration used
        # by the dialog. No personal collection or profile is involved.
        for field_name in guide_fields:
            field = next(field for field in model["flds"] if field["name"] == field_name)
            col.models.remove_field(model, field)
        col.models.save(model)
        migrated = _ensure_language_model(col, language)
        field_names = [field["name"] for field in migrated["flds"]]
        assert all(field_names.count(name) == 1 for name in guide_fields), (language, field_names)
        assert len(migrated["tmpls"]) == len(LANG_TEMPLATES[language]) // 2
        for template in migrated["tmpls"]:
            assert not any("{{" + name + "}}" in template["qfmt"] for name in guide_fields)
        assert all("{{" + name + "}}" in migrated["tmpls"][0]["afmt"] for name in guide_fields)

        deck_id = col.decks.id("Bento P1-05 Anki 26.5 Smoke::" + language)
        undo_entry = col.add_custom_undo_entry("Bento P1-05 add " + language)
        added = apply_import(
            col,
            [{"item": item, "action": "add", "nid": None, "update_fields": []}],
            cfg,
            deck_id,
            {},
            lambda: False,
        )
        col.merge_undo_entries(undo_entry)
        assert added["errors"] == 0 and added["added"] == 1, (language, added)
        note_id = added["added_note_ids"][0]
        note = col.get_note(note_id)
        for json_key, field_name in zip(
            ("usage_pattern", "usage_note", "collocation"), guide_fields
        ):
            assert note[field_name] == item[json_key], (language, field_name)

        card_ids = _card_ids(col, note_id)
        assert len(card_ids) == 1, (language, card_ids)
        card = col.get_card(card_ids[0])
        question = card.question()
        answer = card.answer()
        assert not any(item[key] in question for key in ("usage_pattern", "usage_note", "collocation"))
        assert all(item[key] in answer for key in ("usage_pattern", "usage_note", "collocation"))

        old_note = item["usage_note"]
        updated_note = old_note + " [updated]"
        update_item = {**item, "usage_note": updated_note}
        undo_entry = col.add_custom_undo_entry("Bento P1-05 update " + language)
        updated = apply_import(
            col,
            [{
                "item": update_item,
                "action": "update",
                "nid": note_id,
                "update_fields": ["Usage Note"],
            }],
            cfg,
            deck_id,
            {},
            lambda: False,
        )
        col.merge_undo_entries(undo_entry)
        assert updated["errors"] == 0 and updated["updated"] == 1, (language, updated)
        assert col.get_note(note_id)["Usage Note"] == updated_note
        col.undo()
        assert col.get_note(note_id)["Usage Note"] == old_note

        assert rollback_added_notes(col, [note_id, note_id, 0, "invalid"]) == 1
        assert not _card_ids(col, note_id)


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
            _smoke_usage_guide(col)
            print(
                "PASS: Anki 26.5 collection/import/update/undo/rollback compatibility; "
                "P1-05 Usage Guide migrated and rendered back-only for 4 languages"
            )
            return 0
        finally:
            col.close()


if __name__ == "__main__":
    raise SystemExit(main())
