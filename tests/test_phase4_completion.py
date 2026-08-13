"""Regression tests for the remaining Phase 4 architecture and UX work."""

import importlib.util
import sys
import types
from pathlib import Path

from utils.model_lifecycle import collect_template_fields, ensure_model


ROOT = Path(__file__).resolve().parent.parent

_accessibility_spec = importlib.util.spec_from_file_location("phase4_accessibility", ROOT / "ui" / "accessibility.py")
_accessibility = importlib.util.module_from_spec(_accessibility_spec)
_accessibility_spec.loader.exec_module(_accessibility)
configure_keyboard_navigation = _accessibility.configure_keyboard_navigation


class FakeModelManager:
    def __init__(self, model=None):
        self.model = model
        self.saved = []
        self.added = []

    def by_name(self, name):
        if self.model and self.model["name"] == name:
            return self.model
        return None

    def save(self, model):
        self.saved.append(model)

    def new(self, name):
        self.model = {"name": name, "id": 10, "flds": [], "tmpls": [], "css": ""}
        return self.model

    def new_field(self, name):
        return {"name": name}

    def add_field(self, model, field):
        model["flds"].append(field)

    def new_template(self, name):
        return {"name": name, "qfmt": "", "afmt": ""}

    def add_template(self, model, template):
        model["tmpls"].append(template)

    def remove_template(self, model, template):
        model["tmpls"].remove(template)

    def add(self, model):
        self.added.append(model)


def _cfg():
    return {
        "model_name": "Bento Test", "old_model_names": ["Bento Old"],
        "all_fields": ["Front", "Meaning"], "template_names": ["Card"],
    }


def _templates():
    return [lambda: "{{Front}}", lambda: "{{type:Meaning}} {{#Extra}}{{/Extra}}"]


def _qfmt(cfg, templates, index):
    return templates[index]()


def _afmt(cfg, templates, index):
    return templates[index]()


def test_model_lifecycle_creates_complete_model_without_ui_or_anki_import():
    manager = FakeModelManager()
    result = ensure_model(manager, _cfg(), _templates(), ".card{}", _qfmt, _afmt,
                          rename_primary_template=True)

    assert result.existed is False
    assert [field["name"] for field in result.model["flds"]] == ["Front", "Meaning"]
    assert result.model["tmpls"][0]["qfmt"] == "{{Front}}"
    assert manager.added == [result.model]


def test_model_lifecycle_migrates_fields_and_reduces_extra_templates():
    existing = {
        "name": "Bento Test", "id": 10, "flds": [{"name": "Front"}],
        "tmpls": [{"name": "Old", "qfmt": "", "afmt": ""}, {"name": "Extra", "qfmt": "", "afmt": ""}],
        "css": "old",
    }
    manager = FakeModelManager(existing)
    result = ensure_model(manager, _cfg(), _templates(), ".card{color:red}", _qfmt, _afmt,
                          rename_primary_template=True)

    assert result.existed is True and result.had_extra_templates is True
    assert {field["name"] for field in existing["flds"]} == {"Front", "Meaning", "Extra"}
    assert len(existing["tmpls"]) == 1
    assert existing["tmpls"][0]["name"] == "Card"
    assert existing["css"] == ".card{color:red}"
    assert manager.saved == [existing]


def test_template_field_parser_excludes_anki_special_fields():
    fields = collect_template_fields([lambda: "{{FrontSide}} {{Tags}} {{#Front}}{{type:Meaning}}{{/Front}}"])
    assert fields == {"Front", "Meaning"}


class FakeWidget:
    def __init__(self):
        self.name = self.description = self.focus = None

    def setAccessibleName(self, value):
        self.name = value

    def setAccessibleDescription(self, value):
        self.description = value

    def setFocusPolicy(self, value):
        self.focus = value


class FakeDialog:
    def __init__(self):
        self.order = []

    def setTabOrder(self, before, after):
        self.order.append((before, after))


def test_keyboard_navigation_has_accessible_metadata_and_stable_order():
    dialog, first, second = FakeDialog(), FakeWidget(), FakeWidget()
    configure_keyboard_navigation(dialog, [(first, "Input"), (second, "Import")],
                                  description="Use Tab", focus_policy="strong")

    assert (first.name, first.description, first.focus) == ("Input", "Use Tab", "strong")
    assert dialog.order == [(first, second)]


def test_dark_and_light_stylesheets_resolve_all_tokens():
    qt = types.ModuleType("aqt.qt")
    for name in ("QDialog", "QVBoxLayout", "QHBoxLayout", "QLabel", "QPushButton", "QComboBox",
                 "QSlider", "QSpinBox", "QColorDialog", "QGroupBox", "QGridLayout", "QSplitter"):
        setattr(qt, name, type(name, (), {}))
    qt.QColor = type("QColor", (), {})
    qt.Qt = type("Qt", (), {})
    aqt = types.ModuleType("aqt")
    utils = types.ModuleType("aqt.utils")
    utils.tooltip = lambda *args, **kwargs: None
    previous = {name: sys.modules.get(name) for name in ("aqt", "aqt.qt", "aqt.utils")}
    sys.modules.update({"aqt": aqt, "aqt.qt": qt, "aqt.utils": utils})
    try:
        spec = importlib.util.spec_from_file_location("phase4_theme", ROOT / "ui" / "theme.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for preset in ("glass_dark", "glass_light", "midnight"):
            qss = module.build_stylesheet({"preset": preset, "accent": "#6aa7ff", "glass_alpha": 7,
                                           "font_size": 13, "radius": 14})
            assert "__" not in qss
            assert module.PRESETS[preset]["text"] in qss
            assert "QLineEdit:focus" in qss
    finally:
        for name, original in previous.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
