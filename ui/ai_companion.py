"""Lazy dockable/floating AI Study Sessions companion for Anki Reviewer/Forge."""

from __future__ import annotations

import hashlib
import html
import json
import uuid
from typing import Optional
from urllib.parse import quote, unquote

from aqt import mw
from aqt.qt import (
    QAction, QCheckBox, QComboBox, QDialog, QDockWidget, QHBoxLayout, QInputDialog,
    QKeySequence, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QShortcut, QTimer,
    QGridLayout, QTableWidget, QTableWidgetItem, QTextBrowser, QTextEdit, QToolButton,
    QVBoxLayout, QWidget, Qt,
)
from aqt.utils import showInfo, tooltip

from utils.ai_card_artifacts import (
    artifact_is_compatible, artifact_label, artifact_to_factory_payload,
    create_card_artifact,
)
from utils.ai_coaching_loop import (
    build_reviewer_checkpoint, latest_reviewer_checkpoint,
)
from utils.ai_extractor import get_api_config, get_api_key_for_provider
from utils.ai_providers import AI_PROVIDERS, detect_provider, get_provider
from utils.ai_source_candidates import (
    build_selected_candidate_instruction, mark_existing_candidate_surfaces,
)
from utils.ai_session_store import StudySessionStore
from utils.ai_usage_history import get_usage_entries, summarize_usage
from utils.ai_workflow import AiWorkflowCoordinator
from utils.ai_workspace import (
    build_workspace_request_context, get_workspace_policy, resolve_workspace,
)
from utils.i18n import get_language, t
from utils.logger import get_logger, log_event
from utils.language_identity import try_normalize_language
from ui.theme import apply_theme
from workers.ai_workers import AiChatThread


logger = get_logger()
_COMPANION = None
_STUDY_DIALOG = None
_SHORTCUT_ACTION = None

_LANGUAGE_LABELS = {
    "japanese": "日本語", "chinese": "中文", "korean": "한국어", "english": "English",
}
class AiCompanionDock(QDockWidget):
    """Workspace-parameterized surface over one shared Study Session backend."""

    def __init__(self, main_window, *, workspace="reviewer", dockable=True, parent=None):
        workspace = resolve_workspace(workspace)
        policy = get_workspace_policy(workspace)
        if workspace == "forge" and dockable:
            raise ValueError("Forge workspace is a standalone surface")
        super().__init__(t(policy.title_key), parent or main_window)
        self._workspace = workspace
        self._policy = policy
        self._dockable = bool(dockable)
        self.setObjectName(
            "bentoForgeReviewerWorkspace"
            if self._workspace == "reviewer" else "bentoForgeWorkshopWorkspace"
        )
        self.setMinimumWidth(340)
        self.resize(440, 720)
        if self._dockable:
            self.setAllowedAreas(
                Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
            )
            self.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetClosable
                | QDockWidget.DockWidgetFeature.DockWidgetMovable
                | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            )
        else:
            self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
            self.setTitleBarWidget(QWidget(self))
        self._main_window = main_window
        self._store = StudySessionStore()
        self._workflow = AiWorkflowCoordinator()
        self._card_context = None
        self._active_session_id = ""
        self._pending_session_id = ""
        self._pending_user_message_id = ""
        self._pending_card_mode = None
        self._pending_candidate_mode = False
        self._pending_request_token = ""
        self._pending_workspace_request = None
        self._existing_entries = []
        self._prepared_candidate_source_digest = ""
        self._learning_mode = "language"
        self._lane = "vocab"
        self._editing_latest = False
        self._restoring = True
        self._geometry_timer = QTimer(self)
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.timeout.connect(self._persist_floating_geometry)
        self._build_ui()
        if self._dockable:
            self._restore_state()
        self._reload_sessions()
        self._restoring = False
        if self._dockable:
            self.topLevelChanged.connect(self._on_top_level_changed)
            self.dockLocationChanged.connect(self._on_dock_location_changed)
            self.visibilityChanged.connect(self._on_visibility_changed)

    def _build_ui(self):
        root = QWidget(self)
        root.setObjectName("forgeAiCompanionRoot")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(10, 9, 10, 9)
        outer.setSpacing(7)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel(f"<b>{t(self._policy.title_key)}</b>")
        title.setObjectName("forgeAiStationTitle")
        subtitle = QLabel(t(self._policy.subtitle_key))
        subtitle.setObjectName("forgeAiStationSubtitle")
        subtitle.setProperty("class", "dim")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)
        self.btn_collapse = QToolButton()
        self.btn_collapse.setText("−")
        self.btn_collapse.setToolTip(t("study_collapse"))
        self.btn_collapse.clicked.connect(self.toggle_collapsed)
        header.addWidget(self.btn_collapse)
        outer.addLayout(header)

        self.context_board = QLabel()
        self.context_board.setObjectName("forgeAiContextBoard")
        self.context_board.setWordWrap(True)
        outer.addWidget(self.context_board)

        self.route_strip = QLabel(t("study_forge_route_strip"))
        self.route_strip.setObjectName("forgeAiRouteStrip")
        self.route_strip.setVisible(self._policy.shows_route_strip)
        outer.addWidget(self.route_strip)

        self.body = QWidget(root)
        body = QVBoxLayout(self.body)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(7)

        sessions = QHBoxLayout()
        self.cbo_session = QComboBox()
        self.cbo_session.setAccessibleName(t("study_sessions"))
        self.cbo_session.currentIndexChanged.connect(self._on_session_selected)
        sessions.addWidget(self.cbo_session, 1)
        for label, tip, callback in (
            ("＋", "study_new", self.new_session),
            ("✎", "study_rename", self.rename_session),
            ("×", "study_delete", self.delete_session),
        ):
            button = QToolButton()
            button.setText(label)
            button.setToolTip(t(tip))
            button.clicked.connect(lambda _checked=False, fn=callback: fn())
            sessions.addWidget(button)
        body.addLayout(sessions)

        provider_row = QHBoxLayout()
        self.cbo_provider = QComboBox()
        for provider in AI_PROVIDERS:
            self.cbo_provider.addItem(provider["name"], provider["id"])
        self.cbo_provider.addItem(t("ai_set_provider_custom"), "__custom__")
        self.cbo_provider.currentIndexChanged.connect(self._on_provider_selected)
        provider_row.addWidget(self.cbo_provider, 1)
        self.cbo_model = QComboBox()
        self.cbo_model.setEditable(True)
        self.cbo_model.currentTextChanged.connect(self._on_model_selected)
        provider_row.addWidget(self.cbo_model, 2)
        self.btn_settings = QToolButton()
        self.btn_settings.setText("⚙")
        self.btn_settings.setToolTip(t("ai_settings_btn"))
        self.btn_settings.clicked.connect(self._open_settings)
        provider_row.addWidget(self.btn_settings)
        body.addLayout(provider_row)

        self.source_label = QLabel(t("study_forge_source_label"))
        self.source_label.setObjectName("forgeAiSourceLabel")
        self.source_label.setVisible(self._policy.allows_source_context)
        body.addWidget(self.source_label)
        self.source_input = QPlainTextEdit()
        self.source_input.setObjectName("forgeAiSourceInput")
        self.source_input.setPlaceholderText(t("study_forge_source_placeholder"))
        self.source_input.setAccessibleName(t("study_forge_source_label"))
        self.source_input.setMaximumHeight(105)
        self.source_input.setVisible(self._policy.allows_source_context)
        self.source_input.textChanged.connect(self._update_context_board)
        body.addWidget(self.source_input)

        self.transcript = QTextBrowser()
        self.transcript.setObjectName("forgeAiTranscript")
        self.transcript.setOpenExternalLinks(False)
        self.transcript.setOpenLinks(False)
        self.transcript.anchorClicked.connect(self._on_transcript_link)
        self.transcript.setAccessibleName(t("study_conversation"))
        body.addWidget(self.transcript, 1)

        quick = QGridLayout()
        for index, (key, prompt_key) in enumerate(self._policy.quick_actions):
            button = QPushButton(t(key))
            button.setProperty("class", "stationAction")
            button.setToolTip(t("study_quick_tip"))
            button.clicked.connect(lambda _checked=False, value=prompt_key: self._set_quick_prompt(t(value)))
            quick.addWidget(button, index // 3, index % 3)
        body.addLayout(quick)

        coach = QVBoxLayout()
        self.coach_state = QLabel(t("study_coach_loop_idle"))
        self.coach_state.setObjectName("forgeAiCoachState")
        self.coach_state.setWordWrap(True)
        coach.addWidget(self.coach_state)
        coach_actions = QHBoxLayout()
        self.btn_needs_practice = QPushButton(t("study_coach_needs_practice"))
        self.btn_needs_practice.setProperty("class", "stationAction")
        self.btn_needs_practice.clicked.connect(
            lambda: self.mark_coaching_outcome("needs_practice")
        )
        coach_actions.addWidget(self.btn_needs_practice)
        self.btn_understood = QPushButton(t("study_coach_understood"))
        self.btn_understood.setProperty("class", "primary")
        self.btn_understood.clicked.connect(
            lambda: self.mark_coaching_outcome("understood")
        )
        coach_actions.addWidget(self.btn_understood)
        for widget in (
            self.coach_state, self.btn_needs_practice, self.btn_understood,
        ):
            widget.setVisible(self._workspace == "reviewer")
        coach.addLayout(coach_actions)
        body.addLayout(coach)

        context_row = QHBoxLayout()
        self.chk_context = QCheckBox(t("study_use_card_context"))
        self.chk_context.setChecked(False)
        self.chk_context.setVisible(self._policy.allows_card_context)
        self.chk_context.toggled.connect(self._update_context_board)
        context_row.addWidget(self.chk_context, 1)
        self.cbo_mode = QComboBox()
        self.cbo_mode.addItem(t("study_mode_chat"), None)
        if self._policy.allows_card_mode:
            self.cbo_mode.addItem(t("study_forge_mode_candidates"), "candidates")
            self.cbo_mode.addItem(t("study_forge_mode_vocab"), "vocab")
            self.cbo_mode.addItem(t("study_forge_mode_grammar"), "grammar")
        self.cbo_mode.setAccessibleName(t("study_card_mode"))
        self.cbo_mode.setVisible(self._policy.allows_card_mode)
        self.cbo_mode.currentIndexChanged.connect(self._update_context_board)
        context_row.addWidget(self.cbo_mode)
        body.addLayout(context_row)

        artifacts = QHBoxLayout()
        self.cbo_artifact = QComboBox()
        self.cbo_artifact.setAccessibleName(t("study_artifacts"))
        self.cbo_artifact.currentIndexChanged.connect(self._on_artifact_selected)
        artifacts.addWidget(self.cbo_artifact, 1)
        self.btn_review_artifact = QPushButton(t("study_review_artifact"))
        self.btn_review_artifact.clicked.connect(self.review_artifact)
        artifacts.addWidget(self.btn_review_artifact)
        self.btn_forge = QPushButton(t("study_open_forge"))
        self.btn_forge.clicked.connect(self.open_artifact_in_forge)
        artifacts.addWidget(self.btn_forge)
        for widget in (self.cbo_artifact, self.btn_review_artifact, self.btn_forge):
            widget.setVisible(self._policy.allows_card_mode)
        body.addLayout(artifacts)

        self.input = QTextEdit()
        self.input.setObjectName("forgeAiInstructionInput")
        self.input.setAcceptRichText(False)
        self.input.setPlaceholderText(t(self._policy.input_placeholder_key))
        self.input.setAccessibleName(t(self._policy.input_accessible_key))
        self.input.setMaximumHeight(115)
        body.addWidget(self.input)

        actions = QHBoxLayout()
        self.btn_edit_latest = QPushButton(t("study_edit_latest"))
        self.btn_edit_latest.clicked.connect(self.edit_latest_message)
        actions.addWidget(self.btn_edit_latest)
        self.btn_delete_latest = QPushButton(t("study_delete_latest"))
        self.btn_delete_latest.clicked.connect(self.delete_latest_message)
        actions.addWidget(self.btn_delete_latest)
        self.btn_stop = QPushButton(t("ai_stop_btn"))
        self.btn_stop.clicked.connect(self.stop_request)
        self.btn_stop.setVisible(False)
        actions.addWidget(self.btn_stop)
        actions.addStretch()
        self.btn_send = QPushButton(t("study_send"))
        self.btn_send.setProperty("class", "primary")
        self.btn_send.setDefault(True)
        self.btn_send.clicked.connect(self.send_message)
        actions.addWidget(self.btn_send)
        body.addLayout(actions)

        footer = QHBoxLayout()
        self.status = QLabel(t("study_ready"))
        self.status.setObjectName("forgeAiStatus")
        footer.addWidget(self.status, 1)
        back_key = "study_back_review" if self._workspace == "reviewer" else "study_close_workspace"
        self.btn_back = QPushButton(t(back_key))
        self.btn_back.clicked.connect(self.back_to_review)
        footer.addWidget(self.btn_back)
        body.addLayout(footer)

        outer.addWidget(self.body, 1)
        self.setWidget(root)
        self._theme_cfg = apply_theme(self)
        self._send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self._send_shortcut.activated.connect(self.send_message)
        self._send_shortcut_alt = QShortcut(QKeySequence("Ctrl+Enter"), self)
        self._send_shortcut_alt.activated.connect(self.send_message)
        self._escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self._escape_shortcut.activated.connect(self.back_to_review)

    def _restore_state(self):
        state = self._store.get_ui_state()
        side = state.get("dock_side", "right")
        area = (
            Qt.DockWidgetArea.LeftDockWidgetArea
            if side == "left" else Qt.DockWidgetArea.RightDockWidgetArea
        )
        self._main_window.addDockWidget(area, self)
        if state.get("floating"):
            self.setFloating(True)
            self.resize(
                max(340, int(state.get("floating_width") or 440)),
                max(420, int(state.get("floating_height") or 720)),
            )
            self.move(int(state.get("floating_x") or 80), int(state.get("floating_y") or 80))
        if state.get("collapsed"):
            self.body.setVisible(False)
            self.btn_collapse.setText("+")
        if not state.get("visible", False):
            self.hide()

    def _reload_sessions(self, select_id: str = ""):
        requested = select_id or self._active_session_id or self._store.get_ui_state().get("last_session_id", "")
        self.cbo_session.blockSignals(True)
        self.cbo_session.clear()
        selected = -1
        for index, session in enumerate(self._store.list_sessions()):
            self.cbo_session.addItem(session["title"], session["id"])
            if session["id"] == requested:
                selected = index
        self.cbo_session.blockSignals(False)
        if self.cbo_session.count() == 0:
            self.new_session()
            return
        self.cbo_session.setCurrentIndex(selected if selected >= 0 else 0)
        self._on_session_selected(self.cbo_session.currentIndex())

    def _default_provider_model(self) -> tuple[str, str]:
        cfg = get_api_config()
        provider_id = str(cfg.get("default_provider") or cfg.get("provider") or "")
        provider_id = provider_id or detect_provider(cfg.get("api_base", ""), cfg.get("model", ""))
        provider = get_provider(provider_id)
        if provider is None:
            return "__custom__", str(cfg.get("model") or "")
        models = dict(cfg.get("default_models") or {})
        model = str(models.get(provider_id) or provider.get("default") or provider["models"][0])
        if model not in provider["models"]:
            model = str(provider.get("default") or provider["models"][0])
            tooltip(t("study_model_fallback"))
        return provider_id, model

    def _resolve_language(self, language: str = "") -> Optional[str]:
        candidate = language
        if not candidate:
            try:
                candidate = mw.col.conf.get("ai_factory_active_lang")
            except Exception:
                candidate = None
        return try_normalize_language(candidate)

    def new_session(self, *, language: str = "", deck: str = ""):
        language = self._resolve_language(language)
        if language is None:
            self.status.setText(t("study_language_required"))
            return None
        provider, model = self._default_provider_model()
        title = t("study_default_title")
        session = self._store.create_session(
            language=language, title=title, provider=provider, model=model,
            optional_deck_context={"deck": deck} if deck else None,
        )
        self._active_session_id = session["id"]
        self._reload_sessions(session["id"])

    def rename_session(self):
        session = self._current_session()
        if not session:
            return
        title, accepted = QInputDialog.getText(
            self, t("study_rename"), t("study_rename_prompt"), text=session["title"],
        )
        if accepted and title.strip():
            self._store.rename_session(session["id"], title.strip())
            self._reload_sessions(session["id"])

    def delete_session(self):
        session = self._current_session()
        if not session:
            return
        answer = QMessageBox.question(
            self, t("study_delete"), t("study_delete_confirm", title=session["title"]),
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._store.delete_session(session["id"])
            self._active_session_id = ""
            self._reload_sessions()

    def _current_session(self) -> Optional[dict]:
        session_id = self._active_session_id or str(self.cbo_session.currentData() or "")
        return self._store.get_session(session_id) if session_id else None

    def _on_session_selected(self, _index):
        session_id = str(self.cbo_session.currentData() or "")
        if not session_id:
            return
        self._active_session_id = session_id
        self._store.update_ui_state(last_session_id=session_id)
        session = self._store.get_session(session_id)
        if not session:
            return
        self._set_provider_model(session.get("provider"), session.get("model"))
        self._render_session(session)
        self._update_context_board()

    def _set_provider_model(self, provider_id: str, model: str):
        self.cbo_provider.blockSignals(True)
        index = self.cbo_provider.findData(provider_id)
        self.cbo_provider.setCurrentIndex(index if index >= 0 else self.cbo_provider.findData("__custom__"))
        self.cbo_provider.blockSignals(False)
        self._populate_models(str(self.cbo_provider.currentData() or "__custom__"), model)

    def _populate_models(self, provider_id: str, selected: str = ""):
        self.cbo_model.blockSignals(True)
        self.cbo_model.clear()
        provider = get_provider(provider_id)
        if provider:
            self.cbo_model.addItems(provider["models"])
            model = selected if selected in provider["models"] else provider.get("default", "")
            if selected and selected not in provider["models"]:
                self.status.setText(t("study_model_fallback"))
            self.cbo_model.setCurrentText(model)
        else:
            self.cbo_model.setEditText(selected or get_api_config().get("model", ""))
        self.cbo_model.blockSignals(False)

    def _on_provider_selected(self, _index):
        if self._restoring:
            return
        provider_id = str(self.cbo_provider.currentData() or "__custom__")
        self._populate_models(provider_id)
        self._persist_session_provider_model()

    def _on_model_selected(self, _model):
        if not self._restoring:
            self._persist_session_provider_model()

    def _persist_session_provider_model(self):
        session = self._current_session()
        if not session:
            return
        session["provider"] = str(self.cbo_provider.currentData() or "__custom__")
        session["model"] = self.cbo_model.currentText().strip()
        self._store.save_session(session)

    def _runtime_config(self) -> dict:
        cfg = get_api_config()
        provider_id = str(self.cbo_provider.currentData() or "__custom__")
        provider = get_provider(provider_id)
        api_base = provider["base"] if provider else cfg.get("api_base", "")
        runtime = dict(cfg)
        runtime.update({
            "provider": provider_id,
            "api_base": api_base,
            "model": self.cbo_model.currentText().strip(),
            "api_key": get_api_key_for_provider(provider_id, api_base),
        })
        return runtime

    def open_for_context(
        self,
        snapshot: Optional[dict] = None,
        *,
        language: str = "",
        initial_text: str = "",
        source_text: str = "",
        learning_mode: str = "language",
        lane: str = "vocab",
        existing_entries: Optional[list] = None,
    ):
        snapshot_language = try_normalize_language((snapshot or {}).get("language"))
        self._card_context = (
            dict(snapshot)
            if self._workspace == "reviewer"
            and isinstance(snapshot, dict)
            and snapshot_language
            else None
        )
        self.chk_context.setChecked(bool(self._card_context))
        self._learning_mode = (
            str(learning_mode or "language").strip().casefold()
            if self._workspace == "forge" else "language"
        )
        self._lane = str(lane or "vocab").strip().casefold()
        self._existing_entries = (
            list(existing_entries or ()) if self._workspace == "forge" else []
        )
        self._prepared_candidate_source_digest = ""
        if self._workspace == "forge":
            self.source_input.setPlainText(source_text or "")
        else:
            self.source_input.clear()
        language = self._resolve_language(language or str((snapshot or {}).get("language") or "")) or ""
        current = self._current_session()
        if language and current and current.get("language") != language:
            matching = next(
                (item for item in self._store.list_sessions() if item.get("language") == language),
                None,
            )
            if matching:
                self._reload_sessions(matching["id"])
                current = self._current_session()
            else:
                current = None
        if not current:
            self.new_session(language=language, deck=str((snapshot or {}).get("deck") or ""))
        if initial_text:
            self.input.setPlainText(initial_text)
        elif self._workspace == "forge":
            self.input.clear()
        self._update_context_board()
        self.show()
        self.raise_()
        if self._dockable:
            self._store.update_ui_state(visible=True)

    def _update_context_board(self, *_args):
        session = self._current_session()
        language = str((session or {}).get("language") or "")
        language_label = _LANGUAGE_LABELS.get(language, language.title() or "-")
        if self._workspace == "reviewer":
            context_enabled = bool(self._card_context) and self.chk_context.isChecked()
            checkpoint = latest_reviewer_checkpoint(
                (session or {}).get("messages", []), self._card_context,
            )
            outcome = str((checkpoint or {}).get("outcome") or "idle")
            self.coach_state.setText(t(f"study_coach_loop_{outcome}"))
            for button in (self.btn_needs_practice, self.btn_understood):
                button.setEnabled(bool(self._card_context))
            mode = str((self._card_context or {}).get("study_mode") or "-").upper()
            side_key = (
                "study_context_answer_side"
                if str((self._card_context or {}).get("side") or "question") == "answer"
                else "study_context_question_side"
            )
            card_key = (
                "study_context_card_attached"
                if context_enabled else "study_context_card_not_sent"
            )
            self.context_board.setText(t(
                "study_context_reviewer",
                language=language_label,
                mode=mode,
                side=t(side_key),
                card=t(card_key),
            ))
            return
        lane = "knowledge" if self._learning_mode == "knowledge" else self._lane
        lane_label = t(f"study_context_lane_{lane}")
        source = self.source_input.toPlainText().strip()
        source_state = (
            t("study_context_source_chars", count=len(source))
            if source else t("study_context_source_none")
        )
        self.context_board.setText(t(
            "study_context_forge",
            language=language_label,
            lane=lane_label,
            source=source_state,
            card=t("study_context_no_current_card"),
        ))

    def refresh_reviewer_context(self, snapshot: Optional[dict]):
        """Refresh the current card/side without opening or raising the dock."""
        if self._workspace != "reviewer":
            return
        snapshot_language = try_normalize_language((snapshot or {}).get("language"))
        self._card_context = (
            dict(snapshot) if isinstance(snapshot, dict) and snapshot_language else None
        )
        if not self._card_context:
            self.chk_context.setChecked(False)
        self._update_context_board()

    def _set_quick_prompt(self, prompt: str):
        self.input.setPlainText(prompt)
        self.input.setFocus()

    def mark_coaching_outcome(self, outcome: str):
        """Persist a local Reviewer checkpoint without calling AI or touching SRS."""
        if self._workspace != "reviewer":
            return
        if self._workflow.chat_worker is not None:
            tooltip(t("study_coach_request_active"))
            return
        session = self._current_session()
        try:
            checkpoint = build_reviewer_checkpoint(self._card_context, outcome)
        except ValueError:
            tooltip(t("study_coach_context_required"))
            return
        if not session:
            self.status.setText(t("study_language_required"))
            return
        normalized = checkpoint["outcome"]
        self._store.add_message(
            session["id"], role="system",
            content=t(f"study_coach_checkpoint_{normalized}"),
            message_type="system_internal", context_snapshot=checkpoint,
        )
        self._reload_sessions(session["id"])
        if normalized == "needs_practice":
            self._set_quick_prompt(t("study_prompt_check"))
            self.status.setText(t("study_coach_practice_prepared"))
            return
        tooltip(t("study_coach_returning"))
        self.back_to_review()

    def send_message(self):
        if self._workflow.chat_worker is not None:
            return
        selected_mode = (
            self.cbo_mode.currentData() if self._policy.allows_card_mode else None
        )
        text = self.input.toPlainText().strip()
        if selected_mode == "candidates" and not text:
            text = t("study_candidates_default_instruction")
        if not text:
            return
        session = self._current_session()
        if not session:
            self.new_session(language=str((self._card_context or {}).get("language") or ""))
            session = self._current_session()
        if not session:
            self.status.setText(t("study_language_required"))
            return
        if selected_mode == "candidates":
            if self._learning_mode != "language":
                showInfo(t("study_candidates_language_only"))
                return
            if not self.source_input.toPlainText().strip():
                showInfo(t("study_candidates_source_required"))
                return
        runtime = self._runtime_config()
        if not runtime.get("api_key") and "localhost" not in runtime.get("api_base", ""):
            showInfo(t("error_api_key_missing"))
            return
        request_token = uuid.uuid4().hex
        request_context = build_workspace_request_context(
            workspace=self._workspace,
            language=session["language"],
            user_instruction=text,
            request_token=request_token,
            learning_mode=self._learning_mode,
            lane=self._lane,
            source_text=(
                self.source_input.toPlainText() if self._workspace == "forge" else ""
            ),
            card_context=self._card_context,
            use_card_context=(
                self._workspace == "reviewer" and self.chk_context.isChecked()
            ),
        )
        if (
            selected_mode in {"vocab", "grammar"}
            and self._prepared_candidate_source_digest
            and "SELECTED_SOURCE_CANDIDATES=" in text
            and hashlib.sha256(request_context.source_text.encode("utf-8")).hexdigest()
            != self._prepared_candidate_source_digest
        ):
            showInfo(t("study_candidates_source_changed"))
            return
        if session["title"] == t("study_default_title") and not session["messages"]:
            local_title = " ".join(text.replace("\n", " ").split()[:8])[:80]
            self._store.rename_session(session["id"], local_title or t("study_default_title"))
        if self._editing_latest:
            session = self._store.replace_latest_user_message(
                session["id"], text,
                context_snapshot=request_context.to_snapshot(),
                workspace=self._workspace,
            )
            if session is None:
                self._editing_latest = False
                tooltip(t("study_latest_turn_other_workspace"))
                self._reload_sessions(self._active_session_id)
                return
            user_message = session["messages"][-1]
            self._editing_latest = False
        else:
            user_message = self._store.add_message(
                session["id"], role="user", content=text,
                context_snapshot=request_context.to_snapshot(),
            )
        self._pending_user_message_id = user_message["id"]
        self._pending_session_id = session["id"]
        self._pending_candidate_mode = selected_mode == "candidates"
        self._pending_card_mode = (
            selected_mode if selected_mode in {"vocab", "grammar"} else None
        )
        self._pending_request_token = request_token
        self._pending_workspace_request = request_context
        self._prepared_candidate_source_digest = ""
        self.input.clear()
        self._reload_sessions(session["id"])
        self.btn_send.setEnabled(False)
        self.btn_stop.setVisible(True)
        self.status.setText(t("study_thinking"))
        self._workflow.begin()
        self._workflow.start_chat(
            AiChatThread,
            message=text,
            lang=session["language"],
            conversation_history=None,
            anki_context=request_context.card_context,
            card_kind=self._pending_card_mode or "vocab",
            card_mode=self._pending_card_mode,
            candidate_mode=self._pending_candidate_mode,
            study_session=self._store.get_session(session["id"]),
            use_card_context=request_context.use_card_context,
            session_id=session["id"],
            runtime_config=runtime,
            workspace=self._workspace,
            workspace_request=request_context,
            on_progress=lambda message, token=request_token: self._on_progress(message, token),
            on_finished=lambda result, token=request_token: self._on_finished(result, token),
            on_error=lambda error, token=request_token: self._on_error(error, token),
        )

    def _owns_request(self, token: str) -> bool:
        return bool(token) and token == self._pending_request_token

    def _response_context_snapshot(self, token: str) -> dict:
        """Persist response ownership without duplicating request source/card data."""
        return {"workspace": self._workspace, "request_token": token}

    def _on_progress(self, message: str, token: str):
        if not self._owns_request(token):
            return
        self.status.setText(message.splitlines()[0][:120])

    def _finish_request_ui(self):
        self.btn_send.setEnabled(True)
        self.btn_stop.setVisible(False)
        self.cbo_mode.setCurrentIndex(0)
        self._workflow.clear_chat_worker()

    def _on_finished(self, result: dict, token: str):
        if not self._owns_request(token):
            return
        session = self._store.get_session(self._pending_session_id)
        source_exists = bool(session) and any(
            item.get("id") == self._pending_user_message_id
            for item in session.get("messages", [])
        )
        if not session or not source_exists:
            self._finish_request_ui()
            self._clear_pending_request(token)
            return
        response_snapshot = self._response_context_snapshot(token)
        reply = str(result.get("reply") or "").strip()
        if reply:
            self._store.add_message(
                session["id"], role="assistant", content=reply,
                context_snapshot=response_snapshot,
            )
        candidate_manifest = None
        if self._pending_candidate_mode and result.get("candidate_manifest"):
            candidate_manifest = mark_existing_candidate_surfaces(
                result["candidate_manifest"], self._existing_entries,
            )
            rejected = int(candidate_manifest.get("invalid_count", 0)) + int(
                candidate_manifest.get("duplicate_count", 0)
            )
            self._store.add_message(
                session["id"], role="assistant",
                content=t(
                    "study_candidates_ready",
                    count=len(candidate_manifest.get("candidates", [])),
                    rejected=rejected,
                    existing=candidate_manifest.get("existing_surface_count", 0),
                ),
                context_snapshot=response_snapshot,
            )
        cards = result.get("card_json")
        if cards and self._policy.allows_card_mode and self._pending_card_mode:
            try:
                artifact = create_card_artifact(
                    session_id=session["id"], language=session["language"],
                    kind=self._pending_card_mode, cards=cards,
                    source_message_id=self._pending_user_message_id,
                )
                artifact = self._store.add_artifact(session["id"], artifact)
                self._store.add_message(
                    session["id"], role="assistant",
                    content=t("study_artifact_ready", count=len(cards)),
                    message_type="artifact_reference", artifact_id=artifact["artifact_id"],
                    context_snapshot=response_snapshot,
                )
            except ValueError as error:
                log_event(
                    "AI_ARTIFACT_REJECTED", "keep_invalid_cards_out_of_factory",
                    error=error.__class__.__name__,
                )
                self._store.add_message(
                    session["id"], role="assistant", content=t("study_artifact_rejected"),
                    context_snapshot=response_snapshot,
                )
        elif (
            self._policy.allows_card_mode
            and self._pending_card_mode
            and result.get("card_error")
        ):
            self._store.add_message(
                session["id"], role="assistant",
                content=result.get("card_warning") or t("study_artifact_rejected"),
                context_snapshot=response_snapshot,
            )
        if result.get("session_summary"):
            self._store.update_summary(
                session["id"],
                result["session_summary"],
                result.get("session_summary_through_message_id"),
                workspace=self._workspace,
            )
        selected_id = self._active_session_id or session["id"]
        self._finish_request_ui()
        self._clear_pending_request(token)
        self._reload_sessions(selected_id)
        if candidate_manifest:
            selected_ids = self._review_candidate_manifest(candidate_manifest)
            if selected_ids:
                instruction = build_selected_candidate_instruction(
                    candidate_manifest, selected_ids,
                    english_ui=get_language() == "en",
                )
                self.input.setPlainText(instruction)
                self._prepared_candidate_source_digest = str(
                    candidate_manifest.get("source_digest") or ""
                )
                mode_index = self.cbo_mode.findData(candidate_manifest.get("lane"))
                if mode_index >= 0:
                    self.cbo_mode.setCurrentIndex(mode_index)
                self.status.setText(t("study_candidates_selected", count=len(selected_ids)))
                self.input.setFocus()

    def _review_candidate_manifest(self, manifest: dict) -> list[str]:
        """Let the user explicitly choose source candidates for the next request."""
        candidates = list(manifest.get("candidates", []))
        dialog = QDialog(self)
        dialog.setWindowTitle(t("study_candidates_dialog_title"))
        dialog.resize(980, 560)
        layout = QVBoxLayout(dialog)
        summary = QLabel(t(
            "study_candidates_dialog_summary",
            count=len(candidates),
            existing=manifest.get("existing_surface_count", 0),
        ))
        summary.setWordWrap(True)
        layout.addWidget(summary)
        table = QTableWidget(len(candidates), 7, dialog)
        table.setHorizontalHeaderLabels([
            t("study_candidates_header_select"),
            t("study_candidates_header_target"),
            t("study_candidates_header_meaning"),
            t("study_candidates_header_priority"),
            t("study_candidates_header_source"),
            t("study_candidates_header_reason"),
            t("study_candidates_header_status"),
        ])
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        for row, candidate in enumerate(candidates):
            select_item = QTableWidgetItem("")
            select_item.setFlags(
                select_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
            )
            select_item.setCheckState(Qt.CheckState.Checked)
            select_item.setData(Qt.ItemDataRole.UserRole, candidate.get("candidate_id"))
            table.setItem(row, 0, select_item)
            values = (
                candidate.get("target", ""), candidate.get("meaning_hint", ""),
                candidate.get("priority", ""), candidate.get("source_excerpt", ""),
                candidate.get("reason", ""),
                t(
                    "study_candidates_status_existing"
                    if candidate.get("existing_surface")
                    else "study_candidates_status_new"
                ),
            )
            for column, value in enumerate(values, start=1):
                table.setItem(row, column, QTableWidgetItem(str(value)))
        table.resizeColumnsToContents()
        layout.addWidget(table, 1)
        actions = QHBoxLayout()
        btn_all = QPushButton(t("study_candidates_select_all"))
        btn_none = QPushButton(t("study_candidates_select_none"))
        btn_cancel = QPushButton(t("study_candidates_cancel"))
        btn_use = QPushButton(t("study_candidates_use_selected"))
        btn_use.setProperty("class", "primary")
        actions.addWidget(btn_all)
        actions.addWidget(btn_none)
        actions.addStretch()
        actions.addWidget(btn_cancel)
        actions.addWidget(btn_use)
        layout.addLayout(actions)

        def set_checked(state):
            for row in range(table.rowCount()):
                table.item(row, 0).setCheckState(state)

        btn_all.clicked.connect(lambda: set_checked(Qt.CheckState.Checked))
        btn_none.clicked.connect(lambda: set_checked(Qt.CheckState.Unchecked))
        btn_cancel.clicked.connect(dialog.reject)
        btn_use.clicked.connect(dialog.accept)
        apply_theme(dialog)
        if not dialog.exec():
            return []
        selected = [
            str(table.item(row, 0).data(Qt.ItemDataRole.UserRole) or "")
            for row in range(table.rowCount())
            if table.item(row, 0).checkState() == Qt.CheckState.Checked
        ]
        selected = [candidate_id for candidate_id in selected if candidate_id]
        if not selected:
            tooltip(t("study_candidates_none_selected"))
        return selected

    def _on_error(self, error: str, token: str):
        if not self._owns_request(token):
            return
        self._finish_request_ui()
        self._clear_pending_request(token)
        self.status.setText(t("study_error", error=error[:80]))

    def stop_request(self):
        token = self._pending_request_token
        self._workflow.cancel()
        self._finish_request_ui()
        self._clear_pending_request(token)
        self.status.setText(t("study_stopped"))

    def _clear_pending_request(self, token: str = ""):
        if token and token != self._pending_request_token:
            return
        self._pending_session_id = ""
        self._pending_user_message_id = ""
        self._pending_card_mode = None
        self._pending_candidate_mode = False
        self._pending_request_token = ""
        self._pending_workspace_request = None

    def edit_latest_message(self):
        session = self._current_session()
        if not session:
            return
        if self._pending_request_token and session["id"] == self._pending_session_id:
            tooltip(t("study_request_edit_blocked"))
            return
        message = next(
            (item for item in reversed(session["messages"]) if item["role"] == "user"), None,
        )
        snapshot = message.get("context_snapshot") if message else None
        message_workspace = (
            str(snapshot.get("workspace") or "").strip().casefold()
            if isinstance(snapshot, dict) else ""
        )
        if message and message_workspace == self._workspace:
            self.input.setPlainText(message["content"])
            self._editing_latest = True
            self.input.setFocus()
        elif message:
            tooltip(t("study_latest_turn_other_workspace"))

    def delete_latest_message(self):
        session = self._current_session()
        if (
            session and self._pending_request_token
            and session["id"] == self._pending_session_id
        ):
            tooltip(t("study_request_edit_blocked"))
            return
        if session and self._store.delete_latest_user_turn(
            session["id"], workspace=self._workspace,
        ):
            self._editing_latest = False
            self.input.clear()
            self._reload_sessions(session["id"])
        elif session:
            tooltip(t("study_latest_turn_other_workspace"))

    def _render_session(self, session: dict):
        blocks = []
        artifacts = {item["artifact_id"]: item for item in session["artifacts"]}
        for message in session["messages"]:
            if message["type"] == "system_internal":
                snapshot = message.get("context_snapshot") or {}
                outcome = str(snapshot.get("outcome") or "")
                if (
                    self._workspace == "reviewer"
                    and snapshot.get("workspace") == "reviewer"
                    and outcome in {"understood", "needs_practice"}
                ):
                    blocks.append(
                        "<div style='margin:6px 0;padding:7px;border-radius:6px;"
                        "background:rgba(127,127,127,.12);font-size:12px'>"
                        f"{html.escape(t(f'study_coach_checkpoint_{outcome}'))}</div>"
                    )
                continue
            if message["type"] == "artifact_reference":
                if not self._policy.allows_card_mode:
                    continue
                artifact = artifacts.get(message.get("artifact_id"))
                label = artifact_label(artifact) if artifact else t("study_artifact_missing")
                artifact_id = quote(str(message.get("artifact_id") or ""), safe="")
                actions = ""
                if artifact:
                    compatible = artifact_is_compatible(artifact)
                    if not compatible:
                        label = t("study_artifact_stale_label", label=label)
                    actions = (
                        "<br>"
                        f"<a style='color:inherit;font-weight:600' href='forge-artifact://review/{artifact_id}'>"
                        f"{html.escape(t('study_review_artifact'))}</a>"
                    )
                    if compatible:
                        actions += (
                            " &nbsp;·&nbsp; "
                            f"<a style='color:inherit;font-weight:600' href='forge-artifact://open/{artifact_id}'>"
                            f"{html.escape(t('study_open_forge'))}</a>"
                        )
                    else:
                        actions += "<br>" + html.escape(t("study_artifact_stale_notice"))
                blocks.append(
                    "<div style='margin:8px 0;padding:10px;border-left:4px solid #d7a928;border-radius:6px;background:rgba(215,169,40,.12)'>"
                    f"<b>📦 {html.escape(label)}</b><br>{html.escape(message['content'])}{actions}</div>"
                )
                continue
            learner = message["role"] == "user"
            snapshot = message.get("context_snapshot") or {}
            message_workspace = str(snapshot.get("workspace") or self._workspace)
            label = (
                t("study_you") if learner
                else t(
                    "study_reviewer_ai"
                    if message_workspace == "reviewer" else "study_forge_ai"
                )
            )
            color = "rgba(53,111,164,0.16)" if learner else "rgba(255,255,255,0.07)"
            edge = "#4f8fbd" if learner else "#7f8c8d"
            content = html.escape(message["content"]).replace("\n", "<br>")
            blocks.append(
                f"<div style='margin:7px 0;padding:9px;border-left:3px solid {edge};"
                f"border-radius:6px;background:{color};'>"
                f"<b>{html.escape(label)}</b><br>{content}</div>"
            )
        self.transcript.setHtml("".join(blocks) or f"<p>{t('study_empty')}</p>")
        scrollbar = self.transcript.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.cbo_artifact.blockSignals(True)
        self.cbo_artifact.clear()
        if self._policy.allows_card_mode:
            for artifact in reversed(session["artifacts"]):
                label = artifact_label(artifact)
                if not artifact_is_compatible(artifact):
                    label = t("study_artifact_stale_label", label=label)
                self.cbo_artifact.addItem(label, artifact["artifact_id"])
        self.cbo_artifact.blockSignals(False)
        self._on_artifact_selected()
        self.status.setText(self._usage_text(session["id"]))

    def _usage_text(self, session_id: str) -> str:
        entries = [entry for entry in get_usage_entries() if entry.get("session_id") == session_id]
        totals = summarize_usage(entries)
        if not totals["calls"]:
            return t("study_ready")
        return t("study_usage", tokens=totals["total_tokens"], cost=totals["total_cost"])

    def _selected_artifact(self) -> Optional[dict]:
        if not self._policy.allows_card_mode:
            return None
        session = self._current_session()
        artifact_id = str(self.cbo_artifact.currentData() or "")
        return self._store.get_artifact(session["id"], artifact_id) if session and artifact_id else None

    def _on_artifact_selected(self, _index=-1):
        artifact = self._selected_artifact()
        available = artifact is not None
        compatible = available and artifact_is_compatible(artifact)
        self.btn_review_artifact.setEnabled(available)
        self.btn_forge.setEnabled(compatible)
        notice = "" if compatible or not available else t("study_artifact_stale_notice")
        self.cbo_artifact.setToolTip(notice)
        self.btn_review_artifact.setToolTip(notice)
        self.btn_forge.setToolTip(notice)

    def _on_transcript_link(self, url):
        """Route internal artifact links through the existing artifact owner."""
        if not self._policy.allows_card_mode or str(url.scheme()) != "forge-artifact":
            return
        action = str(url.host())
        artifact_id = unquote(str(url.path()).lstrip("/"))
        index = self.cbo_artifact.findData(artifact_id)
        if index < 0:
            return
        self.cbo_artifact.setCurrentIndex(index)
        if action == "review":
            self.review_artifact()
        elif action == "open":
            self.open_artifact_in_forge()

    def review_artifact(self):
        if not self._policy.allows_card_mode:
            return
        artifact = self._selected_artifact()
        if not artifact:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(artifact_label(artifact))
        dialog.resize(760, 560)
        apply_theme(dialog)
        layout = QVBoxLayout(dialog)
        if not artifact_is_compatible(artifact):
            notice = QLabel(t("study_artifact_stale_review"))
            notice.setWordWrap(True)
            layout.addWidget(notice)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(json.dumps(artifact["cards"], ensure_ascii=False, indent=2))
        layout.addWidget(text)
        close = QPushButton(t("chat_close"))
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()

    def open_artifact_in_forge(self):
        if not self._policy.allows_card_mode:
            return
        artifact = self._selected_artifact()
        if not artifact:
            return
        if not artifact_is_compatible(artifact):
            showInfo(t("study_artifact_stale_open_error"))
            return
        try:
            artifact_to_factory_payload(artifact)
            factory = getattr(mw, "factory_dialog", None)
            if factory is None:
                from ui.factory_dialog import start_smart_factory
                start_smart_factory()
                factory = getattr(mw, "factory_dialog", None)
            if factory is None or not hasattr(factory, "load_card_artifact"):
                raise RuntimeError("Factory is unavailable")
            factory.load_card_artifact(artifact)
            factory.show()
            factory.raise_()
            factory.activateWindow()
            tooltip(t("study_sent_forge"))
        except Exception as error:
            log_event(
                "AI_ARTIFACT_OPEN_FAILED", "keep_artifact_snapshot",
                error=error.__class__.__name__,
            )
            showInfo(t("study_artifact_open_error"))

    def _open_settings(self):
        from ui.ai_settings import show_ai_settings_dialog
        show_ai_settings_dialog(self)

    def toggle_collapsed(self):
        collapsed = self.body.isVisible()
        self.body.setVisible(not collapsed)
        self.btn_collapse.setText("+" if collapsed else "−")
        self._store.update_ui_state(collapsed=collapsed)

    def back_to_review(self):
        if self._dockable:
            self.hide()
            self._store.update_ui_state(visible=False)
        else:
            host = self.parentWidget()
            if isinstance(host, QDialog):
                host.hide()
            else:
                self.hide()
        if self._workspace == "forge":
            self._main_window.setFocus()
            return
        reviewer = getattr(self._main_window, "reviewer", None)
        web = getattr(reviewer, "web", None)
        if web is not None:
            web.setFocus()
        else:
            self._main_window.setFocus()

    def _on_top_level_changed(self, floating: bool):
        if floating:
            desired = (
                Qt.WindowType.WindowMinimizeButtonHint
                | Qt.WindowType.WindowMaximizeButtonHint
            )
            if self.windowFlags() & desired != desired:
                self.setWindowFlags(self.windowFlags() | desired)
                self.show()
        if not self._restoring:
            self._store.update_ui_state(floating=bool(floating))

    def _on_dock_location_changed(self, area):
        if not self._restoring:
            side = "left" if area == Qt.DockWidgetArea.LeftDockWidgetArea else "right"
            self._store.update_ui_state(dock_side=side)

    def _on_visibility_changed(self, visible: bool):
        if self._dockable and not self._restoring:
            self._store.update_ui_state(visible=bool(visible))

    def moveEvent(self, event):
        super().moveEvent(event)
        if self._dockable and not self._restoring and self.isFloating():
            self._geometry_timer.start(250)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._dockable and not self._restoring and self.isFloating():
            self._geometry_timer.start(250)

    def _persist_floating_geometry(self):
        if self._dockable and self.isFloating():
            self._store.update_ui_state(
                floating_x=self.x(), floating_y=self.y(),
                floating_width=self.width(), floating_height=self.height(),
            )


def get_ai_companion(main_window=None) -> AiCompanionDock:
    global _COMPANION
    owner = main_window or mw
    if _COMPANION is None:
        _COMPANION = AiCompanionDock(owner, workspace="reviewer")
    return _COMPANION


def refresh_ai_companion_context(snapshot: Optional[dict]) -> bool:
    """Update an existing Reviewer surface without creating or showing it."""
    if _COMPANION is None:
        return False
    _COMPANION.refresh_reviewer_context(snapshot)
    return True


class AiStudySessionDialog(QDialog):
    """Standalone Forge workshop over the shared Study Session backend."""

    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setObjectName("bentoForgeAiStudyDialog")
        self.setWindowTitle(t("study_forge_title"))
        self.setMinimumSize(760, 600)
        self.resize(980, 760)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.companion = AiCompanionDock(
            mw, workspace="forge", dockable=False, parent=self,
        )
        layout.addWidget(self.companion)
        apply_theme(self)

    def open_session(
        self,
        *,
        language="",
        initial_text="",
        source_text="",
        learning_mode="language",
        lane="vocab",
        existing_entries=None,
    ):
        apply_theme(self)
        self.companion._theme_cfg = apply_theme(self.companion)
        self.companion.open_for_context(
            language=language,
            initial_text=initial_text,
            source_text=source_text,
            learning_mode=learning_mode,
            lane=lane,
            existing_entries=existing_entries,
        )
        self.show()
        self.raise_()
        self.activateWindow()


def get_ai_study_dialog(parent=None) -> AiStudySessionDialog:
    global _STUDY_DIALOG
    if _STUDY_DIALOG is None:
        _STUDY_DIALOG = AiStudySessionDialog(parent or mw)
    return _STUDY_DIALOG


def show_ai_study_dialog(
    *, language="", initial_text="", source_text="", learning_mode="language", lane="vocab",
    existing_entries=None,
) -> AiStudySessionDialog:
    dialog = get_ai_study_dialog(mw)
    dialog.open_session(
        language=language,
        initial_text=initial_text,
        source_text=source_text,
        learning_mode=learning_mode,
        lane=lane,
        existing_entries=existing_entries,
    )
    return dialog


def show_ai_companion(
    *, snapshot: Optional[dict] = None, language: str = "", initial_text: str = "",
) -> AiCompanionDock:
    companion = get_ai_companion(mw)
    companion.open_for_context(snapshot, language=language, initial_text=initial_text)
    return companion


def toggle_ai_companion():
    if str(getattr(mw, "state", "")).lower() != "review":
        show_ai_study_dialog()
        return
    companion = get_ai_companion(mw)
    if companion.isVisible():
        companion.back_to_review()
    else:
        reviewer = getattr(mw, "reviewer", None)
        snapshot = None
        if reviewer is not None:
            try:
                from hooks.reviewer import get_current_card_snapshot
                snapshot = get_current_card_snapshot(reviewer)
            except Exception:
                snapshot = None
        companion.open_for_context(
            snapshot,
            language=str((snapshot or {}).get("language") or ""),
        )


def register_companion_shortcut() -> bool:
    """Register Ctrl+Shift+A only when another Anki action does not own it."""
    global _SHORTCUT_ACTION
    if _SHORTCUT_ACTION is not None:
        return True
    requested = QKeySequence("Ctrl+Shift+A")
    try:
        tools = getattr(getattr(mw, "form", None), "menuTools", None)
        if tools is None:
            return False
        conflict = False
        for action in mw.findChildren(QAction):
            shortcut = action.shortcut()
            if not shortcut.isEmpty() and shortcut == requested:
                logger.warning("AI_COMPANION_SHORTCUT_CONFLICT: Ctrl+Shift+A is already in use")
                conflict = True
                break
        action = QAction(t("study_menu_action"), mw)
        if not conflict:
            action.setShortcut(requested)
        action.triggered.connect(toggle_ai_companion)
        tools.addAction(action)
        _SHORTCUT_ACTION = action
        if (
            str(getattr(mw, "state", "")).lower() == "review"
            and StudySessionStore().get_ui_state().get("visible")
        ):
            get_ai_companion(mw).show()
        return not conflict
    except Exception as error:
        log_event(
            "AI_COMPANION_SHORTCUT_FAILED", "continue_without_shortcut",
            error=error.__class__.__name__,
        )
        return False


__all__ = [
    "AiCompanionDock", "AiStudySessionDialog", "get_ai_companion",
    "get_ai_study_dialog", "refresh_ai_companion_context",
    "register_companion_shortcut", "show_ai_companion",
    "show_ai_study_dialog", "toggle_ai_companion",
]
