"""Pure regression contract for Bento Forge 18.1 AI Study Sessions."""

import json
from pathlib import Path

import pytest

from utils.ai_card_artifacts import (
    ARTIFACT_COMPATIBILITY_CURRENT, ARTIFACT_COMPATIBILITY_STALE,
    artifact_is_compatible, artifact_label, artifact_to_factory_payload,
    create_card_artifact,
)
from utils.ai_context_manager import compact_session_summary, prepare_study_context
from utils.ai_output_validation import AI_OUTPUT_SCHEMA_VERSION
from utils.ai_session_store import (
    SESSION_SCHEMA_VERSION, StudySessionStore, _serialized_size,
)


ROOT = Path(__file__).resolve().parents[1]


def _english_card(front="opportunity"):
    return {
        "front": front, "meaning": "opportunity", "cefr_level": "B1",
        "example": f"This is an example with {front}.",
    }


def _seed_persisted_artifact(path):
    store = StudySessionStore(str(path))
    session = store.create_session(language="english", title="Artifact history")
    source = store.add_message(session["id"], role="user", content="Create this card")
    artifact = create_card_artifact(
        session_id=session["id"], language="english", kind="vocab",
        cards=[_english_card()], source_message_id=source["id"],
    )
    stored = store.add_artifact(session["id"], artifact)
    store.add_message(
        session["id"], role="assistant", content="Artifact ready",
        message_type="artifact_reference", artifact_id=stored["artifact_id"],
    )
    return store, session, stored


def _retention_document(path, *, artifact_count=1, stale=False, source_size=20):
    store = StudySessionStore(str(path))
    session = store.create_session(language="english", title="Retention")
    source = store.add_message(
        session["id"], role="user", content="source:" + "s" * source_size,
    )
    artifacts = []
    for index in range(artifact_count):
        artifact = create_card_artifact(
            session_id=session["id"], language="english", kind="vocab",
            cards=[_english_card(f"sense-{index}")], source_message_id=source["id"],
        )
        artifacts.append(store.add_artifact(session["id"], artifact))
    session = store.get_session(session["id"])
    if stale:
        for artifact in session["artifacts"]:
            artifact["schema_version"] -= 1
            artifact["compatibility"] = ARTIFACT_COMPATIBILITY_STALE
    return {
        "schema_version": SESSION_SCHEMA_VERSION,
        "sessions": [session],
        "ui_state": {},
    }, session["id"], source["id"], artifacts


def _long_messages(count=24, *, start=0, prefix="message", width=240, id_prefix="msg"):
    messages = []
    for index in range(start, start + count):
        role = "user" if index % 2 == 0 else "assistant"
        messages.append({
            "id": f"{id_prefix}-{index:03d}",
            "role": role,
            "type": role,
            "content": f"{prefix} {index} " + "x" * width,
        })
    return messages


def _prepare_long(session, current="What matters now?"):
    return prepare_study_context(
        session,
        current_user_message=current,
        system_prompt="Concise tutor",
        model="unknown-model",
        session_max_tokens=2_400,
        max_output_tokens=500,
    )


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
            "summary": "Learner chose the formal sense.",
            "artifacts": [],
        }],
        "ui_state": {"dock_side": "left"},
    }), encoding="utf-8")
    store = StudySessionStore(str(path))
    legacy = store.get_session("legacy")
    assert legacy["messages"][0]["content"] == "hello"
    assert legacy["summary"] == "Learner chose the formal sense."
    assert legacy["summary_through_message_id"] == ""
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


@pytest.mark.parametrize("stale", [False, True])
def test_bounded_retention_prunes_unreferenced_messages_before_artifact_sources(
    tmp_path, stale,
):
    path = tmp_path / "bounded.json"
    document, session_id, source_id, artifacts = _retention_document(
        tmp_path / "seed.json", artifact_count=2, stale=stale,
    )
    session = document["sessions"][0]
    session["messages"].extend({
        "id": f"unreferenced-{index}", "role": "assistant", "type": "assistant",
        "content": f"discard-{index}:" + "x" * 1_800,
        "created_at": f"2026-08-21T00:00:0{index}+00:00",
    } for index in range(4))
    store = StudySessionStore(str(path), max_bytes=4_096, max_messages=50)

    store._save(document)
    restored = store.get_session(session_id)

    assert path.stat().st_size <= 4_096
    assert {item["artifact_id"] for item in restored["artifacts"]} == {
        item["artifact_id"] for item in artifacts
    }
    assert all(
        item["compatibility"] == (
            ARTIFACT_COMPATIBILITY_STALE if stale else ARTIFACT_COMPATIBILITY_CURRENT
        )
        for item in restored["artifacts"]
    )
    assert source_id in {item["id"] for item in restored["messages"]}
    assert restored["artifacts"][0]["source_message_id"] == source_id
    assert store.list_sessions()[0]["artifact_count"] == 2
    assert store.list_sessions()[0]["message_count"] == len(restored["messages"])


def test_shared_source_stays_until_last_artifact_is_deterministically_pruned(tmp_path):
    path = tmp_path / "shared-source.json"
    document, session_id, source_id, artifacts = _retention_document(
        tmp_path / "seed.json", artifact_count=2,
    )
    for artifact in document["sessions"][0]["artifacts"]:
        artifact["cards"][0]["usage_note"] = "x" * 3_000
    after_oldest_artifact = json.loads(json.dumps(document))
    after_oldest_artifact["sessions"][0]["artifacts"].pop(0)
    max_bytes = max(4_096, _serialized_size(after_oldest_artifact))
    store = StudySessionStore(str(path), max_bytes=max_bytes, max_messages=50)

    store._save(document)
    restored = store.get_session(session_id)

    assert [item["artifact_id"] for item in restored["artifacts"]] == [
        artifacts[1]["artifact_id"],
    ]
    assert source_id in {item["id"] for item in restored["messages"]}
    assert restored["artifacts"][0]["source_message_id"] == source_id

    stable_document = store._load()
    before = json.loads(json.dumps(stable_document))
    store._save(stable_document)
    assert store._load() == before


def test_forced_artifact_removal_releases_source_without_orphan_or_size_overflow(tmp_path):
    path = tmp_path / "forced.json"
    document, session_id, _, artifacts = _retention_document(
        tmp_path / "seed.json", source_size=7_000,
    )
    store = StudySessionStore(str(path), max_bytes=4_096, max_messages=50)

    store._save(document)
    restored = store.get_session(session_id)

    assert path.stat().st_size <= 4_096
    assert restored["artifacts"] == []
    assert restored["messages"] == []
    assert store.get_artifact(session_id, artifacts[0]["artifact_id"]) is None
    assert store.list_sessions()[0]["artifact_count"] == 0
    assert store.list_sessions()[0]["message_count"] == 0


def test_message_count_retention_also_protects_artifact_source(tmp_path):
    path = tmp_path / "message-count.json"
    document, session_id, source_id, artifacts = _retention_document(tmp_path / "seed.json")
    session = document["sessions"][0]
    session["messages"].extend({
        "id": f"recent-{index}", "role": "assistant", "type": "assistant",
        "content": f"recent {index}", "created_at": "2026-08-21T00:00:00+00:00",
    } for index in range(15))
    store = StudySessionStore(str(path), max_messages=10)

    store.save_session(session)
    restored = store.get_session(session_id)

    assert len(restored["messages"]) == 10
    assert source_id in {item["id"] for item in restored["messages"]}
    assert [item["artifact_id"] for item in restored["artifacts"]] == [
        artifacts[0]["artifact_id"],
    ]


def test_corrupt_persisted_provenance_remains_rejected(tmp_path):
    path = tmp_path / "corrupt-provenance.json"
    document, session_id, source_id, _ = _retention_document(tmp_path / "seed.json")
    session = document["sessions"][0]
    session["messages"] = [
        item for item in session["messages"] if item["id"] != source_id
    ]
    StudySessionStore(str(path))._save(document)

    assert StudySessionStore(str(path)).get_session(session_id)["artifacts"] == []


def test_retention_and_reload_never_call_ai_or_network(monkeypatch, tmp_path):
    from utils import ai_extractor, grammar_ai

    calls = []
    monkeypatch.setattr(
        ai_extractor, "_http_post_json",
        lambda *args, **kwargs: calls.append(("network", args, kwargs)),
    )
    monkeypatch.setattr(
        grammar_ai, "generate_grammar_examples",
        lambda *args, **kwargs: calls.append(("grammar", args, kwargs)),
    )
    path = tmp_path / "no-ai.json"
    document, session_id, source_id, _ = _retention_document(tmp_path / "seed.json")
    document["sessions"][0]["messages"].append({
        "id": "discard", "role": "assistant", "type": "assistant",
        "content": "x" * 6_000, "created_at": "2026-08-21T00:00:00+00:00",
    })
    store = StudySessionStore(str(path), max_bytes=4_096, max_messages=50)

    store._save(document)
    restored = store.get_session(session_id)

    assert source_id in {item["id"] for item in restored["messages"]}
    assert restored["artifacts"]
    assert calls == []


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
    messages = _long_messages(80, width=350)
    prepared = prepare_study_context(
        {"summary": "", "messages": messages},
        current_user_message="What matters now?", system_prompt="Concise tutor",
        model="unknown-model", session_max_tokens=2_400, max_output_tokens=500,
    )
    assert prepared.compacted_message_count > 0
    assert prepared.summary
    assert prepared.summary_through_message_id
    assert prepared.estimated_tokens <= 2_400 - 500 - 768 - 512
    joined = "\n".join(item["content"] for item in prepared.messages)
    assert "message 79" in joined and "message 20 " not in joined


def test_first_compaction_creates_summary_and_exact_progress_marker():
    messages = _long_messages()
    prepared = _prepare_long({"summary": "", "messages": messages})

    assert prepared.summary
    assert prepared.compacted_message_count > 0
    assert prepared.summary_through_message_id in {item["id"] for item in messages}
    marker_index = next(
        index for index, item in enumerate(messages)
        if item["id"] == prepared.summary_through_message_id
    )
    assert marker_index == prepared.compacted_message_count - 1
    assert marker_index < len(messages) - 1


def test_second_request_does_not_refold_messages_before_marker():
    messages = _long_messages()
    first = _prepare_long({"summary": "", "messages": messages})
    second = _prepare_long({
        "summary": first.summary,
        "summary_through_message_id": first.summary_through_message_id,
        "messages": messages,
    }, current="Continue the same topic.")

    assert second.compacted_message_count == 0
    assert second.summary == first.summary
    assert second.summary_through_message_id == first.summary_through_message_id


def test_newly_old_messages_are_folded_once_then_marker_stops():
    original = _long_messages()
    first = _prepare_long({"summary": "", "messages": original})
    added = _long_messages(8, start=len(original), prefix="correction delta")
    expanded = original + added
    second = _prepare_long({
        "summary": first.summary,
        "summary_through_message_id": first.summary_through_message_id,
        "messages": expanded,
    }, current="Apply the correction.")
    third = _prepare_long({
        "summary": second.summary,
        "summary_through_message_id": second.summary_through_message_id,
        "messages": expanded,
    }, current="Apply the correction again.")

    assert second.compacted_message_count > 0
    assert second.summary_through_message_id != first.summary_through_message_id
    assert "correction delta" in second.summary
    assert third.compacted_message_count == 0
    assert third.summary == second.summary


def test_recent_unsummarized_messages_remain_raw_and_marker_does_not_cross_them():
    messages = _long_messages()
    prepared = _prepare_long({"summary": "", "messages": messages})
    raw = "\n".join(
        item["content"] for item in prepared.messages if item["role"] != "system"
    )
    marker_index = next(
        index for index, item in enumerate(messages)
        if item["id"] == prepared.summary_through_message_id
    )

    assert messages[-1]["content"] in raw
    assert messages[marker_index + 1]["content"] in raw
    assert messages[marker_index]["content"] not in raw


def test_legacy_summary_infers_boundary_without_recursive_refold():
    messages = _long_messages()
    legacy_summary = "Tutor: agreed correction is already retained"
    prepared = _prepare_long({"summary": legacy_summary, "messages": messages})

    assert prepared.summary == legacy_summary
    assert prepared.summary_through_message_id
    assert prepared.compacted_message_count == 0
    assert prepared.summary.count("agreed correction") == 1


def test_summary_marker_and_content_are_session_local():
    messages_a = _long_messages(prefix="SESSION-A", id_prefix="a")
    messages_b = _long_messages(prefix="SESSION-B", id_prefix="b")
    prepared_a = _prepare_long({"summary": "", "messages": messages_a})
    prepared_b = _prepare_long({"summary": "", "messages": messages_b})

    assert "SESSION-A" in prepared_a.summary and "SESSION-B" not in prepared_a.summary
    assert "SESSION-B" in prepared_b.summary and "SESSION-A" not in prepared_b.summary
    assert prepared_a.summary_through_message_id.startswith("a-")
    assert prepared_b.summary_through_message_id.startswith("b-")


def test_summary_size_stays_bounded_and_prefers_new_tail():
    messages = _long_messages(80, prefix="correction latest", width=400)
    summary = compact_session_summary(
        messages,
        existing_summary="old summary " * 800,
        max_chars=4_000,
    )

    assert len(summary) <= 4_000
    assert "correction latest 79" in summary


def test_correction_and_artifact_references_survive_compaction():
    messages = _long_messages(8, prefix="incidental")
    messages.extend([
        {
            "id": "msg-correction", "role": "assistant", "type": "assistant",
            "content": "Correction: use opportunity with to + infinitive.",
        },
        {
            "id": "msg-artifact", "role": "assistant", "type": "artifact_reference",
            "content": "Artifact created: English Vocabulary · 3 cards.",
        },
    ])
    summary = compact_session_summary(messages)

    assert "Correction: use opportunity" in summary
    assert "Artifact created" in summary


def test_store_persists_summary_marker_and_edit_clears_both(tmp_path):
    store = StudySessionStore(str(tmp_path / "sessions.json"))
    session = store.create_session(language="english")
    first = store.add_message(session["id"], role="user", content="first")
    store.add_message(session["id"], role="assistant", content="reply")
    store.update_summary(session["id"], "Learner: first", first["id"])

    restored = StudySessionStore(str(tmp_path / "sessions.json")).get_session(session["id"])
    assert restored["summary_through_message_id"] == first["id"]
    edited = store.replace_latest_user_message(session["id"], "edited")
    assert edited["summary"] == ""
    assert edited["summary_through_message_id"] == ""


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


def test_current_artifact_survives_store_reload_unchanged_and_remains_usable(tmp_path):
    path = tmp_path / "sessions.json"
    _, session, stored = _seed_persisted_artifact(path)

    restored = StudySessionStore(str(path)).get_artifact(
        session["id"], stored["artifact_id"],
    )

    assert restored == stored
    assert restored["compatibility"] == ARTIFACT_COMPATIBILITY_CURRENT
    assert artifact_is_compatible(restored)
    assert artifact_to_factory_payload(restored) == (
        "english", "vocab", [_english_card()],
    )


@pytest.mark.parametrize(
    "schema_version",
    [AI_OUTPUT_SCHEMA_VERSION - 1, AI_OUTPUT_SCHEMA_VERSION + 1],
)
def test_unsupported_artifact_survives_reload_and_save_as_read_only_stale(
    tmp_path, schema_version,
):
    path = tmp_path / "sessions.json"
    _, session, stored = _seed_persisted_artifact(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    persisted = document["sessions"][0]["artifacts"][0]
    persisted["schema_version"] = schema_version
    persisted.pop("compatibility", None)
    original_cards = persisted["cards"]
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

    restarted = StudySessionStore(str(path))
    restored_session = restarted.get_session(session["id"])
    restored = restarted.get_artifact(session["id"], stored["artifact_id"])

    assert restored_session["artifacts"] == [restored]
    assert restarted.list_sessions()[0]["artifact_count"] == 1
    assert restored["artifact_id"] == stored["artifact_id"]
    assert restored["session_id"] == session["id"]
    assert restored["source_message_id"] == stored["source_message_id"]
    assert restored["created_at"] == stored["created_at"]
    assert restored["language"] == "english"
    assert restored["kind"] == "vocab"
    assert restored["schema_version"] == schema_version
    assert restored["cards"] == original_cards
    assert restored["compatibility"] == ARTIFACT_COMPATIBILITY_STALE
    assert not artifact_is_compatible(restored)
    with pytest.raises(ValueError, match="unsupported"):
        artifact_to_factory_payload(restored)

    restarted.save_session(restored_session)
    round_tripped = StudySessionStore(str(path)).get_artifact(
        session["id"], stored["artifact_id"],
    )
    assert round_tripped == restored


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [("cards", "not-a-list"), ("schema_version", "not-an-integer")],
)
def test_structurally_corrupt_persisted_artifact_is_still_rejected(
    tmp_path, field, bad_value,
):
    path = tmp_path / "sessions.json"
    _, session, _ = _seed_persisted_artifact(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["sessions"][0]["artifacts"][0][field] = bad_value
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

    restored = StudySessionStore(str(path)).get_session(session["id"])

    assert restored["artifacts"] == []


def test_loading_and_reviewing_stale_snapshot_never_calls_ai_or_network(
    monkeypatch, tmp_path,
):
    from utils import ai_extractor, grammar_ai

    calls = []
    monkeypatch.setattr(
        ai_extractor, "_http_post_json",
        lambda *args, **kwargs: calls.append(("network", args, kwargs)),
    )
    monkeypatch.setattr(
        grammar_ai, "generate_grammar_examples",
        lambda *args, **kwargs: calls.append(("grammar", args, kwargs)),
    )
    path = tmp_path / "sessions.json"
    _, session, stored = _seed_persisted_artifact(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["sessions"][0]["artifacts"][0]["schema_version"] -= 1
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

    stale = StudySessionStore(str(path)).get_artifact(session["id"], stored["artifact_id"])
    review_snapshot = json.dumps(stale["cards"], ensure_ascii=False, indent=2)

    assert artifact_label(stale) == "English Vocabulary · 1"
    assert "opportunity" in review_snapshot
    with pytest.raises(ValueError, match="unsupported"):
        artifact_to_factory_payload(stale)
    assert calls == []


def test_companion_surfaces_stale_artifact_and_disables_forge_action():
    companion = (ROOT / "ui" / "ai_companion.py").read_text(encoding="utf-8")

    assert 'for artifact in reversed(session["artifacts"])' in companion
    assert 't("study_artifact_stale_label", label=label)' in companion
    assert 'self.btn_forge.setEnabled(compatible)' in companion
    assert 'QLabel(t("study_artifact_stale_review"))' in companion
    assert 'showInfo(t("study_artifact_stale_open_error"))' in companion


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
    assert "aria-label" in reviewer
    assert "getElementById('bento-forge-ai-action')" in reviewer
    assert "#fffaf0" not in reviewer and "#4d4338" not in reviewer and "#c9bca8" not in reviewer
    assert "color: inherit" in reviewer and "prefers-color-scheme: dark" in reviewer
    assert "show_ai_study_dialog" in factory
    factory_chat = factory.split("def _ai_chat(self):", 1)[1].split("def _ai_chat_legacy", 1)[0]
    assert "show_ai_study_dialog" in factory_chat
    assert "show_ai_companion" not in factory_chat
    assert "#f8f4ec" not in companion and "#fffdf9" not in companion
    assert "def load_card_artifact" in factory
    artifact_loader = factory.split("def load_card_artifact", 1)[1].split("def ", 1)[0]
    assert "artifact_to_factory_payload" in artifact_loader
    assert "chat_with_ai" not in artifact_loader
    assert "forge-artifact://review/" in companion
    assert "forge-artifact://open/" in companion
    assert "self.transcript.setOpenLinks(False)" in companion
    assert "self.review_artifact()" in companion and "self.open_artifact_in_forge()" in companion
    extractor = (ROOT / "utils" / "ai_extractor.py").read_text(encoding="utf-8")
    assert '"session_summary_through_message_id": context_summary_marker' in extractor
