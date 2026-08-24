"""Reviewer-only local learning checkpoint contracts."""

from pathlib import Path

import pytest

from utils.ai_coaching_loop import (
    build_reviewer_checkpoint, latest_reviewer_checkpoint,
)
from utils.ai_context_manager import compact_session_summary, prepare_study_context
from utils.ai_session_store import StudySessionStore
from utils.i18n import t


ROOT = Path(__file__).resolve().parents[1]


def _card(card_id="42", mode="qa", language="english", side="question"):
    return {
        "card_id": card_id,
        "study_mode": mode,
        "language": language,
        "side": side,
        "front": "opportunity",
        "meaning": "a favorable chance",
    }


def _message(checkpoint, *, message_type="system_internal", role="system"):
    return {
        "id": "checkpoint-message",
        "role": role,
        "type": message_type,
        "content": "local checkpoint",
        "context_snapshot": checkpoint,
    }


@pytest.mark.parametrize("outcome", ["understood", "needs_practice"])
def test_checkpoint_is_bounded_to_reviewer_card_and_study_mode(outcome):
    checkpoint = build_reviewer_checkpoint(_card(side="answer"), outcome)

    assert checkpoint == {
        "checkpoint_schema_version": 1,
        "workspace": "reviewer",
        "outcome": outcome,
        "language": "english",
        "card_id": "42",
        "study_mode": "qa",
        "side": "answer",
    }
    assert "front" not in checkpoint and "meaning" not in checkpoint


@pytest.mark.parametrize(
    ("context", "outcome"),
    [
        (None, "understood"),
        (_card(card_id=""), "understood"),
        (_card(mode="unknown"), "understood"),
        (_card(language="unknown"), "understood"),
        (_card(), "mastered_forever"),
    ],
)
def test_checkpoint_creation_fails_closed_without_owned_identity(context, outcome):
    with pytest.raises(ValueError):
        build_reviewer_checkpoint(context, outcome)


def test_latest_checkpoint_uses_newest_exact_card_and_mode_only():
    understood = build_reviewer_checkpoint(_card(), "understood")
    needs_practice = build_reviewer_checkpoint(_card(), "needs_practice")
    other_card = build_reviewer_checkpoint(_card(card_id="99"), "needs_practice")
    other_mode = build_reviewer_checkpoint(_card(mode="wb"), "needs_practice")
    messages = [
        _message(understood),
        _message(other_card),
        _message(other_mode),
        _message(needs_practice),
    ]

    assert latest_reviewer_checkpoint(messages, _card())["outcome"] == "needs_practice"
    assert latest_reviewer_checkpoint(messages, _card(card_id="99"))["card_id"] == "99"
    assert latest_reviewer_checkpoint(messages, _card(mode="lg")) is None


def test_latest_checkpoint_ignores_malformed_cross_workspace_or_visible_messages():
    valid = build_reviewer_checkpoint(_card(), "understood")
    wrong_workspace = dict(valid, workspace="forge")
    wrong_schema = dict(valid, checkpoint_schema_version=99)
    messages = [
        _message(valid, message_type="assistant"),
        _message(valid, role="user"),
        _message(wrong_workspace),
        _message(wrong_schema),
    ]

    assert latest_reviewer_checkpoint(messages, _card()) is None
    assert latest_reviewer_checkpoint(messages, None) is None


def test_checkpoint_persists_but_never_enters_model_context_or_summary(tmp_path):
    store = StudySessionStore(str(tmp_path / "sessions.json"))
    session = store.create_session(language="english")
    store.add_message(session["id"], role="user", content="Give me a hint")
    checkpoint = build_reviewer_checkpoint(_card(), "needs_practice")
    stored = store.add_message(
        session["id"], role="system", content="PRIVATE CHECKPOINT MARKER",
        message_type="system_internal", context_snapshot=checkpoint,
    )
    restored = StudySessionStore(str(tmp_path / "sessions.json")).get_session(session["id"])
    restored["messages"].append({
        "id": "malformed-internal", "role": "user", "type": "system_internal",
        "content": "MALFORMED PRIVATE MARKER",
    })
    prepared = prepare_study_context(
        restored,
        current_user_message="Quiz me",
        system_prompt="Reviewer coach",
        model="unknown-model",
        session_max_tokens=4_000,
    )

    assert stored["type"] == "system_internal"
    assert restored["messages"][-2]["context_snapshot"] == checkpoint
    assert "PRIVATE CHECKPOINT MARKER" not in "\n".join(
        item["content"] for item in prepared.messages
    )
    assert "MALFORMED PRIVATE MARKER" not in "\n".join(
        item["content"] for item in prepared.messages
    )
    assert "PRIVATE CHECKPOINT MARKER" not in compact_session_summary(restored["messages"])


def test_reviewer_checkpoint_ui_is_explicit_zero_ai_and_forge_hidden():
    companion = (ROOT / "ui" / "ai_companion.py").read_text(encoding="utf-8")
    start = companion.index("    def mark_coaching_outcome")
    end = companion.index("    def send_message", start)
    action = companion[start:end]

    assert 'widget.setVisible(self._workspace == "reviewer")' in companion
    assert 'message_type="system_internal"' in action
    assert 'self._set_quick_prompt(t("study_prompt_check"))' in action
    assert "self.back_to_review()" in action
    assert "chat_with_ai" not in action and "start_chat" not in action
    assert all(forbidden not in action for forbidden in (
        "mw.col.sched", "answer_card", "set_due", "update_note",
    ))
    assert t("study_coach_understood", lang="vi")
    assert t("study_coach_understood", lang="en")
