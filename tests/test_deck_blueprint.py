"""Regression contract for structured-source AI Deck Blueprint."""

import json

from utils.deck_blueprint import (
    attach_source_context,
    build_blueprint_import_plan,
    create_blueprint_decks,
    deck_names_from_blueprint,
    flatten_section_content,
    normalize_deck_blueprint,
    parse_structured_source,
    read_blueprint_existing_cards,
    recheck_blueprint_import_plan,
)


def test_markdown_h1_to_h6_preserves_paths_and_excludes_headings():
    source = """# Travel
intro
## Airport
搭乗券 | boarding pass
#### Check-in details
預け荷物 | checked baggage
## Hotel
予約 | reservation
###### Polite phrases
お願いします | please
"""
    sections = parse_structured_source(source)

    assert [section["level"] for section in sections] == [1, 2, 4, 2, 6]
    assert sections[2]["path"] == ["Travel", "Airport", "Check-in details"]
    assert sections[4]["path"] == ["Travel", "Hotel", "Polite phrases"]
    flattened = flatten_section_content(sections)
    assert "# Travel" not in flattened
    assert "搭乗券" in flattened


def test_rich_html_headings_win_over_qtextedit_plain_wrapper():
    html = "<h1>Chinese Travel</h1><p>机场 | airport</p><h2>Hotel</h2><p>预订 | book</p>"
    sections = parse_structured_source("ignored flat text", html)

    assert [section["title"] for section in sections] == ["Chinese Travel", "Hotel"]
    assert sections[1]["path"] == ["Chinese Travel", "Hotel"]
    assert "预订" in sections[1]["content"]


def test_plain_h_markers_and_unsectioned_source_are_supported():
    marked = parse_structured_source("H1: 한국어\n학교 | school\nH3 - 수업\n교실 | classroom")
    assert marked[1]["path"] == ["한국어", "수업"]

    flat = parse_structured_source("hello | xin chào\nworld | thế giới")
    assert len(flat) == 1
    assert flat[0]["title"] == "Unsectioned"
    assert flat[0]["word_count"] == 2


def test_heading_context_is_attached_by_vocabulary_surface():
    sections = parse_structured_source("# Travel\n## Airport\n- 搭乗券 | boarding pass\n預け荷物: baggage")
    vocab = attach_source_context(
        [{"front": "搭乗券", "meaning": "boarding pass"}, {"front": "預け荷物"}],
        sections,
    )

    assert vocab[0]["source_path"] == ["Travel", "Airport"]
    assert vocab[1]["source_heading"] == "Airport"


def test_batch_parser_accepts_bulleted_pipe_rows_below_headings():
    from utils.batch_processor import parse_word_list

    parsed = parse_word_list("- 搭乗券 | boarding pass\n2. 預け荷物 | checked baggage")

    assert parsed == [
        {"front": "搭乗券", "meaning": "boarding pass", "level": "", "topic": ""},
        {"front": "預け荷物", "meaning": "checked baggage", "level": "", "topic": ""},
    ]


def test_blueprint_normalizer_deduplicates_assignments_and_surfaces_missing_words():
    vocab = [{"front": "搭乗券"}, {"front": "預け荷物"}, {"front": "予約"}]
    raw = {
        "suggestion": "Use headings",
        "decks": [{
            "parent": "Travel::Unsafe",
            "sub_decks": [
                {"name": "Airport", "words": ["搭乗券", "預け荷物"]},
                {"name": "Airport", "words": ["搭乗券"]},
            ],
        }],
    }

    result = normalize_deck_blueprint(
        raw, vocab, default_parent="Japanese Travel", unassigned_name="Needs review"
    )

    assert result["decks"][0]["parent"] == "Travel Unsafe"
    assert result["decks"][0]["sub_decks"][0]["words"] == ["搭乗券", "預け荷物"]
    assert result["decks"][0]["sub_decks"][0]["word_count"] == 2
    assert result["unassigned_count"] == 1
    assert result["decks"][1]["sub_decks"][0]["words"] == ["予約"]


def test_deck_names_are_stable_and_do_not_create_extra_depth():
    blueprint = {
        "decks": [{
            "parent": "Travel::Japanese",
            "sub_decks": [{"name": "Airport::Check-in"}, {"name": "Airport::Check-in"}],
        }]
    }
    assert deck_names_from_blueprint(blueprint) == [
        "Travel Japanese", "Travel Japanese::Airport Check-in"
    ]


def test_ai_organizer_receives_source_paths_outline_and_user_constraints(monkeypatch):
    from utils import batch_processor

    captured = {}

    def fake_post(url, payload, headers, **kwargs):
        captured["payload"] = payload
        return json.dumps({
            "choices": [{"message": {"content": json.dumps({
                "suggestion": "Follow the source",
                "decks": [{
                    "parent": "Travel",
                    "sub_decks": [{"name": "Airport", "words": ["搭乗券"]}],
                }],
            }, ensure_ascii=False)}}],
        }, ensure_ascii=False)

    monkeypatch.setattr(batch_processor, "get_api_config", lambda: {
        "api_key": "test", "api_base": "https://example.invalid/v1", "model": "test-model"
    })
    monkeypatch.setattr(batch_processor, "_http_post_json", fake_post)
    monkeypatch.setattr(batch_processor, "get_language", lambda: "en")

    result = batch_processor.organize_decks_with_ai(
        [{"front": "搭乗券", "source_path": ["Travel", "Airport"]}],
        "japanese",
        source_sections=[{
            "id": "section-2", "level": 2, "path": ["Travel", "Airport"],
            "word_count": 1,
        }],
        custom_instruction="Keep each deck below 30 words",
    )

    prompt = captured["payload"]["messages"][1]["content"]
    assert "SOURCE: Travel > Airport" in prompt
    assert "SOURCE OUTLINE" in prompt
    assert "Keep each deck below 30 words" in prompt
    assert result["decks"][0]["sub_decks"][0]["words"] == ["搭乗券"]


def test_collection_save_creates_only_approved_names_and_reuses_matches():
    class Decks:
        def __init__(self):
            self.names = ["Travel"]

        def all_names(self):
            return list(self.names)

        def id(self, name):
            if name not in self.names:
                self.names.append(name)
            return self.names.index(name) + 1

    collection = type("Collection", (), {"decks": Decks()})()
    result = create_blueprint_decks(collection, {
        "decks": [{
            "parent": "Travel",
            "sub_decks": [{"name": "Airport"}, {"name": "Hotel"}],
        }]
    })

    assert result["reused"] == ["Travel"]
    assert result["created"] == ["Travel::Airport", "Travel::Hotel"]
    assert collection.decks.names == ["Travel", "Travel::Airport", "Travel::Hotel"]


def test_import_plan_is_add_only_and_fail_closed_for_duplicates_conflicts_and_gaps():
    vocab = [
        {"front": "alpha", "meaning": "one", "example": "alpha example"},
        {"front": "beta", "meaning": "two", "example": "beta example"},
        {"front": "gamma", "meaning": "three", "example": "gamma example"},
        {"front": "delta", "meaning": "four", "example": "delta example"},
    ]
    blueprint = {"decks": [{
        "parent": "English",
        "sub_decks": [{"name": "Core", "words": ["alpha", "beta", "gamma", "ghost"]}],
    }]}

    plan = build_blueprint_import_plan(
        blueprint,
        vocab,
        existing_cards=[
            {"front": "Alpha", "meaning": "one", "nid": 1},
            {"front": "beta", "meaning": "different", "nid": 2},
        ],
    )

    assert plan["new"] == 1
    assert plan["duplicates"] == 1
    assert plan["conflicts"] == 1
    assert plan["unassigned"] == 1
    assert plan["missing_assignments"] == 1
    assert plan["groups"][0]["deck_name"] == "English::Core"
    entry = plan["groups"][0]["entries"][0]
    assert entry["item"]["front"] == "gamma"
    assert entry["action"] == "add"
    assert entry["audio_enabled"] == (False, False, False)


def test_import_plan_blocks_ambiguous_same_surface_in_current_batch():
    plan = build_blueprint_import_plan(
        {"decks": [{"parent": "P", "sub_decks": [{"name": "S", "words": ["term"]}]}]},
        [
            {"front": "term", "meaning": "first"},
            {"front": "term", "meaning": "second"},
        ],
    )

    assert plan["new"] == 0
    assert plan["conflicts"] == 1
    assert plan["groups"] == []


def test_import_plan_uses_factory_unicode_punctuation_duplicate_key():
    plan = build_blueprint_import_plan(
        {"decks": [{"parent": "P", "sub_decks": [{"name": "S", "words": ["Ｃａｆé—test"]}]}]},
        [{"front": "Ｃａｆé—test", "meaning": "sample"}],
        existing_cards=[{"front": "café test", "meaning": "sample"}],
    )

    assert plan["new"] == 0
    assert plan["duplicates"] == 1


def test_final_recheck_blocks_collection_changes_after_confirmation():
    plan = {"groups": [{
        "deck_name": "P::S",
        "entries": [
            {"item": {"front": "new", "meaning": "same"}, "action": "add"},
            {"item": {"front": "conflict", "meaning": "new meaning"}, "action": "add"},
            {"item": {"front": "safe", "meaning": "ok"}, "action": "add"},
        ],
    }]}

    checked = recheck_blueprint_import_plan(plan, [
        {"front": "new", "meaning": "same"},
        {"front": "conflict", "meaning": "old meaning"},
    ])

    assert checked["new"] == 1
    assert checked["late_duplicates"] == 1
    assert checked["late_conflicts"] == 1
    assert checked["groups"][0]["entries"][0]["item"]["front"] == "safe"


def test_existing_card_scan_is_global_to_model_and_supports_first_run():
    class Models:
        def __init__(self, model):
            self.model = model

        def by_name(self, name):
            return self.model if name == "Current" else None

    class Collection:
        def __init__(self, model):
            self.models = Models(model)
            self.queries = []

        def find_notes(self, query):
            self.queries.append(query)
            return [10, 11]

        def get_note(self, note_id):
            return {
                "Front": "alpha" if note_id == 10 else "beta",
                "Meaning": "one" if note_id == 10 else "two",
            }

    cfg = {
        "model_name": "Current", "old_model_names": ["Old"],
        "front_field": "Front", "json_field_map": {"meaning": "Meaning"},
    }
    collection = Collection({"id": 42})

    cards = read_blueprint_existing_cards(collection, cfg)

    assert collection.queries == ['"mid:42"']
    assert cards == [
        {"front": "alpha", "meaning": "one", "nid": 10},
        {"front": "beta", "meaning": "two", "nid": 11},
    ]
    assert read_blueprint_existing_cards(Collection(None), cfg) == []


def test_existing_card_scan_includes_current_and_historical_note_types():
    class Models:
        def by_name(self, name):
            return {"Current": {"id": 1}, "Old": {"id": 2}}.get(name)

    class Collection:
        models = Models()

        def find_notes(self, query):
            return [10] if query == '"mid:1"' else [20]

        def get_note(self, note_id):
            return {"Front": f"word-{note_id}", "Meaning": "meaning"}

    cards = read_blueprint_existing_cards(Collection(), {
        "model_name": "Current", "old_model_names": ["Old"],
        "front_field": "Front", "json_field_map": {"meaning": "Meaning"},
    })

    assert [card["nid"] for card in cards] == [10, 20]


def test_collection_import_applies_add_only_groups_and_returns_exact_undo_ids(monkeypatch):
    from utils import deck_blueprint_import

    class Decks:
        def __init__(self):
            self.names = []

        def all_names(self):
            return list(self.names)

        def id(self, name):
            if name not in self.names:
                self.names.append(name)
            return self.names.index(name) + 1

    collection = type("Collection", (), {
        "decks": Decks(), "models": object(),
    })()
    ensured = []
    imported = []
    monkeypatch.setattr(
        deck_blueprint_import,
        "ensure_model",
        lambda *args, **kwargs: ensured.append((args, kwargs)),
    )
    monkeypatch.setattr(
        deck_blueprint_import, "read_blueprint_existing_cards", lambda *_args: []
    )
    monkeypatch.setattr(deck_blueprint_import, "_prepare_legacy_model", lambda *_args: None)

    def fake_apply(_col, entries, _cfg, deck_id, audio_tags, is_cancelled):
        imported.append((entries, deck_id, audio_tags, is_cancelled()))
        note_id = 100 + deck_id
        return {"added": len(entries), "added_note_ids": [note_id], "errors": 0}

    monkeypatch.setattr(deck_blueprint_import, "_apply_import", fake_apply)
    blueprint = {"decks": [{
        "parent": "Travel", "sub_decks": [{"name": "Airport", "words": ["gate"]}],
    }]}
    plan = {"groups": [{
        "deck_name": "Travel::Airport",
        "entries": [{"item": {"front": "gate"}, "action": "add"}],
    }]}

    result = deck_blueprint_import.apply_blueprint_import(
        collection, blueprint, plan, {"model_name": "M"}, [], "", lambda: "", lambda: "",
    )

    assert len(ensured) == 1
    assert imported[0][2:] == ({}, False)
    assert result["added"] == 1
    assert result["added_note_ids"] == [102]
    assert result["deck_counts"] == {"Travel::Airport": 1}


def test_collection_import_rejects_any_update_action_before_mutation():
    from utils.deck_blueprint_import import apply_blueprint_import

    plan = {"groups": [{"deck_name": "P::S", "entries": [{"action": "update"}]}]}
    try:
        apply_blueprint_import(None, {}, plan, {}, [], "", None, None)
    except ValueError as error:
        assert "add-only" in str(error)
    else:
        raise AssertionError("update action must be rejected")


def test_deck_center_is_the_single_compact_editable_confirmation_gated_entry():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    dialog = (root / "ui" / "deck_blueprint_dialog.py").read_text(encoding="utf-8")
    factory = (root / "ui" / "factory_dialog.py").read_text(encoding="utf-8")
    manager = (root / "ui" / "deck_manager_dialog.py").read_text(encoding="utf-8")

    assert "_COMPACT_SOURCE_HEIGHT = 145" in dialog
    assert "ItemIsEditable" in dialog
    assert "InternalMove" in dialog
    assert "QMessageBox.question" in dialog
    assert "run_collection(" in dialog
    assert 't("blueprint_import")' in dialog
    assert "build_blueprint_import_plan" in dialog
    assert "rollback_added_notes" in dialog
    assert "def start_deck_blueprint" not in factory
    assert "blueprint_action = QAction" not in factory
    assert 't("deck_manage_btn")' in factory
    assert "def _open_blueprint" in manager
    assert 't("deck_center_open_blueprint")' in manager


def test_deck_center_forwards_current_forge_source_without_a_global_cache():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    factory = (root / "ui" / "factory_dialog.py").read_text(encoding="utf-8")
    manager = (root / "ui" / "deck_manager_dialog.py").read_text(encoding="utf-8")
    dialog = (root / "ui" / "deck_blueprint_dialog.py").read_text(encoding="utf-8")

    assert 'source_text = self.ai_text_input.toPlainText()' in factory
    assert '"language": self._current_lang' in factory
    assert 'blueprint_source={' in factory
    assert "blueprint_source=None" in manager
    assert 'initial_source=self._blueprint_source.get("text", "")' in manager
    assert "def _apply_initial_source" in dialog
    assert "self.txt_source.setPlainText(source_text)" in dialog
    assert '"blueprint_source_reused"' in dialog
