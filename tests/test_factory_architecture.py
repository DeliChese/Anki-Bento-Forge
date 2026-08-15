"""Regression gates for the C1 package/UI boundary."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_package_root_is_a_small_compatibility_facade():
    source = _source("__init__.py")
    assert len(source.splitlines()) < 1500
    assert "AnkiSmartFactory = _factory_dialog.AnkiSmartFactory" in source
    assert "start_smart_factory = _factory_dialog.start_smart_factory" in source


def test_package_root_has_no_direct_anki_or_qt_dependency():
    tree = ast.parse(_source("__init__.py"))
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    assert not any(
        name == "aqt" or name.startswith("aqt.") or name == "anki" or name.startswith("anki.")
        for name in imported_modules
    )


def test_factory_dialog_is_the_ui_orchestration_owner():
    tree = ast.parse(_source("ui/factory_dialog.py"))
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    assert "AnkiSmartFactory" in classes

    source = _source("ui/factory_dialog.py")
    assert "from utils.factory_state import FactoryStateStore" in source
    assert "from utils.anki_adapter import AnkiCollectionAdapter" in source
    assert "from utils.import_operations import apply_import, prepare_audio_tasks" in source
    assert "from utils.model_lifecycle import ensure_model" in source
