"""Pure regression contract for Bento Forge 18.1 AI Study Sessions."""

import json
from pathlib import Path

import pytest

from utils.ai_card_artifacts import create_card_artifact, artifact_to_factory_payload
from utils.ai_context_manager import prepare_study_context
from utils.ai_session_store import SESSION_SCHEMA_VERSION, StudySessionStore


ROOT = Path(__file__).resolve().parents[1]


def _english_card(front="opportunity"):
    return {"front": front, "meaning": "cơ hội", "cefr_level": "B1"}


def test_session_create_save_reload_rename_and_delete(tmp_path):
    path = tmp_path / "sessions.json"
    first = StudySessionStore(str(path))
    session = first.create_session(
        language="english", title="Opportunity", provider="openai", model="gpt-5.6-luna",
    )
    user = first.add_message(session["id"], role="user", content="How is it used?")
    first.add_message(session["id"], role="assistant", content="Use it for a favorable possibility.")
    first.rename_session(session["id"], "Opportunity / chance")

    restarted = StudySessionStore(str(path))
    restored = restarted.get_session(session["id"])
    assert restored["title"] == "Opportunity / chance"
    assert [item["role"] for item in restored["messages"]] == ["user", "assistant"]
    assert restored["messages"][0]["id"] == user["id"]
    assert restarted.delete_session(session["id"]) is True
    assert restarted.get_session(session["id"]) is None


def test_corrupt_store_is_ignored_and_next_write_recovers(tmp_path):
    path = tmp_path / "sessions.json"
    path.write_text("{broken", encoding="utf-8")
    store = StudySessionStore(str(path))
    assert store.list_sessions() == []
    store.create_session(language="japanese")
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == SESSION_SCHEMA_VERSION


def test_legacy_session_document_migrates_on_next_write(tmp_path):
    path = tmp_path / "sessions.json"
    path.write_text(json.dumps({
        "schema_version": 0,
        "sessions": [{
            "id": "legacy", "title": "Legacy", "language": "english",
            "messages": [{"role": "user", "type": "user", "content": "hello"}],
            "artifacts": [],
        }],
        "ui_state": {"dock_side": "left"},
    }), encoding="utf-8")
    store = StudySessionStore(str(path))
    assert store.get_session("legacy")["messages"][0]["content"] == "hello"
    store.rename_session("legacy", "Migrated")
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == SESSION_SCHEMA_VERSION


def test_store_retention_artifacts_and_secret_redaction(tmp_path):
    store = StudySessionStore(str(tmp_path / "sessions.json"), max_sessions=2, max_messages=10)
    for index in range(3):
        session = store.create_session(language="english", title=f"S{index}")
    assert [item["title"] for item in store.list_sessions()] == ["S2", "S1"]

    message = store.add_message(
        session["id"], role="user", content="api_key=unit-test-secret-value explain this",
        context_snapshot={"authorization": "Bearer secret", "front": "word"},
    )
    assert "unit-test-secret-value" not in message["content"]
    artifact = create_card_artifact(
        session_id=session["id"], language="english", kind="vocab",
        cards=[_english_card()], source_message_id=message["id"],
    )
    stored = store.add_artifact(session["id"], artifact)
    assert store.get_artifact(session["id"], stored["artifact_id"])["cards"] == [_english_card()]
    serialized = (tmp_path / "sessions.json").read_text(encoding="utf-8")
    assert "Bearer secret" not in serialized and "unit-test-secret-value" not in serialized


def test_store_enforces_total_byte_retention(tmp_path):
    path = tmp_path / "sessions.json"
    store = StudySessionStore(str(path), max_bytes=4_096, max_messages=50)
    session = store.create_session(language="english")
    for index in range(12):
        store.add_message(session["id"], role="user", content=f"{index}:" + "x" * 700)
    restored = store.get_session(session["id"])
    assert path.stat().st_size <= 4_096
    assert restored["messages"][-1]["content"].startswith("11:")
    assert len(restored["messages"]) < 12


def test_latest_message_edit_discards_later_assistant_without_branching(tmp_path):
    store = StudySessionStore(str(tmp_path / "sessions.json"))
    session = store.create_session(language="korean")
    store.add_message(session["id"], role="user", content="first")
    store.add_message(session["id"], role="assistant", content="answer")
    edited = store.replace_latest_user_message(session["id"], "edited")
    assert [item["content"] for item in edited["messages"]] == ["edited"]


def test_delete_latest_turn_removes_derived_reply_but_keeps_earlier_turns(tmp_path):
    store = StudySessionStore(str(tmp_path / "sessions.json"))
    session = store.create_session(language="english")
    for role, content in (
        ("user", "first"), ("assistant", "answer one"),
        ("user", "second"), ("assistant", "answer two"),
    ):
        store.add_message(session["id"], role=role, content=content)
    assert store.delete_latest_user_turn(session["id"]) is True
    restored = store.get_session(session["id"])
    assert [item["content"] for item in restored["messages"]] == ["first", "answer one"]


def test_context_short_session_and_card_toggle_are_session_local():
    session_a = {
        "summary": "", "messages": [
            {"role": "user", "content": "Earlier A", "type": "user"},
            {"role": "assistant", "content": "Answer A", "type": "assistant"},
        ],
    }
    snapshot = {"side": "answer", "front": "affect", "meaning": "ảnh hưởng", "deck": "English"}
    prepared = prepare_study_context(
        session_a, current_user_message="Current A", system_prompt="Tutor", model="unknown",
        session_max_tokens=4_000, card_context=snapshot, use_card_context=True,
    )
    text = "\n".join(item["content"] for item in prepared.messages)
    assert "Earlier A" in text and "Answer A" in text and "affect" in text
    assert "Current A" in text

    session_b = {"summary": "", "messages": []}
    other = prepare_study_context(
        session_b, current_user_message="Current B", system_prompt="Tutor", model="unknown",
        session_max_tokens=4_000, card_context=snapshot, use_card_context=False,
    )
    other_text = "\n".join(item["content"] for item in other.messages)
    assert "Earlier A" not in other_text and "affect" not in other_text


def test_long_context_compacts_old_messages_and_respects_hard_cap():
    messages = []
    for index in range(80):
        role = "user" if index % 2 == 0 else "assistant"
        messages.append({"role": role, "type": role, "content": f"message {index} " + "x" * 350})
    prepared = prepare_study_context(
        {"summary": "", "messages": messages},
        current_user_message="What matters now?", system_prompt="Concise tutor",
        model="unknown-model", session_max_tokens=2_400, max_output_tokens=500,
    )
    assert prepared.compacted_message_count > 0
    assert prepared.summary
    assert prepared.estimated_tokens <= 2_400 - 500 - 768 - 512
    joined = "\n".join(item["content"] for item in prepared.messages)
    assert "message 79" in joined and "message 20 " not in joined


def test_question_side_context_omits_answer_fields():
    prepared = prepare_study_context(
        {"summary": "", "messages": []}, current_user_message="Hint", system_prompt="Tutor",
        model="gpt-5.6-luna", session_max_tokens=4_000, use_card_context=True,
        card_context={"side": "question", "front": "affect", "meaning": "ảnh hưởng"},
    )
    text = "\n".join(item["content"] for item in prepared.messages)
    assert "front: affect" in text
    assert "meaning:" not in text
    assert "do not reveal the answer" in text


def test_artifact_round_trip_never_calls_ai_and_rejects_bad_payload():
    artifact = create_card_artifact(
        session_id="session-a", language="english", kind="vocab",
        cards=[_english_card()], source_message_id="msg-a",
    )
    assert artifact_to_factory_payload(artifact) == ("english", "vocab", [_english_card()])
    with pytest.raises(ValueError):
        create_card_artifact(
            session_id="session-a", language="english", kind="vocab",
            cards=[{"front": "broken"}], source_message_id="msg-a",
        )


def test_ui_state_persists_dock_geometry_and_last_session(tmp_path):
    path = tmp_path / "sessions.json"
    store = StudySessionStore(str(path))
    session = store.create_session(language="chinese")
    store.update_ui_state(
        dock_side="left", floating=True, floating_x=40, floating_y=50,
        floating_width=480, floating_height=720, collapsed=True,
        last_session_id=session["id"], visible=False,
    )
    assert StudySessionStore(str(path)).get_ui_state() == {
        "dock_side": "left", "floating": True, "floating_x": 40, "floating_y": 50,
        "floating_width": 480, "floating_height": 720, "collapsed": True,
        "last_session_id": session["id"], "visible": False,
    }


def test_companion_source_keeps_reviewer_secondary_and_card_mode_one_shot():
    companion = (ROOT / "ui" / "ai_companion.py").read_text(encoding="utf-8")
    reviewer = (ROOT / "hooks" / "reviewer.py").read_text(encoding="utf-8")
    factory = (ROOT / "ui" / "factory_dialog.py").read_text(encoding="utf-8")
    assert "class AiCompanionDock(QDockWidget)" in companion
    assert "class AiStudySessionDialog(QDialog)" in companion
    assert "DockWidgetFloatable" in companion and "DockWidgetClosable" in companion
    assert "self.cbo_mode.setCurrentIndex(0)" in companion
    assert "self._store.get_session(self._pending_session_id)" in companion
    assert "tools.addAction(action)" in companion
    assert "self.hide()" in companion and "web.setFocus()" in companion
    assert "bento_forge_ai:open" in reviewer
    assert "show_ai_study_dialog" in factory
    factory_chat = factory.split("def _ai_chat(self):", 1)[1].split("def _ai_chat_legacy", 1)[0]
    assert "show_ai_study_dialog" in factory_chat
    assert "show_ai_companion" not in factory_chat
    assert "#f8f4ec" not in companion and "#fffdf9" not in companion
    assert "def load_card_artifact" in factory
    artifact_loader = factory.split("def load_card_artifact", 1)[1].split("def ", 1)[0]
    assert "artifact_to_factory_payload" in artifact_loader
    assert "chat_with_ai" not in artifact_loader
