"""V18.2 request-scoped Reviewer/Forge workspace contracts."""

from pathlib import Path
import json

import pytest

from utils.ai_context_manager import prepare_study_context
from utils.ai_session_store import StudySessionStore
from utils.ai_study_prompts import build_study_prompt
from utils import ai_extractor
from utils.ai_workspace import (
    build_workspace_request_context, get_workspace_policy, resolve_workspace,
)
from utils.i18n import t


def _snapshot(mode="qa", side="question"):
    return {
        "language": "english",
        "side": side,
        "study_mode": mode,
        "front": "TARGET",
        "meaning": "MEANING",
        "furigana": "FURIGANA",
        "pinyin": "PINYIN",
        "romanization": "ROMANIZATION",
        "example": "HIDDEN EXAMPLE",
    }


def _request(workspace, token, **kwargs):
    defaults = {
        "language": "english",
        "user_instruction": "Help with this request",
        "request_token": token,
    }
    defaults.update(kwargs)
    return build_workspace_request_context(workspace=workspace, **defaults)


def test_workspace_policy_is_explicit_and_actions_are_distinct():
    reviewer = get_workspace_policy("reviewer")
    forge = get_workspace_policy("forge")

    assert resolve_workspace(" REVIEWER ") == "reviewer"
    assert reviewer.workspace == "reviewer"
    assert forge.workspace == "forge"
    assert reviewer.allows_card_context and not reviewer.allows_source_context
    assert forge.allows_source_context and not forge.allows_card_context
    assert reviewer.quick_actions != forge.quick_actions
    assert not set(reviewer.quick_actions).intersection(forge.quick_actions)
    with pytest.raises(ValueError, match="workspace"):
        resolve_workspace("auto")


@pytest.mark.parametrize(
    ("mode", "present", "absent"),
    [
        ("qa", {"front"}, {"meaning", "example"}),
        ("vn", {"meaning"}, {"front", "furigana", "pinyin", "romanization"}),
        ("wb", {"meaning"}, {"front", "furigana", "pinyin", "romanization"}),
        ("pron", {"front", "meaning"}, {"furigana", "pinyin", "romanization"}),
        ("lg", {"meaning", "furigana", "pinyin", "romanization"}, {"front"}),
    ],
)
def test_reviewer_question_request_preserves_mode_aware_no_leakage(
    mode, present, absent,
):
    request = _request(
        "reviewer", f"reviewer-{mode}",
        card_context=_snapshot(mode), use_card_context=True,
    )

    assert request.workspace == "reviewer"
    assert request.use_card_context
    assert present <= set(request.card_context)
    assert not absent.intersection(request.card_context)
    assert not request.source_attached


def test_reviewer_context_disabled_is_explicit_and_answer_side_is_allowed():
    disabled = _request(
        "reviewer", "reviewer-off",
        card_context=_snapshot(), use_card_context=False,
    )
    answer = _request(
        "reviewer", "reviewer-answer",
        card_context=_snapshot(side="answer"), use_card_context=True,
    )

    assert not disabled.use_card_context
    assert disabled.card_context == {}
    assert {"front", "meaning", "example"} <= set(answer.card_context)


def test_forge_request_is_canonical_source_explicit_and_never_owns_a_card():
    request = _request(
        "forge", "forge-source",
        language="en", learning_mode="language", lane="grammar",
        source_text="  A source sentence.  ",
        card_context=_snapshot(side="answer"), use_card_context=True,
    )

    assert request.workspace == "forge"
    assert request.language == "english"
    assert request.learning_mode == "language"
    assert request.lane == "grammar"
    assert request.source_text == "A source sentence."
    assert request.source_attached
    assert request.card_context == {}
    assert not request.use_card_context
    assert request.to_snapshot()["request_token"] == "forge-source"


def test_forge_empty_source_and_knowledge_workflow_are_honest():
    request = _request(
        "forge", "forge-empty", learning_mode="knowledge", lane="grammar",
        source_text="",
    )

    assert request.lane == "knowledge"
    assert not request.source_attached
    assert request.to_snapshot()["source_chars"] == 0


def test_workspace_prompt_owner_is_explicit_and_card_contract_stays_canonical():
    reviewer = build_study_prompt(
        "english", None, english_ui=True, workspace="reviewer",
    )
    forge = build_study_prompt(
        "english", None, english_ui=True, workspace="forge",
    )
    forge_card = build_study_prompt(
        "english", "grammar", english_ui=True, workspace="forge",
    )

    assert "return to Reviewer" in reviewer
    assert "current request" in forge
    assert "never claim access to a Reviewer card" in forge
    assert "ONLY SCHEMA:" in forge_card
    assert "complete Quality V2 contract" in forge_card
    assert "ONLY SCHEMA:" not in forge


def test_chat_boundary_rejects_workspace_or_language_provenance_mismatch():
    reviewer = _request("reviewer", "reviewer-owned")
    with pytest.raises(ValueError, match="ownership"):
        ai_extractor.chat_with_ai(
            "Help with this request", lang="english", workspace="forge",
            workspace_request=reviewer,
        )
    with pytest.raises(ValueError, match="language"):
        ai_extractor.chat_with_ai(
            "Help with this request", lang="japanese", workspace="reviewer",
            workspace_request=reviewer,
        )


def test_forge_chat_payload_contains_only_current_request_source(monkeypatch):
    request = _request(
        "forge", "forge-payload", user_instruction="Analyze it",
        source_text="Explicit source marker", lane="grammar",
        card_context=_snapshot(side="answer"), use_card_context=True,
    )
    captured = {}

    def fake_post(_url, payload, _headers, **_kwargs):
        captured["messages"] = payload["messages"]
        return json.dumps({"choices": [{"message": {"content": "Analysis"}}]})

    monkeypatch.setattr(ai_extractor, "_http_post_json", fake_post)
    result = ai_extractor.chat_with_ai(
        "Analyze it",
        lang="english",
        workspace="forge",
        workspace_request=request,
        study_session={"messages": [], "summary": ""},
        anki_context=_snapshot(side="answer"),
        use_card_context=True,
        runtime_config={
            "api_key": "test-key", "api_base": "https://example.test/v1",
            "model": "unknown", "temperature": 0.2, "max_tokens": 512,
            "session_max_tokens": 4_000,
        },
    )
    payload_text = "\n".join(item["content"] for item in captured["messages"])

    assert result["reply"] == "Analysis"
    assert "Explicit source marker" in payload_text
    assert "current_card: none" in payload_text
    assert "TARGET" not in payload_text


def test_same_session_switches_workspaces_without_request_context_bleed(tmp_path):
    store = StudySessionStore(str(tmp_path / "sessions.json"))
    session = store.create_session(language="english")
    reviewer = _request(
        "reviewer", "reviewer-one", user_instruction="Hint please",
        card_context=_snapshot("qa"), use_card_context=True,
    )
    forge = _request(
        "forge", "forge-one", user_instruction="Analyze it",
        source_text="Source-only marker", lane="vocab",
    )
    reviewer_again = _request(
        "reviewer", "reviewer-two", user_instruction="Quiz me",
        card_context=_snapshot("vn"), use_card_context=False,
    )

    prepared_reviewer = prepare_study_context(
        session, current_user_message=reviewer.user_instruction,
        system_prompt="Reviewer prompt", model="unknown", session_max_tokens=4_000,
        workspace_request=reviewer,
    )
    prepared_forge = prepare_study_context(
        session, current_user_message=forge.user_instruction,
        system_prompt="Forge prompt", model="unknown", session_max_tokens=4_000,
        workspace_request=forge,
    )
    prepared_reviewer_again = prepare_study_context(
        session, current_user_message=reviewer_again.user_instruction,
        system_prompt="Reviewer prompt", model="unknown", session_max_tokens=4_000,
        workspace_request=reviewer_again,
    )
    first_text = "\n".join(item["content"] for item in prepared_reviewer.messages)
    forge_text = "\n".join(item["content"] for item in prepared_forge.messages)
    last_text = "\n".join(item["content"] for item in prepared_reviewer_again.messages)

    assert "TARGET" in first_text and "MEANING" not in first_text
    assert "Source-only marker" in forge_text and "current_card: none" in forge_text
    assert "TARGET" not in forge_text
    assert "Source-only marker" not in last_text
    assert "no current-card context was attached" in last_text


def test_request_provenance_is_optional_and_v1811_sessions_still_reload(tmp_path):
    path = tmp_path / "sessions.json"
    store = StudySessionStore(str(path))
    session = store.create_session(language="english")
    request = _request(
        "forge", "forge-persisted", source_text="Persisted source", lane="vocab",
    )
    store.add_message(
        session["id"], role="user", content=request.user_instruction,
        context_snapshot=request.to_snapshot(),
    )
    store.add_message(session["id"], role="assistant", content="Legacy-compatible reply")

    restored = StudySessionStore(str(path)).get_session(session["id"])
    snapshot = restored["messages"][0]["context_snapshot"]
    assert snapshot["workspace"] == "forge"
    assert snapshot["source_text"] == "Persisted source"
    assert "context_snapshot" not in restored["messages"][1]


def test_station_ui_has_explicit_surface_ownership_and_bilingual_labels():
    root = Path(__file__).resolve().parents[1]
    companion = (root / "ui" / "ai_companion.py").read_text(encoding="utf-8")
    factory = (root / "ui" / "factory_dialog.py").read_text(encoding="utf-8")

    assert 'workspace="reviewer"' in companion
    assert 'workspace="forge"' in companion
    assert "self.context_board" in companion
    assert "self.source_input" in companion
    assert "self.source_input.textChanged.connect(self._update_context_board)" in companion
    assert "self.cbo_mode.currentIndexChanged.connect(self._update_context_board)" in companion
    assert "refresh_ai_companion_context" in companion
    assert "self.setMinimumWidth(340)" in companion
    assert "self.setMinimumSize(760, 600)" in companion
    assert "source_text=source_text" in factory
    assert "query_anki_context" not in factory[factory.index("def _ai_chat(self):"):factory.index("def _ai_chat_legacy(self):")]
    assert t("study_reviewer_title", lang="vi")
    assert t("study_reviewer_title", lang="en")
    assert t("study_forge_title", lang="vi")
    assert t("study_forge_title", lang="en")
