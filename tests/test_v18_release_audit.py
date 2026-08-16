"""V18-06 release-candidate metadata and compatibility contracts."""

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_manifest_declares_learning_modes_and_anki_26_5_install_metadata():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["config"]["learning_modes"] == ["language", "knowledge"]
    assert manifest["anki"] == {"min_version": "2.1.50", "max_version": "26.5"}
    assert manifest["package"] == "bento_forge"
    assert manifest["min_point_version"] == 50
    assert manifest["max_point_version"] == 260500


def test_v18_user_docs_and_pending_release_gate_are_present():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    checklist = (ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    smoke = (ROOT / "work_items" / "V18_SMOKE_PROFILE.md").read_text(encoding="utf-8")

    assert "Learning Modes (V18 release candidate)" in readme
    assert "V18 Learning Modes" in changelog.split("## [V17.1]", 1)[0]
    assert "V18 release-candidate gate" in checklist
    assert "manifest.json` từ `17.2.0` sang `18.0.0" in checklist
    assert "Undo khôi phục update" in smoke


def test_knowledge_domain_modules_do_not_import_anki_or_qt():
    for relative in (
        "utils/knowledge_schema.py",
        "utils/knowledge_model.py",
        "utils/knowledge_workflow.py",
        "utils/knowledge_extractor.py",
        "utils/learning_mode.py",
    ):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        assert roots.isdisjoint({"aqt", "anki", "PyQt5", "PyQt6"}), relative
