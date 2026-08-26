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
    route_forge_lane, workspace_context_message,
)
from utils.i18n import t


def _snapshot(mode="qa", side="question"):
    return {
        "language": "english",
        "side": side,
        "study_mode": mode,
        "card_kind": "vocabulary",
        "front": "TARGET",
        "current_target": "TARGET",
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
    assert not reviewer.allows_card_mode and forge.allows_card_mode
    assert reviewer.quick_actions != forge.quick_actions
    assert not set(reviewer.quick_actions).intersection(forge.quick_actions)
    with pytest.raises(ValueError, match="workspace"):
        resolve_workspace("auto")


@pytest.mark.parametrize(
    ("source", "instruction", "fallback", "expected"),
    [
        ("A short article", "Tìm từ vựng đáng học", "grammar", "vocab"),
        ("日本語の文法 ～ながら", "", "vocab", "grammar"),
        ("N + that-clause", "", "vocab", "grammar"),
        ("neutral source", "", "grammar", "grammar"),
        ("neutral source", "", "unknown", "vocab"),
    ],
)
def test_forge_router_prefers_explicit_intent_then_preserves_fallback(
    source, instruction, fallback, expected,
):
    assert route_forge_lane(source, instruction, fallback) == expected


@pytest.mark.parametrize(
    ("mode", "present", "absent"),
    [
        ("qa", {"front"}, {"meaning", "example"}),
        ("vn", {"meaning"}, {"front", "current_target", "furigana", "pinyin", "romanization"}),
        ("wb", {"meaning"}, {"front", "current_target", "furigana", "pinyin", "romanization"}),
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


def test_reviewer_resolves_deictic_word_reference_to_current_card_target():
    request = _request(
        "reviewer", "reviewer-current-word",
        user_instruction="Lấy cho tôi ví dụ về phương vị từ của từ vựng này",
        language="chinese",
        card_context={
            "language": "chinese", "side": "question", "study_mode": "qa",
            "card_kind": "vocabulary", "front": "水果", "current_target": "水果",
            "pinyin": "shuǐguǒ", "meaning": "hoa quả",
        },
        use_card_context=True,
    )
    content = workspace_context_message(request)["content"]

    assert "current_card_kind: vocabulary" in content
    assert "current_target: 水果" in content
    assert "'từ vựng này'" in content
    assert "meaning: hoa quả" not in content


def test_reviewer_grammar_answer_context_keeps_standard_grammar_fields():
    request = _request(
        "reviewer", "reviewer-current-grammar", language="japanese",
        card_context={
            "language": "japanese", "side": "answer", "study_mode": "qa",
            "card_kind": "grammar", "pattern": "～わけではない",
            "current_target": "～わけではない", "meaning": "không hẳn là",
            "level": "N3", "topic": "phủ định một phần", "usage": "V + わけではない",
            "explanation": "Phủ định một kết luận tuyệt đối.",
            "example": "嫌いなわけではない。",
            "example_romanization": "kirai na wake dewa nai",
            "example_vn": "Không phải là tôi ghét.",
        },
        use_card_context=True,
    )
    content = workspace_context_message(request)["content"]

    assert "current_card_kind: grammar" in content
    assert "current_target: ～わけではない" in content
    assert "'ngữ pháp này'" in content
    assert "level: N3" in content
    assert "topic: phủ định một phần" in content
    assert "usage: V + わけではない" in content
    assert "example_romanization: kirai na wake dewa nai" in content


def test_reviewer_metadata_only_snapshot_is_not_claimed_as_attached():
    request = _request(
        "reviewer", "reviewer-metadata-only",
        card_context={
            "language": "chinese", "side": "question", "study_mode": "qa",
            "card_kind": "vocabulary", "deck": "HSK1",
        },
        use_card_context=True,
    )

    assert not request.use_card_context
    assert request.card_context == {}
    assert "no current-card context was attached" in workspace_context_message(request)["content"]


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
    assert "learning-material production belongs to Forge AI Workshop" in reviewer
    assert "verify the exact number and title in the same SOURCE" in reviewer
    assert "Never infer numbering or titles from chunk order" in reviewer
    assert "Separate SOURCE facts from Coach-created examples" in reviewer
    assert "current instruction always determines the task" in reviewer
    assert "never replace an explicit request with a generic card drill" in reviewer
    assert "Never invent register, nuance, or usage contrasts between grammar variants" in reviewer
    with pytest.raises(ValueError, match="Reviewer workspace"):
        build_study_prompt(
            "english", "vocab", english_ui=True, workspace="reviewer",
        )


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
    with pytest.raises(ValueError, match="Reviewer workspace"):
        ai_extractor.chat_with_ai(
            "Create a card", lang="english", card_mode="vocab",
            workspace="reviewer", workspace_request=reviewer,
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


def test_mixed_session_history_and_summaries_are_workspace_scoped(tmp_path):
    store = StudySessionStore(str(tmp_path / "sessions.json"))
    session = store.create_session(language="english")
    reviewer = _request(
        "reviewer", "reviewer-history", user_instruction="Reviewer history marker",
        card_context=_snapshot("qa"), use_card_context=True,
    )
    forge = _request(
        "forge", "forge-history", user_instruction="Forge history marker",
        source_text="Forge source marker", lane="vocab",
    )
    reviewer_message = store.add_message(
        session["id"], role="user", content=reviewer.user_instruction,
        context_snapshot=reviewer.to_snapshot(),
    )
    store.add_message(
        session["id"], role="assistant", content="Reviewer inferred reply marker",
    )
    store.add_message(
        session["id"], role="system", content="Reviewer checkpoint marker",
        message_type="system_internal", context_snapshot={"workspace": "reviewer"},
    )
    forge_message = store.add_message(
        session["id"], role="user", content=forge.user_instruction,
        context_snapshot=forge.to_snapshot(),
    )
    store.add_message(
        session["id"], role="assistant", content="Forge inferred reply marker",
    )
    store.add_message(
        session["id"], role="assistant", content="Malformed owner marker",
        context_snapshot={"workspace": "unknown"},
    )
    store.add_message(session["id"], role="user", content="Unowned legacy marker")
    store.add_message(session["id"], role="assistant", content="Unowned legacy reply")
    store.update_summary(
        session["id"], "Legacy global summary must not leak", reviewer_message["id"],
    )
    store.update_summary(
        session["id"], "Reviewer summary marker", reviewer_message["id"],
        workspace="reviewer",
    )
    store.update_summary(
        session["id"], "Forge summary marker", forge_message["id"],
        workspace="forge",
    )

    restored = StudySessionStore(str(tmp_path / "sessions.json")).get_session(session["id"])
    reviewer_current = _request(
        "reviewer", "reviewer-current", user_instruction="Reviewer current",
        card_context=_snapshot("qa"), use_card_context=False,
    )
    forge_current = _request(
        "forge", "forge-current", user_instruction="Forge current",
        source_text="Current Forge source", lane="vocab",
    )
    reviewer_prepared = prepare_study_context(
        restored, current_user_message=reviewer_current.user_instruction,
        system_prompt="Reviewer", model="unknown", session_max_tokens=4_000,
        workspace_request=reviewer_current,
    )
    forge_prepared = prepare_study_context(
        restored, current_user_message=forge_current.user_instruction,
        system_prompt="Forge", model="unknown", session_max_tokens=4_000,
        workspace_request=forge_current,
    )
    reviewer_text = "\n".join(item["content"] for item in reviewer_prepared.messages)
    forge_text = "\n".join(item["content"] for item in forge_prepared.messages)

    assert "Reviewer summary marker" in reviewer_text
    assert "Reviewer inferred reply marker" in reviewer_text
    assert "Reviewer checkpoint marker" not in reviewer_text
    assert "Forge history marker" not in reviewer_text
    assert "Forge summary marker" not in reviewer_text
    assert "Unowned legacy marker" not in reviewer_text
    assert "Malformed owner marker" not in reviewer_text
    assert "Legacy global summary must not leak" not in reviewer_text
    assert "Forge summary marker" in forge_text
    assert "Forge inferred reply marker" in forge_text
    assert "Reviewer history marker" not in forge_text
    assert "Reviewer summary marker" not in forge_text
    assert "Unowned legacy marker" not in forge_text
    assert "Malformed owner marker" not in forge_text
    assert restored["workspace_summaries"]["reviewer"]["summary"] == "Reviewer summary marker"
    assert restored["workspace_summaries"]["forge"]["summary"] == "Forge summary marker"


@pytest.mark.parametrize("mutation", ["replace", "delete_message", "delete_turn"])
def test_transcript_mutations_invalidate_global_and_workspace_summaries(tmp_path, mutation):
    store = StudySessionStore(str(tmp_path / f"{mutation}.json"))
    session = store.create_session(language="english")
    first = store.add_message(
        session["id"], role="user", content="first",
        context_snapshot={"workspace": "reviewer"},
    )
    store.add_message(
        session["id"], role="assistant", content="reply",
        context_snapshot={"workspace": "reviewer"},
    )
    store.update_summary(session["id"], "global", first["id"])
    store.update_summary(
        session["id"], "reviewer", first["id"], workspace="reviewer",
    )
    store.update_summary(
        session["id"], "forge", first["id"], workspace="forge",
    )

    if mutation == "replace":
        restored = store.replace_latest_user_message(session["id"], "edited")
    elif mutation == "delete_message":
        assert store.delete_message(session["id"], first["id"])
        restored = store.get_session(session["id"])
    else:
        assert store.delete_latest_user_turn(session["id"])
        restored = store.get_session(session["id"])

    assert restored["summary"] == ""
    assert restored["summary_through_message_id"] == ""
    assert all(
        slot == {"summary": "", "summary_through_message_id": ""}
        for slot in restored["workspace_summaries"].values()
    )


def test_latest_turn_mutation_refuses_the_other_workspace(tmp_path):
    store = StudySessionStore(str(tmp_path / "sessions.json"))
    session = store.create_session(language="english")
    store.add_message(
        session["id"], role="user", content="Forge owns this turn",
        context_snapshot={"workspace": "forge"},
    )
    before = store.get_session(session["id"])

    assert store.replace_latest_user_message(
        session["id"], "Reviewer edit", workspace="reviewer",
        context_snapshot={"workspace": "reviewer"},
    ) is None
    assert store.delete_latest_user_turn(
        session["id"], workspace="reviewer",
    ) is False
    assert store.get_session(session["id"])["messages"] == before["messages"]


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


def test_schema_v2_session_migrates_with_empty_workspace_memory(tmp_path):
    path = tmp_path / "sessions.json"
    path.write_text(json.dumps({
        "schema_version": 2,
        "sessions": [{
            "id": "v2-session", "title": "V2", "language": "english",
            "messages": [{"role": "user", "type": "user", "content": "legacy"}],
            "summary": "Owner unknown", "summary_through_message_id": "legacy-id",
            "artifacts": [],
        }],
        "ui_state": {},
    }), encoding="utf-8")

    store = StudySessionStore(str(path))
    restored = store.get_session("v2-session")

    assert restored["summary"] == "Owner unknown"
    assert restored["workspace_summaries"] == {
        "reviewer": {"summary": "", "summary_through_message_id": ""},
        "forge": {"summary": "", "summary_through_message_id": ""},
    }
    store.rename_session("v2-session", "Migrated")
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 3


def test_station_ui_has_explicit_surface_ownership_and_bilingual_labels():
    root = Path(__file__).resolve().parents[1]
    companion = (root / "ui" / "ai_companion.py").read_text(encoding="utf-8")
    factory = (root / "ui" / "factory_dialog.py").read_text(encoding="utf-8")
    theme = (root / "ui" / "theme.py").read_text(encoding="utf-8")

    assert 'workspace="reviewer"' in companion
    assert 'workspace="forge"' in factory
    assert "self.context_board" in companion
    assert "self.source_input" in companion
    assert "self.source_input.textChanged.connect(self._update_context_board)" in companion
    assert "self.cbo_mode.currentIndexChanged.connect(self._update_context_board)" in companion
    assert "self.cbo_mode.setVisible(self._policy.allows_card_mode and not self._integrated)" in companion
    assert "self.cbo_lane.currentIndexChanged.connect(self._update_context_board)" in companion
    assert "self.cbo_lane.setVisible(self._policy.allows_card_mode and not self._integrated)" in companion
    assert 'self.cbo_lane.addItem(t("study_forge_router_auto"), "auto")' in companion
    assert "if not self._policy.allows_card_mode:" in companion
    assert "refresh_ai_companion_context" in companion
    assert "380 if not self._integrated else 0" in companion
    assert "self.transcript.setMinimumHeight(120 if self._integrated else 140)" in companion
    assert "class AiStudySessionDialog" not in companion
    assert "source_text=source_text" in factory
    assert 'self.cbo_mode.addItem(t("study_forge_mode_candidates"), "candidates")' in companion
    assert 'self.cbo_mode.addItem(t("study_forge_mode_artifact"), "artifact")' in companion
    assert 'self.cbo_mode.addItem(t("study_forge_mode_vocab"), "vocab")' not in companion
    assert 'self.cbo_mode.addItem(t("study_forge_mode_grammar"), "grammar")' not in companion
    assert "build_selected_candidate_instruction" in companion
    assert "study_candidates_source_changed" in companion
    assert "_prepared_candidate_source_digest" in companion
    assert "def _response_context_snapshot" in companion
    assert "context_snapshot=response_snapshot" in companion
    assert "workspace=self._workspace" in companion
    assert "study_latest_turn_other_workspace" in companion
    assert "existing_entries=list(existing_entries or ())" in factory
    assert "integrated=True" in factory
    assert "source_input=self.ai_text_input" in factory
    assert "bentoForgeIntegratedProductionLine" in factory
    assert "forgeFactoryPipelineStrip" not in factory
    assert "forgeFactoryPipelineStrip" not in theme
    assert "forgeProductionWorkbench" in factory
    assert "forgeProcessingStack" in factory
    assert "card_target = next(" in companion
    assert "safe_card_terms" not in companion
    assert "def _scope_heading(source: dict)" in companion
    assert 'return f"{number}. {title}"' in companion
    assert "forgeSourcePanel" in factory
    assert "forgeAiPanel" in factory
    assert "forgeArtifactPanel" in factory
    assert "self.forge_panel.body.setVisible(True)" in factory
    assert "btn_top_ai_settings" not in factory
    assert "self.cbo_language = QComboBox()" in factory
    assert "self.main_columns = QHBoxLayout()" in factory
    assert "self.main_columns.addWidget(self.left_scroll, 6)" in factory
    assert "self.main_columns.addWidget(self.right_scroll, 4)" in factory
    assert "self.main_splitter" not in factory
    assert "self.production_splitter" not in factory
    assert "self.processing_splitter" not in factory
    assert "self.lbl_tip.setVisible(False)" in factory
    assert "Qt.ScrollBarPolicy.ScrollBarAlwaysOff" in factory
    assert "op_grid.addWidget(self.btn_import, 0, 0, 1, 2)" in factory
    assert "op_grid.addWidget(self.btn_rollback_import, 1, 0)" in factory
    assert "op_grid.addWidget(self.btn_cancel_order, 1, 1)" in factory
    assert "forgeSourceProductionScroll" in factory
    assert "forgeReviewImportScroll" in factory
    assert "self.lbl_ai_files.setWordWrap(False)" in factory
    assert "self.title_label.setVisible(not self._integrated)" in companion
    assert "self.context_board.setVisible(not self._integrated)" in companion
    assert "self.transcript.setVisible(bool(blocks))" in companion
    assert 'self.composer.setObjectName("forgeAiComposer")' in companion
    assert "self.chk_create_card = QCheckBox()" in companion
    assert "def _on_create_card_toggled" in companion
    assert 'return self._lane if self._lane in {"vocab", "grammar"} else "vocab"' in companion
    assert "self.btn_ai_settings.setVisible(False)" in factory
    assert "ai_bar.insertWidget(0, self.btn_ai_chat)" in factory
    assert "self.btn_ai_chat.setVisible(False)" in factory
    assert "ai_main.addLayout(instr_bar)" not in factory
    assert "get_existing_vocab_from_deck" in factory[factory.index("def _ai_chat(self):"):factory.index("def _ai_chat_legacy(self):")]
    assert "query_anki_context" not in factory[factory.index("def _ai_chat(self):"):factory.index("def _ai_chat_legacy(self):")]
    factory_extract = factory[factory.index("def _ai_extract(self):"):factory.index("def _on_deck_scan_finished", factory.index("def _ai_extract(self):"))]
    assert "route_forge_lane" in factory_extract
    assert t("study_reviewer_title", lang="vi")
    assert t("study_reviewer_title", lang="en")
    assert t("study_forge_title", lang="vi")
    assert t("study_forge_title", lang="en")
    assert t("study_forge_source_label", lang="vi") == "NGUỒN HỌC LIỆU"
    assert "Nạp Quặng" not in t("ai_input_placeholder_vocab", lang="vi")
    assert "không tạo thẻ mới" in t("study_reviewer_subtitle", lang="vi")
    assert "no card creation" in t("study_reviewer_subtitle", lang="en")
    assert "AI Study Sessions" in t("study_menu_action", lang="vi")
