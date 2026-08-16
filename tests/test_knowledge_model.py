"""V18-03 tests for the isolated Knowledge note type and import boundary."""

from mode.knowledge import KNOWLEDGE_FIELDS, KNOWLEDGE_MODEL_NAME, KNOWLEDGE_TEMPLATES, knowledge_css
from utils.knowledge_model import (
    ensure_knowledge_model,
    knowledge_duplicate_scope,
    knowledge_note_payload,
)


class FakeModelManager:
    def __init__(self, models=None):
        self.models = dict(models or {})
        self.added = []
        self.saved = []
        self.removed = []

    def by_name(self, name):
        return self.models.get(name)

    def new(self, name):
        return {"name": name, "id": 99, "flds": [], "tmpls": [], "css": ""}

    def new_field(self, name):
        return {"name": name}

    def add_field(self, model, field):
        model["flds"].append(field)

    def new_template(self, name):
        return {"name": name, "qfmt": "", "afmt": ""}

    def add_template(self, model, template):
        model["tmpls"].append(template)

    def remove_template(self, model, template):
        self.removed.append(template)
        model["tmpls"].remove(template)

    def add(self, model):
        self.models[model["name"]] = model
        self.added.append(model)

    def save(self, model):
        self.saved.append(model)


def _basic_card():
    return {
        "type": "basic", "question": " What is CPU? ", "answer": "Central Processing Unit",
        "explanation": "", "source": "notes", "tags": ["computing"], "cloze_text": "",
    }


def test_knowledge_model_is_created_idempotently_without_touching_language_models():
    language_model = {"name": "AnkiTool Japanese V17.0 (Add-on)", "flds": [], "tmpls": [], "css": ""}
    manager = FakeModelManager({language_model["name"]: language_model})

    created = ensure_knowledge_model(manager)
    updated = ensure_knowledge_model(manager)
    model = created.model
    model["tmpls"].append({"name": "User extension", "qfmt": "custom", "afmt": "custom"})
    preserved = ensure_knowledge_model(manager)

    assert created.existed is False and updated.existed is True
    assert preserved.had_extra_templates is True
    assert model["name"] == KNOWLEDGE_MODEL_NAME
    assert [field["name"] for field in model["flds"]] == list(KNOWLEDGE_FIELDS)
    assert [template["name"] for template in model["tmpls"]] == ["Basic Q&A", "Cloze", "User extension"]
    assert manager.added == [model]
    assert manager.removed == []
    assert language_model == {"name": "AnkiTool Japanese V17.0 (Add-on)", "flds": [], "tmpls": [], "css": ""}


def test_knowledge_templates_have_separate_basic_and_cloze_card_boundaries():
    basic_q, basic_a, cloze_q, cloze_a = (template() for template in KNOWLEDGE_TEMPLATES)
    assert "{{#Question}}" in basic_q and "{{^Cloze Text}}" in basic_q
    assert "{{Answer}}" in basic_a and "{{Explanation}}" in basic_a and "{{Source}}" in basic_a
    assert "{{cloze:Cloze Text}}" in cloze_q and "{{cloze:Cloze Text}}" in cloze_a
    assert ".knowledge-source" in knowledge_css()


def test_knowledge_payload_and_duplicate_scope_stay_within_knowledge_model_and_deck():
    payload = knowledge_note_payload(_basic_card())
    scope = knowledge_duplicate_scope(_basic_card(), deck_id=42)

    assert payload["fields"]["Question"] == "What is CPU?"
    assert payload["fields"]["Duplicate Key"] == "whatiscpu"
    assert payload["tags"] == ["computing"]
    assert (scope.deck_id, scope.model_name, scope.key) == (42, KNOWLEDGE_MODEL_NAME, "whatiscpu")

    cloze_scope = knowledge_duplicate_scope({
        "type": "cloze", "question": "", "answer": "", "explanation": "", "source": "",
        "tags": [], "cloze_text": "A {{c1::pure function}} has no side effects.",
    }, deck_id=42)
    assert cloze_scope.key == "apurefunctionhasnosideeffects"
