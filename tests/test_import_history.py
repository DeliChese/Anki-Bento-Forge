"""Regression tests for the isolated import-history owner."""

import ast
import time
from pathlib import Path

import pytest

from utils import ai_extractor
from utils import import_history as history


@pytest.fixture(autouse=True)
def _isolated_history(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "_HISTORY_PATH", str(tmp_path / "import_history.json"))
    monkeypatch.setattr(history, "_LEGACY_HISTORY_PATH", str(tmp_path / "legacy.json"))


def test_c2_ai_extractor_line_budget_is_locked():
    source = Path(ai_extractor.__file__).read_text(encoding="utf-8")
    # The usage-history and provider-key ownership paths need modest headroom,
    # but this remains a guard against returning to an unbounded monolith.
    assert len(source.splitlines()) < 1600


def test_history_owner_has_no_anki_ui_or_ai_orchestration_dependency():
    source = Path(history.__file__).read_text(encoding="utf-8")
    imports = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    assert not imports.intersection({"aqt", "Language", "ai_extractor", "ui", "workers"})


def test_ai_extractor_reexports_history_api_without_accessing_mw(monkeypatch):
    direct_names = (
        "add_to_import_history",
        "get_import_history",
        "get_import_history_items",
        "search_import_history",
        "get_history_summary_text",
        "clear_import_history",
    )
    for name in direct_names:
        assert getattr(ai_extractor, name) is getattr(history, name)

    captured = {}

    def fake_init(*, force_rescan, scan_context_factory, cancel_event, progress_callback):
        captured.update(force_rescan=force_rescan, factory=scan_context_factory)
        return {"ok": True}

    monkeypatch.setattr(history, "init_import_history", fake_init)
    context_factory = lambda: (object(), {})
    assert ai_extractor.init_import_history(
        force_rescan=True, scan_context_factory=context_factory
    ) == {"ok": True}
    assert captured["force_rescan"] is True
    assert captured["factory"] is context_factory


def test_existing_history_never_rescans_only_because_its_timestamp_is_old():
    data = history._load_history()
    data["last_full_scan"] = time.time() - (history._HISTORY_SCAN_TTL * 2)
    data["entries"] = {"japanese": {"食べる": {"front": "食べる"}}}
    history._save_history(data)

    def unexpected_scan():
        raise AssertionError("scan context must stay lazy while TTL is valid")

    loaded = history.init_import_history(scan_context_factory=unexpected_scan)
    assert loaded["entries"] == data["entries"]


def test_cancelled_bootstrap_does_not_persist_partial_results():
    class Models:
        @staticmethod
        def by_name(_name):
            return {"flds": [{"name": "Front"}, {"name": "Meaning"}]}

    class Database:
        @staticmethod
        def all(_query, *_ids):
            return [(1, "one\\x1fmeaning")]

    class Collection:
        models = Models()
        db = Database()

        @staticmethod
        def find_notes(_query):
            return [1]

    class CancelEvent:
        cancelled = False

        def is_set(self):
            return self.cancelled

        def set(self):
            self.cancelled = True

    cancel_event = CancelEvent()
    progress = []

    def stop_after_first_progress(update):
        progress.append(update)
        cancel_event.set()

    result = history.init_import_history(
        scan_context_factory=lambda: (Collection(), {
            "japanese": {"model_name": "Test", "front_field": "Front"},
        }),
        cancel_event=cancel_event,
        progress_callback=stop_after_first_progress,
    )

    assert result["_scan_cancelled"] is True
    assert progress[0]["total"] == 1
    persisted = history.load_import_history()
    assert persisted["entries"] == {}
    assert persisted["last_full_scan"] is None


def test_forced_scan_uses_injected_collection_and_language_config():
    class Models:
        @staticmethod
        def by_name(_name):
            return {
                "flds": [
                    {"name": "Front"},
                    {"name": "Meaning"},
                    {"name": "Furigana"},
                    {"name": "JLPT Level"},
                ]
            }

    class Database:
        @staticmethod
        def all(_query, *_ids):
            return [(1, "食べる\x1făn\x1fたべる\x1fN5")]

    class Collection:
        models = Models()
        db = Database()

        @staticmethod
        def find_notes(_query):
            return [1]

    configs = {
        "japanese": {
            "model_name": "Test Japanese",
            "front_field": "Front",
            "furi_label": "Furigana",
            "level_field": "JLPT Level",
        }
    }
    data = history.init_import_history(
        force_rescan=True,
        scan_context_factory=lambda: (Collection(), configs),
    )

    entry = data["entries"]["japanese"]["食べる"]
    assert entry["meaning"] == "ăn"
    assert entry["furigana"] == "たべる"
    assert entry["level"] == "N5"
    assert data["_scan_summary"]["total_words_scanned"] == 1


def test_history_query_search_summary_and_clear():
    history.add_to_import_history(
        [{"front": "食べる", "meaning": "ăn", "jlptlevel": "N5", "topic": "food"}],
        "japanese",
        deck_name="JP",
    )
    history.add_to_import_history(
        [{"simplified": "学习", "meaning": "học", "hsk_level": "HSK1", "pinyin": "xuéxí"}],
        "chinese",
        deck_name="ZH",
    )

    japanese = history.get_import_history(lang="japanese")
    assert japanese["total_count"] == 1
    assert japanese["summary"]["japanese"]["levels"] == {"N5": 1}
    assert history.search_import_history("xué", lang="chinese")[0]["front"] == "学习"
    assert "食べる = ăn [N5]" in history.get_history_summary_text("japanese")

    assert history.clear_import_history() is True
    assert not Path(history._HISTORY_PATH).exists()
