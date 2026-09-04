"""Regression coverage for versioned Reviewer examples."""

from types import SimpleNamespace

import pytest

from utils.example_note_ops import (
    activate_example_version,
    delete_example_version,
    save_example_version,
)
from utils.example_versions import (
    HISTORY_FIELD,
    append_version,
    delete_version,
    empty_history,
    example_field_names,
    parse_history,
    reusable_audio,
    select_version,
    slot_state,
)


def _record(text, *, reading="", translation="", audio=""):
    return {
        "text": text,
        "reading": reading,
        "translation": translation,
        "audio": audio,
    }


@pytest.mark.parametrize(
    ("language", "reading_field"),
    [
        ("japanese", "Example3 Reading"),
        ("chinese", "Example3 Pinyin"),
        ("korean", "Example3 Romanization"),
        ("english", "Example3 Pronunciation"),
    ],
)
def test_example_field_mapping_covers_all_languages(language, reading_field):
    fields = example_field_names(language, 3)
    assert fields == {
        "text": "Example3",
        "reading": reading_field,
        "translation": "Example3 in Vietnamese",
        "audio": "Example3 Audio",
    }


def test_append_select_delete_preserves_versions_until_explicit_delete():
    original = _record(
        "I study every day.", translation="Tôi học mỗi ngày.", audio="[sound:old.mp3]",
    )
    history, state = append_version(
        empty_history(), 3,
        _record("I reviewed tonight.", translation="Tối nay tôi đã ôn bài."),
        seed=original,
    )
    history, state = append_version(
        history, 3,
        _record("I will revise tomorrow.", translation="Ngày mai tôi sẽ ôn lại."),
    )

    assert state["active"] == 2
    assert [item["text"] for item in state["versions"]] == [
        "I study every day.", "I reviewed tonight.", "I will revise tomorrow.",
    ]
    assert reusable_audio(history, 3, "I study every day.") == "[sound:old.mp3]"

    history, state = select_version(history, 3, 1)
    assert state["active"] == 1
    history, state = delete_version(history, 3, 1)
    assert state["active"] == 1
    assert [item["text"] for item in state["versions"]] == [
        "I study every day.", "I will revise tomorrow.",
    ]


def test_duplicate_and_corrupt_history_are_rejected_without_data_loss():
    history, _state = append_version(empty_history(), 1, _record("Same"))
    with pytest.raises(ValueError, match="example_version_duplicate"):
        append_version(history, 1, _record("Same"))
    with pytest.raises(ValueError, match="example_history_corrupt"):
        parse_history("{broken")


class _FakeNote(dict):
    def __init__(self, note_id, model, values):
        super().__init__(values)
        self.id = note_id
        self._model = model

    def __getitem__(self, key):
        return self.get(key, "")

    def model(self):
        return self._model


class _FakeModels:
    def new_field(self, name):
        return {"name": name}

    def add_field(self, model, field):
        model["flds"].append(field)

    def save(self, _model):
        return None


class _FakeCollection:
    def __init__(self, note):
        self.note = note
        self.models = _FakeModels()
        self.updated = []

    def get_note(self, note_id):
        assert note_id == self.note.id
        return self.note

    def update_note(self, note):
        self.updated.append(note)


def test_collection_mutations_migrate_fields_and_restore_saved_audio():
    model = {
        "name": "Bento Forge English Vocabulary",
        "flds": [
            {"name": "Example"}, {"name": "Example in Vietnamese"},
            {"name": "Example Audio"},
        ],
    }
    note = _FakeNote(42, model, {
        "Example": "Original sentence.",
        "Example in Vietnamese": "Câu gốc.",
        "Example Audio": "[sound:original.mp3]",
    })
    col = _FakeCollection(note)

    result = save_example_version(
        col, 42, "english", 1,
        _record(
            "A new sentence.", reading="/a nuː ˈsentəns/",
            translation="Một câu mới.", audio="[sound:new.mp3]",
        ),
    )
    assert (result["current"], result["total"]) == (2, 2)
    assert HISTORY_FIELD in {field["name"] for field in model["flds"]}
    assert note["Example"] == "A new sentence."
    assert note["Example Audio"] == "[sound:new.mp3]"

    restored = activate_example_version(col, 42, "english", 1, 0)
    assert (restored["current"], restored["total"]) == (1, 2)
    assert note["Example"] == "Original sentence."
    assert note["Example Audio"] == "[sound:original.mp3]"

    remaining = delete_example_version(col, 42, "english", 1, 0)
    assert (remaining["current"], remaining["total"]) == (1, 1)
    assert note["Example"] == "A new sentence."


def test_review_example_parser_accepts_one_strict_object():
    from utils.review_example_ai import decode_payload

    adapted = SimpleNamespace(
        structured_data=None,
        text='{"sentence":"Hello.","reading":"/həˈloʊ/","translation":"Xin chào."}',
    )
    assert decode_payload(adapted) == {
        "text": "Hello.", "reading": "/həˈloʊ/", "translation": "Xin chào.",
    }


def test_review_example_request_is_compact_and_bounded(monkeypatch):
    import json
    from utils import ai_extractor, review_example_ai

    captured = {}

    class _Policy:
        def configure(self, **_kwargs):
            return None

        def estimate(self, **kwargs):
            captured["estimate"] = kwargs
            return {}

        def check(self, _estimate):
            return ""

    def fake_post(_url, payload, _headers, **_kwargs):
        captured["payload"] = payload
        return json.dumps({
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": json.dumps({
                    "sentence": "I learn through varied examples.",
                    "reading": "/aɪ lɜːrn θruː ˈverid ɪɡˈzæmpəlz/",
                    "translation": "Tôi học qua các ví dụ đa dạng.",
                })},
            }],
        })

    monkeypatch.setattr(ai_extractor, "get_api_config", lambda: {
        "api_key": "test-key", "api_base": "https://api.openai.com/v1",
        "model": "test-model", "max_tokens": 8192,
    })
    monkeypatch.setattr(ai_extractor, "get_ai_session_policy", lambda: _Policy())
    monkeypatch.setattr(ai_extractor, "_http_post_json", fake_post)

    result = review_example_ai.generate_review_example_with_ai(
        target="learn", meaning="học", language="english",
        difficulty="advanced", length="long",
        existing_examples=[f"old-{index}" for index in range(20)],
    )

    assert result["error"] is None
    assert result["text"] == "I learn through varied examples."
    assert captured["payload"]["max_tokens"] <= 700
    assert len(captured["payload"]["messages"]) == 2
    request = json.loads(captured["payload"]["messages"][1]["content"])
    assert request["difficulty"] == "advanced"
    assert request["length"] == "long"
    assert len(request["avoid"]) == 8


def test_review_example_request_uses_its_configured_model(monkeypatch):
    import json
    from utils import ai_extractor, review_example_ai

    class _Policy:
        def configure(self, **_kwargs):
            return None

        def estimate(self, **_kwargs):
            return {}

        def check(self, _estimate):
            return ""

    captured = {}
    monkeypatch.setattr(review_example_ai, "get_review_example_api_config", lambda: {
        "api_key": "test-key", "api_base": "https://api.openai.com/v1",
        "model": "example-model", "max_tokens": 8192,
    })
    monkeypatch.setattr(ai_extractor, "get_ai_session_policy", lambda: _Policy())
    monkeypatch.setattr(
        ai_extractor, "_http_post_json",
        lambda _url, payload, _headers, **_kwargs: captured.setdefault("body", payload) and json.dumps({
            "choices": [{"finish_reason": "stop", "message": {"content": json.dumps({
                "sentence": "A test sentence.", "reading": "/test/", "translation": "Một câu thử.",
            })}}],
        }),
    )

    result = review_example_ai.generate_review_example_with_ai(
        target="test", meaning="thử", language="english",
    )
    assert result["error"] is None
    assert captured["body"]["model"] == "example-model"


def test_language_models_include_version_storage_and_four_reading_fields():
    from Language import LANG_CONFIG, LANG_GRAMMAR_CONFIG

    suffixes = {
        "japanese": " Reading", "chinese": " Pinyin",
        "korean": " Romanization", "english": " Pronunciation",
    }
    for configs in (LANG_CONFIG, LANG_GRAMMAR_CONFIG):
        for language, cfg in configs.items():
            assert HISTORY_FIELD in cfg["all_fields"]
            for slot in range(1, 5):
                stem = "Example" if slot == 1 else f"Example{slot}"
                assert f"{stem}{suffixes[language]}" in cfg["all_fields"]
                assert f"{stem} Audio" in cfg["all_fields"]


def test_slot_state_counter_uses_current_position_and_total():
    history, _ = append_version(empty_history(), 4, _record("One"))
    history, state = append_version(history, 4, _record("Two"))
    assert state["active"] + 1 == 2
    assert len(slot_state(history, 4)["versions"]) == 2
