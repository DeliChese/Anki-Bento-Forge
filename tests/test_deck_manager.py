"""
Unit tests cho utils/deck_manager.py — quản lý Parent/Sub Deck trong Anki collection.

Test:
- create_deck: tạo deck mới, trả về deck_id
- rename_deck: đổi tên deck
- delete_deck: xóa deck
- get_deck_tree: xây dựng cây parent/sub + card count
- get_deck_card_count: đếm thẻ
- refresh_anki: gọi mw.reset()
- import ui/utils package không phá vỡ
"""

import os
import sys
import types
from unittest.mock import MagicMock, patch

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)


# ── Mock Anki (aqt + aqt.qt + aqt.utils) để cho phép import ui package ──
aqt = types.ModuleType("aqt")
aqt.mw = None
sys.modules["aqt"] = aqt

aqt_qt = types.ModuleType("aqt.qt")
for _n in ("QDialog", "QVBoxLayout", "QHBoxLayout", "QGridLayout", "QFormLayout",
           "QLabel", "QPushButton", "QTreeWidget", "QTreeWidgetItem",
           "QInputDialog", "QMessageBox", "QMenu", "QComboBox", "QPlainTextEdit",
           "QLineEdit", "QCheckBox", "QGroupBox", "QSpinBox", "QProgressBar",
           "QTextEdit", "QListWidget", "QListWidgetItem", "QWidget", "QTimer", "QAction",
           "QApplication", "QFileDialog", "QColorDialog", "QDoubleSpinBox",
           "QSlider", "QTableWidget", "QTableWidgetItem", "QScrollArea",
           "QTextBrowser", "QAbstractItemView", "QTabWidget", "QHeaderView"):
    aqt_qt.__dict__[_n] = MagicMock
aqt_qt.Qt = MagicMock()
aqt_qt.Qt.ItemDataRole = type("ItemDataRole", (), {"UserRole": 0})
aqt_qt.Qt.WindowType = type("WindowType", (), {
    "WindowMinMaxButtonsHint": 1, "WindowMaximizeButtonHint": 2,
})
aqt_qt.Qt.ContextMenuPolicy = type("ContextMenuPolicy", (), {"CustomContextMenu": 0})
aqt_qt.Qt.Orientation = type("Orientation", (), {"Horizontal": 1})
aqt_qt.QMessageBox.StandardButton = type("StandardButton", (), {"Yes": 1, "No": 2})
aqt_qt.QDialog.DialogCode = type("DialogCode", (), {"Accepted": 1, "Rejected": 0})
sys.modules["aqt.qt"] = aqt_qt

aqt_utils = types.ModuleType("aqt.utils")
aqt_utils.showInfo = lambda *a, **k: None
aqt_utils.tooltip = lambda *a, **k: None
aqt_utils.qconnect = lambda *a, **k: None
aqt_utils.askUser = lambda *a, **k: True
sys.modules["aqt.utils"] = aqt_utils

from utils.deck_manager import (
    get_deck_tree, create_deck, rename_deck, delete_deck,
    delete_decks, collapse_selected_deck_names, get_deck_card_count, get_deck_names,
    move_decks, refresh_anki,
)


def _make_mw():
    """Tạo mock mw mới cho mỗi test để cô lập hoàn toàn."""
    mw = MagicMock()
    mw.col.decks = MagicMock()
    return mw


# ── Tests ──────────────────────────────────────────────────
def test_create_deck_returns_id():
    mw = _make_mw()
    mw.col.decks.id.return_value = 123
    mw.col.decks.get.return_value = {"id": 123, "name": "Test"}
    with patch("aqt.mw", mw):
        result = create_deck("Test Deck")
    assert result == 123
    mw.col.decks.id.assert_called_once_with("Test Deck")
    mw.col.decks.save.assert_called_once()


def test_create_deck_empty_name_returns_none():
    mw = _make_mw()
    with patch("aqt.mw", mw):
        assert create_deck("   ") is None
    mw.col.decks.id.assert_not_called()


def test_create_deck_error_returns_none():
    mw = _make_mw()
    mw.col.decks.id.side_effect = Exception("boom")
    with patch("aqt.mw", mw):
        assert create_deck("Broken") is None


def test_create_sub_deck_uses_parent_separator():
    mw = _make_mw()
    mw.col.decks.id.return_value = 456
    mw.col.decks.get.return_value = {"id": 456, "name": "Parent::Sub"}
    with patch("aqt.mw", mw):
        result = create_deck("Parent::Sub")
    assert result == 456
    mw.col.decks.id.assert_called_once_with("Parent::Sub")


def test_rename_deck_success():
    mw = _make_mw()
    mw.col.decks.id.return_value = 1
    mw.col.decks.get.return_value = {"id": 1, "name": "Old"}
    with patch("aqt.mw", mw):
        assert rename_deck("Old", "New") is True
    mw.col.decks.rename.assert_called_once()


def test_rename_deck_same_name_returns_false():
    mw = _make_mw()
    with patch("aqt.mw", mw):
        assert rename_deck("Same", "Same") is False
    mw.col.decks.rename.assert_not_called()


def test_rename_deck_error_returns_false():
    mw = _make_mw()
    mw.col.decks.id.return_value = 1
    mw.col.decks.get.return_value = {"id": 1, "name": "Old"}
    mw.col.decks.rename.side_effect = Exception("boom")
    with patch("aqt.mw", mw):
        assert rename_deck("Old", "New") is False


def test_delete_deck_success():
    mw = _make_mw()
    mw.col.decks.id.return_value = 7
    with patch("aqt.mw", mw):
        assert delete_deck("ToDelete") is True
    mw.col.decks.rem.assert_called_once_with(7, cardsToo=True)


def test_delete_deck_empty_returns_false():
    mw = _make_mw()
    with patch("aqt.mw", mw):
        assert delete_deck("  ") is False
    mw.col.decks.rem.assert_not_called()


def test_selected_deck_roots_skip_checked_descendants():
    assert collapse_selected_deck_names([
        "Chinese::HSK1", "Chinese", "Japanese", "Chinese::HSK1::Lesson 1", "Japanese",
    ]) == ["Chinese", "Japanese"]


def test_delete_decks_only_deletes_selected_roots():
    with patch("utils.deck_manager.delete_deck", return_value=True) as delete:
        assert delete_decks(["Chinese", "Chinese::HSK1", "Japanese"]) == ["Chinese", "Japanese"]
    assert delete.call_args_list[0].args == ("Chinese",)
    assert delete.call_args_list[1].args == ("Japanese",)


def test_move_checked_roots_renames_complete_subtree_under_destination():
    mw = _make_mw()
    mw.col.decks.all_names.return_value = ["Japanese", "Japanese::N5", "Archive"]
    mw.col.decks.id.side_effect = lambda name: {"Japanese": 1, "Archive": 2}[name]
    mw.col.decks.get.side_effect = lambda deck_id: {"id": deck_id}

    with patch("aqt.mw", mw):
        moved = move_decks(["Japanese", "Japanese::N5"], "Archive")

    assert moved == [{"old": "Japanese", "new": "Archive::Japanese"}]
    mw.col.decks.rename.assert_called_once_with({"id": 1}, "Archive::Japanese")


def test_move_decks_rejects_cycle_and_existing_destination_collision():
    mw = _make_mw()
    mw.col.decks.all_names.return_value = ["Japanese", "Japanese::N5", "Archive", "Archive::Japanese"]

    with patch("aqt.mw", mw):
        assert move_decks(["Japanese"], "Japanese::N5") == []
        assert move_decks(["Japanese"], "Archive") == []
    mw.col.decks.rename.assert_not_called()


def test_move_decks_to_root_makes_selected_subdeck_a_parent():
    mw = _make_mw()
    mw.col.decks.all_names.return_value = ["Japanese", "Japanese::N5"]
    mw.col.decks.id.return_value = 3
    mw.col.decks.get.return_value = {"id": 3}

    with patch("aqt.mw", mw):
        assert get_deck_names() == ["Japanese", "Japanese::N5"]
        assert move_decks(["Japanese::N5"], None) == [{"old": "Japanese::N5", "new": "N5"}]
    mw.col.decks.rename.assert_called_once_with({"id": 3}, "N5")


def test_get_deck_card_count():
    mw = _make_mw()
    mw.col.decks.id.return_value = 5
    mw.col.decks.card_count.return_value = 42
    with patch("aqt.mw", mw):
        assert get_deck_card_count("MyDeck") == 42
    mw.col.decks.card_count.assert_called_once_with(5, include_subdecks=True)


def test_get_deck_tree_builds_hierarchy():
    mw = _make_mw()
    decks = mw.col.decks
    # get_deck_tree dùng all_names() để lấy toàn bộ tên deck
    decks.all_names.return_value = ["Parent", "Parent::Sub", "Other"]
    decks.id.side_effect = lambda name: {"Parent": 1, "Parent::Sub": 2, "Other": 3}[name]
    decks.card_count.return_value = 10

    with patch("aqt.mw", mw):
        tree = get_deck_tree()
    # 2 deck cha: Parent (có sub) và Other
    assert len(tree) == 2
    parent = next(n for n in tree if n["name"] == "Parent")
    assert parent["card_count"] == 10
    assert len(parent["children"]) == 1
    assert parent["children"][0]["name"] == "Parent::Sub"
    assert parent["children"][0]["card_count"] == 10
    other = next(n for n in tree if n["name"] == "Other")
    assert other["children"] == []


def test_get_deck_tree_error_returns_empty():
    mw = _make_mw()
    mw.col.decks.all_names.side_effect = Exception("boom")
    with patch("aqt.mw", mw):
        assert get_deck_tree() == []


def test_refresh_anki_calls_reset():
    mw = _make_mw()
    with patch("aqt.mw", mw):
        refresh_anki()
    mw.reset.assert_called_once()


def test_ui_package_imports_deck_manager_dialog():
    """Xác minh ui/__init__.py import được DeckManagerDialog (không phá vỡ)."""
    from ui import DeckManagerDialog
    assert DeckManagerDialog is not None


def test_deck_manager_dialog_exposes_checked_multi_selection_controls():
    source = open(
        os.path.join(_addon_root, "ui", "deck_manager_dialog.py"), encoding="utf-8"
    ).read()
    assert "ExtendedSelection" in source
    assert "ItemIsUserCheckable" in source
    assert "def _checked_deck_names" in source
    assert "def _set_all_checked" in source
    assert "delete_decks(roots)" in source
    assert "def _move_to" in source
    assert "move_decks(roots, destination or None)" in source


def test_utils_package_exports_deck_manager():
    """Xác minh utils/__init__.py export các hàm deck_manager."""
    from utils import (
        get_deck_tree, create_deck, rename_deck, delete_deck, delete_decks,
        collapse_selected_deck_names, get_deck_names, move_decks, refresh_anki,
    )
    assert callable(get_deck_tree)
    assert callable(create_deck)
    assert callable(rename_deck)
    assert callable(get_deck_names)
    assert callable(move_decks)
    assert callable(delete_deck)
    assert callable(delete_decks)
    assert callable(collapse_selected_deck_names)
    assert callable(refresh_anki)
