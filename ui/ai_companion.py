"""Lazy dockable/floating AI Study Sessions companion for Anki Reviewer/Forge."""

from __future__ import annotations

import hashlib
import html
import json
import re
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import quote, unquote

from aqt import mw
from aqt.qt import (
    QAction, QCheckBox, QComboBox, QDialog, QDockWidget, QFileDialog, QFrame, QHBoxLayout, QInputDialog,
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
from utils.ai_context_manager import has_usable_card_context, minimal_card_context
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
    route_forge_lane,
)
from utils.i18n import get_language, t
from utils.logger import get_logger, log_event
from utils.language_identity import try_normalize_language
from utils.study_library import StudyLibraryStore, manifest_snapshot
from ui.theme import apply_theme
from workers.ai_workers import AiChatThread


logger = get_logger()
_COMPANION = None
_SHORTCUT_ACTION = None

_LANGUAGE_LABELS = {
    "japanese": "日本語", "chinese": "中文", "korean": "한국어", "english": "English",
}


def _format_transcript_inline(value: str) -> str:
    """Render a small safe Markdown subset suitable for a narrow QTextBrowser."""
    text = html.escape(str(value or ""), quote=False)
    code_fragments = []

    def keep_code(match):
        index = len(code_fragments)
        code_fragments.append(
            "<code style='background:rgba(127,127,127,.20);padding:2px 5px;"
            "border-radius:3px;font-family:monospace'>" + match.group(1) + "</code>"
        )
        return f"\x00CODE{index}\x00"

    text = re.sub(r"`([^`\n]+)`", keep_code, text)
    text = re.sub(r"\*\*\*([^*\n]+?)\*\*\*", r"<b><i>\1</i></b>", text)
    text = re.sub(r"\*\*([^*\n]+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", text)
    # Links remain non-clickable text: AI output must not create navigation.
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"<u>\1</u>", text)
    for index, fragment in enumerate(code_fragments):
        text = text.replace(f"\x00CODE{index}\x00", fragment)
    return text


def _markdown_table_cells(line: str) -> list[str]:
    value = str(line or "").strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [cell.strip() for cell in value.split("|")]


def _is_markdown_table_divider(line: str) -> bool:
    cells = _markdown_table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _format_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    """Use table HTML for compact data, cards for wide tables in the dock."""
    headers = headers or []
    if len(headers) > 2:
        cards = []
        for row in rows:
            entries = []
            for index, cell in enumerate(row):
                if cell:
                    label = headers[index] if index < len(headers) else ""
                    entries.append(
                        f"<div style='margin:3px 0'><b>{_format_transcript_inline(label)}:</b> "
                        f"{_format_transcript_inline(cell)}</div>"
                    )
            if entries:
                cards.append(
                    "<div style='margin:7px 0;padding:8px 10px;border-radius:6px;"
                    "background:rgba(127,127,127,.13)'>" + "".join(entries) + "</div>"
                )
        return "".join(cards)
    header_html = "".join(
        "<th style='padding:7px 8px;text-align:left;background:rgba(127,127,127,.18);"
        "font-weight:700'>" + _format_transcript_inline(cell) + "</th>"
        for cell in headers
    )
    rows_html = "".join(
        "<tr>" + "".join(
            "<td style='padding:7px 8px;vertical-align:top'>" + _format_transcript_inline(cell) + "</td>"
            for cell in row[:len(headers)]
        ) + "</tr>"
        for row in rows
    )
    return (
        "<table width='100%' cellspacing='0' cellpadding='0' style='margin:8px 0;border-collapse:collapse;"
        "font-size:14px;border:1px solid rgba(127,127,127,.32)'><thead><tr>"
        + header_html + "</tr></thead><tbody>" + rows_html + "</tbody></table>"
    )


def _format_transcript_markdown(value: str) -> str:
    """Turn common AI Markdown into safe, readable rich text for the transcript."""
    lines = str(value or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith("```"):
            language = html.escape(stripped[3:].strip())
            code_lines = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(html.escape(lines[index]))
                index += 1
            if index < len(lines):
                index += 1
            label = f"<div style='font-size:11px;opacity:.72'>{language}</div>" if language else ""
            blocks.append(
                label + "<pre style='margin:7px 0;padding:9px;white-space:pre-wrap;"
                "background:rgba(0,0,0,.18);border-radius:5px;font-family:monospace'>"
                + "\n".join(code_lines) + "</pre>"
            )
            continue
        if index + 1 < len(lines) and "|" in line and _is_markdown_table_divider(lines[index + 1]):
            headers = _markdown_table_cells(line)
            rows = []
            index += 2
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                rows.append(_markdown_table_cells(lines[index]))
                index += 1
            blocks.append(_format_markdown_table(headers, rows))
            continue
        heading = re.match(r"^(#{1,4})\s+(.+?)\s*$", stripped)
        if heading:
            level = min(4, len(heading.group(1)) + 2)
            blocks.append(
                f"<h{level} style='margin:11px 0 5px;font-size:16px;font-weight:700'>"
                f"{_format_transcript_inline(heading.group(2))}</h{level}>"
            )
            index += 1
            continue
        if re.fullmatch(r"(?:[-*_]\s*){3,}", stripped):
            blocks.append("<hr style='border:0;border-top:1px solid rgba(127,127,127,.38);margin:10px 0'>")
            index += 1
            continue
        if stripped.startswith("> "):
            blocks.append(
                "<blockquote style='margin:7px 0;padding:5px 9px;border-left:3px solid #7f8c8d;"
                "background:rgba(127,127,127,.10)'>" + _format_transcript_inline(stripped[2:]) + "</blockquote>"
            )
            index += 1
            continue
        unordered = re.match(r"^\s*[-*+]\s+(.+)$", line)
        ordered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if unordered or ordered:
            tag = "ul" if unordered else "ol"
            items = []
            pattern = r"^\s*[-*+]\s+(.+)$" if unordered else r"^\s*\d+[.)]\s+(.+)$"
            while index < len(lines):
                match = re.match(pattern, lines[index])
                if not match:
                    break
                items.append("<li style='margin:3px 0'>" + _format_transcript_inline(match.group(1)) + "</li>")
                index += 1
            blocks.append(f"<{tag} style='margin:6px 0;padding-left:22px'>" + "".join(items) + f"</{tag}>")
            continue
        paragraph = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate or candidate.startswith("```") or re.match(r"^(#{1,4})\s+", candidate):
                break
            if re.fullmatch(r"(?:[-*_]\s*){3,}", candidate) or candidate.startswith("> "):
                break
            if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", lines[index]):
                break
            if index + 1 < len(lines) and "|" in lines[index] and _is_markdown_table_divider(lines[index + 1]):
                break
            paragraph.append(candidate)
            index += 1
        blocks.append("<p style='margin:6px 0'>" + "<br>".join(
            _format_transcript_inline(item) for item in paragraph
        ) + "</p>")
    return "".join(blocks) or "<p></p>"


class AiCompanionDock(QDockWidget):
    """Workspace-parameterized surface over one shared Study Session backend."""

    def __init__(
        self, main_window, *, workspace="reviewer", dockable=True, parent=None,
        integrated=False, source_input=None,
    ):
        workspace = resolve_workspace(workspace)
        policy = get_workspace_policy(workspace)
        if workspace == "forge" and dockable:
            raise ValueError("Forge workspace is a Factory-integrated surface")
        super().__init__(t(policy.title_key), parent or main_window)
        self._workspace = workspace
        self._policy = policy
        self._dockable = bool(dockable)
        self._integrated = bool(integrated)
        self._external_source_input = source_input
        self.setObjectName(
            "bentoForgeReviewerWorkspace"
            if self._workspace == "reviewer" else "bentoForgeWorkshopWorkspace"
        )
        self.setMinimumWidth(380 if not self._integrated else 0)
        self.resize(520, 760)
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
        self._library = StudyLibraryStore()
        self._workflow = AiWorkflowCoordinator()
        self._card_context = None
        self._context_user_choice = None
        self._active_session_id = ""
        self._pending_session_id = ""
        self._pending_user_message_id = ""
        self._pending_card_mode = None
        self._pending_candidate_mode = False
        self._pending_request_token = ""
        self._pending_workspace_request = None
        self._scope_manifest = None
        self._existing_entries = []
        self._prepared_candidate_source_digest = ""
        self._learning_mode = "language"
        self._lane = "vocab"
        self._editing_latest = False
        self._restoring = True
        self._typing_phase = 0
        self._typing_active = False
        self._typing_timer = QTimer(self)
        self._typing_timer.setInterval(420)
        self._typing_timer.timeout.connect(self._advance_typing_indicator)
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
        margin = 4 if self._integrated else 10
        outer.setContentsMargins(margin, margin, margin, margin)
        outer.setSpacing(5 if self._integrated else 7)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        self.title_label = QLabel(f"<b>{t(self._policy.title_key)}</b>")
        self.title_label.setObjectName("forgeAiStationTitle")
        self.subtitle_label = QLabel(t(self._policy.subtitle_key))
        self.subtitle_label.setObjectName("forgeAiStationSubtitle")
        self.subtitle_label.setProperty("class", "dim")
        self.title_label.setVisible(not self._integrated)
        self.subtitle_label.setVisible(not self._integrated)
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)
        header.addLayout(title_box, 1)
        self.btn_collapse = QToolButton()
        self.btn_collapse.setText("−")
        self.btn_collapse.setToolTip(t("study_collapse"))
        self.btn_collapse.clicked.connect(self.toggle_collapsed)
        self.btn_collapse.setVisible(not self._integrated)
        header.addWidget(self.btn_collapse)
        outer.addLayout(header)

        self.context_board = QLabel()
        self.context_board.setObjectName("forgeAiContextBoard")
        self.context_board.setWordWrap(True)
        self.context_board.setVisible(not self._integrated)
        outer.addWidget(self.context_board)

        self.route_strip = QLabel(t("study_forge_route_strip"))
        self.route_strip.setObjectName("forgeAiRouteStrip")
        self.route_strip.setVisible(self._policy.shows_route_strip and not self._integrated)
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

        self.transcript = QTextBrowser()
        self.transcript.setObjectName("forgeAiTranscript")
        self.transcript.setOpenExternalLinks(False)
        self.transcript.setOpenLinks(False)
        self.transcript.anchorClicked.connect(self._on_transcript_link)
        self.transcript.setAccessibleName(t("study_conversation"))
        self.transcript.setMinimumHeight(120 if self._integrated else 140)
        body.addWidget(self.transcript, 1)

        self.typing_indicator = QLabel()
        self.typing_indicator.setObjectName("forgeAiTypingIndicator")
        self.typing_indicator.setVisible(False)
        body.addWidget(self.typing_indicator)

        language_row = QHBoxLayout()
        self.ai_language_label = QLabel(t("study_ai_language_label"))
        self.ai_language_label.setVisible(self._workspace == "reviewer")
        language_row.addWidget(self.ai_language_label)
        self.cbo_ai_language = QComboBox()
        self.cbo_ai_language.setAccessibleName(t("study_ai_language_label"))
        self.cbo_ai_language.setToolTip(t("study_ai_language_tip"))
        self.cbo_ai_language.addItem(t("study_ai_language_choose"), None)
        for language, label in _LANGUAGE_LABELS.items():
            self.cbo_ai_language.addItem(label, language)
        self.cbo_ai_language.setCurrentIndex(0)
        self.cbo_ai_language.setVisible(self._workspace == "reviewer")
        self.cbo_ai_language.currentIndexChanged.connect(self._on_ai_language_selected)
        language_row.addWidget(self.cbo_ai_language, 1)
        body.addLayout(language_row)

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
        owns_source_widget = self._external_source_input is None
        self.source_label.setVisible(self._policy.allows_source_context and owns_source_widget)
        if owns_source_widget:
            body.addWidget(self.source_label)
            self.source_input = QPlainTextEdit()
            self.source_input.setObjectName("forgeAiSourceInput")
            self.source_input.setPlaceholderText(t("study_forge_source_placeholder"))
            self.source_input.setAccessibleName(t("study_forge_source_label"))
            self.source_input.setMaximumHeight(105)
            self.source_input.setVisible(self._policy.allows_source_context)
            body.addWidget(self.source_input)
        else:
            self.source_input = self._external_source_input
        self.source_input.textChanged.connect(self._update_context_board)

        quick = QGridLayout()
        for index, (key, prompt_key) in enumerate(self._policy.quick_actions):
            button = QPushButton(t(key))
            button.setProperty("class", "stationAction")
            button.setToolTip(t("study_quick_tip"))
            button.clicked.connect(lambda _checked=False, value=prompt_key: self._set_quick_prompt(t(value)))
            button.setVisible(not self._integrated)
            quick.addWidget(button, index // 2, index % 2)
        body.addLayout(quick)

        coach = QVBoxLayout()
        self.coach_state = QLabel(t("study_coach_loop_idle"))
        self.coach_state.setObjectName("forgeAiCoachState")
        self.coach_state.setWordWrap(True)
        coach.addWidget(self.coach_state)
        coach_actions = QGridLayout()
        self.btn_card_drill = QPushButton(t("study_library_card_drill"))
        self.btn_card_drill.setProperty("class", "stationAction")
        self.btn_card_drill.clicked.connect(self.draft_card_drill)
        coach_actions.addWidget(self.btn_card_drill, 0, 0, 1, 2)
        self.btn_needs_practice = QPushButton(t("study_coach_needs_practice"))
        self.btn_needs_practice.setProperty("class", "stationAction")
        self.btn_needs_practice.clicked.connect(
            lambda: self.mark_coaching_outcome("needs_practice")
        )
        coach_actions.addWidget(self.btn_needs_practice, 1, 0)
        self.btn_understood = QPushButton(t("study_coach_understood"))
        self.btn_understood.setProperty("class", "primary")
        self.btn_understood.clicked.connect(
            lambda: self.mark_coaching_outcome("understood")
        )
        coach_actions.addWidget(self.btn_understood, 1, 1)
        for widget in (
            self.coach_state, self.btn_card_drill, self.btn_needs_practice, self.btn_understood,
        ):
            widget.setVisible(self._workspace == "reviewer")
        coach.addLayout(coach_actions)
        body.addLayout(coach)

        context_row = QHBoxLayout()
        self.chk_context = QCheckBox(t("study_use_card_context"))
        self.chk_context.setChecked(False)
        self.chk_context.setVisible(self._policy.allows_card_context)
        self.chk_context.toggled.connect(self._on_card_context_toggled)
        context_row.addWidget(self.chk_context, 1)
        self.cbo_lane = QComboBox()
        self.cbo_lane.addItem(t("study_forge_router_auto"), "auto")
        self.cbo_lane.addItem(t("study_forge_router_vocab"), "vocab")
        self.cbo_lane.addItem(t("study_forge_router_grammar"), "grammar")
        self.cbo_lane.setAccessibleName(t("study_forge_router_label"))
        self.cbo_lane.setVisible(self._policy.allows_card_mode and not self._integrated)
        self.cbo_lane.currentIndexChanged.connect(self._update_context_board)
        context_row.addWidget(self.cbo_lane)
        self.cbo_mode = QComboBox()
        self.cbo_mode.addItem(t("study_mode_chat"), None)
        if self._policy.allows_card_mode:
            self.cbo_mode.addItem(t("study_forge_mode_candidates"), "candidates")
            self.cbo_mode.addItem(t("study_forge_mode_artifact"), "artifact")
        self.cbo_mode.setAccessibleName(t("study_card_mode"))
        self.cbo_mode.setVisible(self._policy.allows_card_mode and not self._integrated)
        self.cbo_mode.currentIndexChanged.connect(self._update_context_board)
        context_row.addWidget(self.cbo_mode)
        body.addLayout(context_row)

        library_row = QHBoxLayout()
        self.btn_library = QPushButton(t("study_library_manage"))
        self.btn_library.clicked.connect(self.open_study_library)
        self.btn_library.setVisible(self._workspace == "reviewer")
        library_row.addWidget(self.btn_library)
        self.chk_follow_library_links = QCheckBox(t("study_library_follow_links"))
        self.chk_follow_library_links.setToolTip(t("study_library_follow_links_tip"))
        self.chk_follow_library_links.setVisible(self._workspace == "reviewer")
        library_row.addWidget(self.chk_follow_library_links, 1)
        body.addLayout(library_row)
        scope_row = QHBoxLayout()
        self.scope_label = QLabel(t("study_library_not_used"))
        self.scope_label.setObjectName("forgeAiScopeManifest")
        self.scope_label.setWordWrap(True)
        self.scope_label.setVisible(self._workspace == "reviewer")
        scope_row.addWidget(self.scope_label, 1)
        self.btn_scope_details = QToolButton()
        self.btn_scope_details.setText("…")
        self.btn_scope_details.setToolTip(t("study_library_scope_details"))
        self.btn_scope_details.clicked.connect(self.show_scope_details)
        self.btn_scope_details.setVisible(self._workspace == "reviewer")
        scope_row.addWidget(self.btn_scope_details)
        body.addLayout(scope_row)

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
        self._artifact_widgets = (
            self.cbo_artifact, self.btn_review_artifact, self.btn_forge,
        )
        for widget in self._artifact_widgets:
            widget.setVisible(self._policy.allows_card_mode and not self._integrated)
        body.addLayout(artifacts)

        self.composer = QFrame(self.body)
        self.composer.setObjectName("forgeAiComposer")
        composer_layout = QVBoxLayout(self.composer)
        composer_layout.setContentsMargins(8, 8, 8, 8)
        composer_layout.setSpacing(6)

        self.input = QTextEdit()
        self.input.setObjectName("forgeAiInstructionInput")
        self.input.setAcceptRichText(False)
        self.input.setPlaceholderText(t(self._policy.input_placeholder_key))
        self.input.setAccessibleName(t(self._policy.input_accessible_key))
        self.input.setMaximumHeight(80 if self._integrated else 115)
        if self._integrated:
            self.input.setMinimumHeight(60)
        self.input.textChanged.connect(self._update_context_board)
        composer_layout.addWidget(self.input)

        actions = QHBoxLayout()
        self.chk_create_card = QCheckBox()
        self.chk_create_card.setVisible(
            self._integrated and self._workspace == "forge"
            and self._policy.allows_card_mode
        )
        self.chk_create_card.toggled.connect(self._on_create_card_toggled)
        actions.addWidget(self.chk_create_card)
        self.btn_edit_latest = QPushButton(t("study_edit_latest"))
        self.btn_edit_latest.clicked.connect(self.edit_latest_message)
        self.btn_edit_latest.setVisible(not self._integrated)
        actions.addWidget(self.btn_edit_latest)
        self.btn_delete_latest = QPushButton(t("study_delete_latest"))
        self.btn_delete_latest.clicked.connect(self.delete_latest_message)
        self.btn_delete_latest.setVisible(not self._integrated)
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
        composer_layout.addLayout(actions)
        body.addWidget(self.composer)

        footer = QHBoxLayout()
        self.status = QLabel(t("study_ready"))
        self.status.setObjectName("forgeAiStatus")
        footer.addWidget(self.status, 1)
        back_key = "study_back_review" if self._workspace == "reviewer" else "study_close_workspace"
        self.btn_back = QPushButton(t(back_key))
        self.btn_back.clicked.connect(self.back_to_review)
        self.btn_back.setVisible(not self._integrated)
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

    def _set_typing_indicator(self, active: bool):
        """Show a lightweight, non-blocking typing cue while the worker is active."""
        self._typing_active = bool(active)
        if not self._typing_active:
            self._typing_timer.stop()
            self.typing_indicator.setVisible(False)
            return
        self._typing_phase = 0
        self._advance_typing_indicator()
        self.typing_indicator.setVisible(True)
        self._typing_timer.start()

    def _advance_typing_indicator(self):
        if not self._typing_active:
            return
        dots = ("", ".", "..", "...")[self._typing_phase % 4]
        self.typing_indicator.setText(t("study_typing", dots=dots))
        self._typing_phase += 1

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
                max(380, int(state.get("floating_width") or 520)),
                max(480, int(state.get("floating_height") or 760)),
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
        return try_normalize_language(language)

    def _selected_ai_language(self) -> Optional[str]:
        return try_normalize_language(self.cbo_ai_language.currentData())

    def _set_ai_language(self, language: str = ""):
        normalized = self._resolve_language(language)
        index = self.cbo_ai_language.findData(normalized) if normalized else 0
        self.cbo_ai_language.blockSignals(True)
        self.cbo_ai_language.setCurrentIndex(index if index >= 0 else 0)
        self.cbo_ai_language.blockSignals(False)

    def _on_ai_language_selected(self, _index):
        """Switch language by switching sessions; never relabel existing history."""
        if self._restoring or self._workspace != "reviewer":
            return
        language = self._selected_ai_language()
        if language is None:
            return
        current = self._current_session()
        if current and current.get("language") == language:
            self._update_context_board()
            return
        matching = next(
            (item for item in self._store.list_sessions() if item.get("language") == language),
            None,
        )
        if matching:
            self._reload_sessions(matching["id"])
            return
        self.new_session(language=language)

    def new_session(self, *, language: str = "", deck: str = ""):
        language = self._resolve_language(language) or self._selected_ai_language()
        if language is None:
            self.status.setText(t("study_language_required"))
            return None
        provider, model = self._default_provider_model()
        title = t("study_default_title")
        session = self._store.create_session(
            language=language, title=title, provider=provider, model=model,
            optional_deck_context={"deck": deck} if deck else None,
        )
        self._set_ai_language(language)
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
        self._set_ai_language(session.get("language"))
        self._set_provider_model(session.get("provider"), session.get("model"))
        self._render_session(session)
        if self._workspace == "reviewer":
            latest_scope = next((
                (item.get("context_snapshot") or {}).get("study_scope")
                for item in reversed(session.get("messages", []))
                if item.get("role") == "user"
                and isinstance(item.get("context_snapshot"), dict)
                and (item.get("context_snapshot") or {}).get("study_scope")
            ), None)
            self._set_scope_manifest(latest_scope)
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
        self._card_context = self._accepted_reviewer_context(snapshot)
        self._set_context_checked(
            bool(self._card_context) and self._context_user_choice is not False
        )
        self._learning_mode = (
            str(learning_mode or "language").strip().casefold()
            if self._workspace == "forge" else "language"
        )
        self._lane = str(lane or "vocab").strip().casefold()
        if self._workspace == "forge":
            self.cbo_lane.setCurrentIndex(0)
        self._sync_create_card_control()
        self._existing_entries = (
            list(existing_entries or ()) if self._workspace == "forge" else []
        )
        self._prepared_candidate_source_digest = ""
        if self._workspace == "forge":
            self.source_input.setPlainText(source_text or "")
        else:
            self.source_input.clear()
        current = self._current_session()
        language = self._resolve_language(
            language or str((snapshot or {}).get("language") or "")
        )
        if language:
            self._set_ai_language(language)
        else:
            language = str((current or {}).get("language") or self._selected_ai_language() or "")
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
            safe_context = minimal_card_context(
                self._card_context,
                include_answer=str((self._card_context or {}).get("side") or "question") == "answer",
            )
            context_enabled = (
                has_usable_card_context(safe_context) and self.chk_context.isChecked()
            )
            checkpoint = latest_reviewer_checkpoint(
                (session or {}).get("messages", []), self._card_context,
            )
            outcome = str((checkpoint or {}).get("outcome") or "idle")
            self.coach_state.setText(t(f"study_coach_loop_{outcome}"))
            for button in (self.btn_card_drill, self.btn_needs_practice, self.btn_understood):
                button.setEnabled(has_usable_card_context(safe_context))
            mode = str((self._card_context or {}).get("study_mode") or "-").upper()
            side_key = (
                "study_context_answer_side"
                if str((self._card_context or {}).get("side") or "question") == "answer"
                else "study_context_question_side"
            )
            target = " ".join(str(
                safe_context.get("current_target")
                or safe_context.get("pattern")
                or safe_context.get("front")
                or safe_context.get("meaning")
                or safe_context.get("question")
                or safe_context.get("concept")
                or ""
            ).split())[:80]
            card_label = (
                t("study_context_card_attached_target", target=html.escape(target))
                if context_enabled else t("study_context_card_not_sent")
            )
            self.context_board.setText(t(
                "study_context_reviewer",
                language=language_label,
                mode=mode,
                side=t(side_key),
                card=card_label,
            ))
            return
        lane = (
            "knowledge" if self._learning_mode == "knowledge"
            else self._resolved_forge_lane(self.input.toPlainText())
        )
        lane_label = t(f"study_context_lane_{lane}")
        if (
            self._learning_mode == "language"
            and str(self.cbo_lane.currentData() or "auto") == "auto"
        ):
            lane_label = t("study_forge_router_result", lane=lane_label)
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

    @staticmethod
    def _accepted_reviewer_context(snapshot: Optional[dict]) -> Optional[dict]:
        """Accept usable card fields even when a custom Note Type has no language map."""
        if not isinstance(snapshot, dict):
            return None
        safe_context = minimal_card_context(
            snapshot,
            include_answer=str(snapshot.get("side") or "question") == "answer",
        )
        return dict(snapshot) if has_usable_card_context(safe_context) else None

    def _set_context_checked(self, checked: bool):
        self.chk_context.blockSignals(True)
        self.chk_context.setChecked(bool(checked))
        self.chk_context.blockSignals(False)

    def _on_card_context_toggled(self, checked: bool):
        self._context_user_choice = bool(checked)
        self._update_context_board()

    def refresh_reviewer_context(self, snapshot: Optional[dict]):
        """Refresh the current card/side without opening or raising the dock."""
        if self._workspace != "reviewer":
            return
        self._card_context = self._accepted_reviewer_context(snapshot)
        if self._card_context and self._context_user_choice is None:
            self._set_context_checked(True)
        elif not self._card_context:
            self._set_context_checked(False)
        self._update_context_board()

    def _refresh_current_reviewer_card(self):
        """Re-read the Reviewer card at send time so requests cannot use stale context."""
        if self._workspace != "reviewer":
            return
        snapshot = None
        reviewer = getattr(mw, "reviewer", None)
        if reviewer is not None and str(getattr(mw, "state", "")).casefold() == "review":
            try:
                from hooks.reviewer import get_current_card_snapshot

                snapshot = get_current_card_snapshot(reviewer)
            except Exception as error:
                log_event(
                    "AI_CARD_CONTEXT_REFRESH_FAILED", "disable_stale_card_context",
                    error=error.__class__.__name__,
                )
        self.refresh_reviewer_context(snapshot)

    def _set_quick_prompt(self, prompt: str):
        self.input.setPlainText(prompt)
        self.input.setFocus()

    def _sync_create_card_control(self):
        checkbox = getattr(self, "chk_create_card", None)
        if checkbox is None:
            return
        lane = self._lane if self._lane in {"vocab", "grammar"} else "vocab"
        checkbox.setText(t(
            "study_create_card_grammar" if lane == "grammar"
            else "study_create_card_vocab"
        ))
        checkbox.setToolTip(t("study_create_card_tip"))
        checkbox.setVisible(
            self._integrated and self._workspace == "forge"
            and self._policy.allows_card_mode
            and self._learning_mode == "language"
        )

    def _on_create_card_toggled(self, checked: bool):
        """Map the compact checkbox to the existing artifact contract."""
        if not self._integrated or self._workspace != "forge":
            return
        target = "artifact" if checked else None
        index = self.cbo_mode.findData(target)
        self.cbo_mode.blockSignals(True)
        self.cbo_mode.setCurrentIndex(index if index >= 0 else 0)
        self.cbo_mode.blockSignals(False)
        self._update_context_board()

    def _resolved_forge_lane(self, instruction: str = "") -> str:
        """Resolve Auto/Vocab/Grammar before starting a Forge request."""
        if self._workspace != "forge" or self._learning_mode != "language":
            return "knowledge" if self._learning_mode == "knowledge" else "vocab"
        if self._integrated:
            return self._lane if self._lane in {"vocab", "grammar"} else "vocab"
        selected = str(self.cbo_lane.currentData() or "auto")
        if selected in {"vocab", "grammar"}:
            return selected
        return route_forge_lane(
            self.source_input.toPlainText(), instruction, fallback=self._lane,
        )

    def draft_card_drill(self):
        """Prepare a Reviewer-only micro-drill; never call AI or mutate SRS."""
        if self._workspace != "reviewer":
            return
        if not self._card_context:
            tooltip(t("study_coach_context_required"))
            return
        self._set_quick_prompt(t("study_library_card_drill_prompt"))
        self.status.setText(t("study_library_card_drill_ready"))

    def _set_scope_manifest(self, manifest: Optional[dict]):
        self._scope_manifest = dict(manifest) if isinstance(manifest, dict) else None
        if not self._scope_manifest:
            self.scope_label.setText(t("study_library_not_used"))
            return
        status = self._scope_manifest.get("status")
        sources = list(self._scope_manifest.get("sources") or ())
        if status == "grounded" and sources:
            first = sources[0]
            self.scope_label.setText(t(
                "study_library_scope_line",
                pack=first.get("pack_name") or "-",
                heading=self._scope_heading(first),
                count=len(sources),
            ))
        else:
            status_key = {
                "no_enabled_packs": "study_library_scope_no_enabled_packs",
                "no_match": "study_library_scope_no_match",
                "ambiguous": "study_library_scope_ambiguous",
            }.get(status, "study_library_not_used")
            self.scope_label.setText(t(status_key))

    @staticmethod
    def _scope_heading(source: dict) -> str:
        """Prefer a verified numbered section over a generic document chunk label."""
        number = source.get("section_number")
        title = str(source.get("section_title") or "").strip()
        if number is not None and title:
            return f"{number}. {title}"
        return str(source.get("heading") or "-")

    def show_scope_details(self):
        manifest = self._scope_manifest
        if not manifest:
            tooltip(t("study_library_not_used"))
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(t("study_library_scope_details"))
        dialog.resize(720, 460)
        layout = QVBoxLayout(dialog)
        details = QPlainTextEdit(dialog)
        details.setReadOnly(True)
        lines = [
            t("study_library_scope_status", status=manifest.get("status", "-")),
            t("study_library_scope_confidence", value=manifest.get("confidence", 0)),
            t("study_library_scope_budget", count=manifest.get("context_chars", 0)),
        ]
        for index, source in enumerate(manifest.get("sources") or (), start=1):
            lines.append(t(
                "study_library_scope_source",
                index=index,
                pack=source.get("pack_name", "-"),
                heading=self._scope_heading(source),
                provenance=source.get("provenance", "-"),
                reason=source.get("reason", "-"),
            ))
        details.setPlainText("\n".join(lines))
        layout.addWidget(details)
        close = QPushButton(t("study_library_close"))
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        apply_theme(dialog)
        dialog.exec()

    def _choose_scope_candidates(self, manifest: dict) -> list[str]:
        candidates = list(manifest.get("candidates") or ())
        dialog = QDialog(self)
        dialog.setWindowTitle(t("study_library_scope_choose"))
        dialog.resize(760, 420)
        layout = QVBoxLayout(dialog)
        label = QLabel(t("study_library_scope_ambiguous_help"))
        label.setWordWrap(True)
        layout.addWidget(label)
        table = QTableWidget(len(candidates), 3, dialog)
        table.setHorizontalHeaderLabels([
            t("study_library_pack"), t("study_library_heading"), t("study_library_reason"),
        ])
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        for row, candidate in enumerate(candidates):
            pack_item = QTableWidgetItem(str(candidate.get("pack_name") or ""))
            pack_item.setData(Qt.ItemDataRole.UserRole, candidate.get("chunk_id"))
            table.setItem(row, 0, pack_item)
            table.setItem(row, 1, QTableWidgetItem(str(candidate.get("heading") or "")))
            table.setItem(row, 2, QTableWidgetItem(str(candidate.get("reason") or "")))
        if candidates:
            table.selectRow(0)
        layout.addWidget(table)
        actions = QHBoxLayout()
        cancel = QPushButton(t("study_library_cancel"))
        use = QPushButton(t("study_library_use_section"))
        use.setProperty("class", "primary")
        cancel.clicked.connect(dialog.reject)
        use.clicked.connect(dialog.accept)
        actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(use)
        layout.addLayout(actions)
        apply_theme(dialog)
        if not dialog.exec():
            return []
        row = table.currentRow()
        if row < 0:
            return []
        return [str(table.item(row, 0).data(Qt.ItemDataRole.UserRole) or "")]

    def open_study_library(self):
        """Manage profile-owned packs for the current session language."""
        if self._workspace != "reviewer":
            return
        session = self._current_session()
        language = try_normalize_language((session or {}).get("language"))
        if not language:
            showInfo(t("study_language_required"))
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(t("study_library_title", language=_LANGUAGE_LABELS[language]))
        dialog.resize(820, 500)
        layout = QVBoxLayout(dialog)
        intro = QLabel(t("study_library_intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        table = QTableWidget(0, 5, dialog)
        table.setHorizontalHeaderLabels([
            t("study_library_enabled"), t("study_library_pack"),
            t("study_library_type"), t("study_library_size"), t("study_library_chunks"),
        ])
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(table, 1)

        def refresh():
            packs = self._library.list_packs(language)
            table.blockSignals(True)
            table.setRowCount(len(packs))
            for row, pack in enumerate(packs):
                enabled = QTableWidgetItem("")
                enabled.setFlags(enabled.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                enabled.setCheckState(
                    Qt.CheckState.Checked if pack["enabled"] else Qt.CheckState.Unchecked
                )
                enabled.setData(Qt.ItemDataRole.UserRole, pack["pack_id"])
                table.setItem(row, 0, enabled)
                table.setItem(row, 1, QTableWidgetItem(pack["name"]))
                table.setItem(row, 2, QTableWidgetItem(pack["source_type"].upper()))
                table.setItem(row, 3, QTableWidgetItem(t("study_library_bytes", count=pack["text_bytes"])))
                table.setItem(row, 4, QTableWidgetItem(str(pack["chunk_count"])))
            table.blockSignals(False)

        def toggle_pack(item):
            if item.column() != 0:
                return
            self._library.set_enabled(
                language,
                str(item.data(Qt.ItemDataRole.UserRole) or ""),
                item.checkState() == Qt.CheckState.Checked,
            )

        def add_file():
            filepath, _selected = QFileDialog.getOpenFileName(
                dialog, t("study_library_add"), "",
                t("study_library_file_filter"),
            )
            if not filepath:
                return
            default_name = Path(filepath).stem
            pack_name, accepted = QInputDialog.getText(
                dialog, t("study_library_pack_name"),
                t("study_library_pack_name_prompt"), text=default_name,
            )
            if not accepted or not pack_name.strip():
                return
            try:
                self._library.add_pack_from_file(language, filepath, name=pack_name.strip())
            except Exception as error:
                logger.warning("Study Library ingest failed: %s", error)
                showInfo(t("study_library_error", error=str(error)[:180]))
                return
            refresh()
            self.status.setText(t("study_library_added"))

        def selected_pack_id() -> str:
            row = table.currentRow()
            return str(table.item(row, 0).data(Qt.ItemDataRole.UserRole) or "") if row >= 0 else ""

        def delete_selected():
            pack_id = selected_pack_id()
            if not pack_id:
                return
            if QMessageBox.question(
                dialog, t("study_library_delete"), t("study_library_delete_confirm"),
            ) == QMessageBox.StandardButton.Yes:
                self._library.delete_pack(language, pack_id)
                refresh()

        def clear_all():
            if QMessageBox.question(
                dialog, t("study_library_clear"), t("study_library_clear_confirm"),
            ) == QMessageBox.StandardButton.Yes:
                self._library.clear_language(language)
                refresh()

        table.itemChanged.connect(toggle_pack)
        actions = QHBoxLayout()
        add = QPushButton(t("study_library_add"))
        delete = QPushButton(t("study_library_delete"))
        clear = QPushButton(t("study_library_clear"))
        close = QPushButton(t("study_library_close"))
        add.clicked.connect(add_file)
        delete.clicked.connect(delete_selected)
        clear.clicked.connect(clear_all)
        close.clicked.connect(dialog.accept)
        actions.addWidget(add)
        actions.addWidget(delete)
        actions.addWidget(clear)
        actions.addStretch()
        actions.addWidget(close)
        layout.addLayout(actions)
        refresh()
        apply_theme(dialog)
        dialog.exec()
        self._set_scope_manifest(None)

    def _resolve_library_context(
        self, language: str, text: str, *, card_context: Optional[dict] = None,
    ) -> Optional[dict]:
        if self._workspace != "reviewer":
            return None
        card_target = next(
            (str((card_context or {}).get(key) or "").strip()
             for key in (
                 "current_target", "pattern", "front", "simplified", "traditional",
                 "question", "concept", "meaning",
             )
             if str((card_context or {}).get(key) or "").strip()),
            "",
        )[:240]
        retrieval_query = f"{text}\n{card_target}".strip()
        resolved = self._library.resolve_scope(
            language, retrieval_query,
            follow_links=self.chk_follow_library_links.isChecked(),
        )
        manifest = resolved["manifest"]
        if manifest.get("status") == "ambiguous":
            selected = self._choose_scope_candidates(manifest)
            if not selected:
                self._set_scope_manifest(manifest)
                self.status.setText(t("study_library_scope_waiting"))
                return None
            resolved = self._library.resolve_scope(
                language, retrieval_query,
                follow_links=self.chk_follow_library_links.isChecked(),
                selected_chunk_ids=selected,
            )
            manifest = resolved["manifest"]
        self._set_scope_manifest(manifest)
        return resolved

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
        if self._integrated and self._workspace == "forge":
            selected_mode = "artifact" if self.chk_create_card.isChecked() else None
        else:
            selected_mode = (
                self.cbo_mode.currentData() if self._policy.allows_card_mode else None
            )
        text = self.input.toPlainText().strip()
        if selected_mode == "candidates" and not text:
            text = t("study_candidates_default_instruction")
        if not text:
            return
        self._refresh_current_reviewer_card()
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
        resolved_lane = self._resolved_forge_lane(text)
        request_context = build_workspace_request_context(
            workspace=self._workspace,
            language=session["language"],
            user_instruction=text,
            request_token=request_token,
            learning_mode=self._learning_mode,
            lane=resolved_lane,
            source_text=(
                self.source_input.toPlainText() if self._workspace == "forge" else ""
            ),
            card_context=self._card_context,
            use_card_context=(
                self._workspace == "reviewer" and self.chk_context.isChecked()
            ),
        )
        study_library_context = self._resolve_library_context(
            session["language"], text, card_context=request_context.card_context,
        )
        if self._workspace == "reviewer" and study_library_context is None:
            return
        message_snapshot = request_context.to_snapshot()
        if isinstance(study_library_context, dict):
            message_snapshot["study_scope"] = manifest_snapshot(
                study_library_context.get("manifest") or {}
            )
        if (
            selected_mode == "artifact"
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
                context_snapshot=message_snapshot,
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
                context_snapshot=message_snapshot,
            )
        self._pending_user_message_id = user_message["id"]
        self._pending_session_id = session["id"]
        self._pending_candidate_mode = selected_mode == "candidates"
        self._pending_card_mode = (
            resolved_lane if selected_mode == "artifact" else None
        )
        self._pending_request_token = request_token
        self._pending_workspace_request = request_context
        self._prepared_candidate_source_digest = ""
        self.input.clear()
        self._reload_sessions(session["id"])
        self.btn_send.setEnabled(False)
        self.btn_stop.setVisible(True)
        self.status.setText(t("study_thinking"))
        self._set_typing_indicator(True)
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
            study_library_context=study_library_context,
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
        self._set_typing_indicator(False)
        self.btn_send.setEnabled(True)
        self.btn_stop.setVisible(False)
        self.cbo_mode.setCurrentIndex(0)
        if self._integrated:
            self.chk_create_card.setChecked(False)
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
                lane_index = self.cbo_lane.findData(candidate_manifest.get("lane"))
                if lane_index >= 0:
                    self.cbo_lane.setCurrentIndex(lane_index)
                mode_index = self.cbo_mode.findData("artifact")
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
            content = (
                html.escape(str(message["content"] or "")).replace("\n", "<br>")
                if learner else _format_transcript_markdown(message["content"])
            )
            content_style = "font-size:13px;line-height:1.5" if learner else "font-size:14px;line-height:1.58"
            blocks.append(
                f"<div style='margin:7px 0;padding:9px;border-left:3px solid {edge};"
                f"border-radius:6px;background:{color};'>"
                f"<b>{html.escape(label)}</b><div style='{content_style}'>{content}</div></div>"
            )
        self.transcript.setHtml("".join(blocks) or f"<p>{t('study_empty')}</p>")
        if self._integrated:
            self.transcript.setVisible(bool(blocks))
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
        show_artifacts = (
            self._policy.allows_card_mode
            and (not self._integrated or self.cbo_artifact.count() > 0)
        )
        for widget in self._artifact_widgets:
            widget.setVisible(show_artifacts)
        if self._integrated:
            has_owned_user_turn = any(
                message.get("role") == "user"
                and isinstance(message.get("context_snapshot"), dict)
                and message["context_snapshot"].get("workspace") == self._workspace
                for message in session["messages"]
            )
            self.btn_edit_latest.setVisible(has_owned_user_turn)
            self.btn_delete_latest.setVisible(has_owned_user_turn)
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
        if self._dockable:
            self._store.update_ui_state(collapsed=collapsed)

    def back_to_review(self):
        if self._integrated:
            self._main_window.setFocus()
            return
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


def show_integrated_forge(
    *, language="", initial_text="", source_text="", learning_mode="language", lane="vocab",
    existing_entries=None,
) -> AiCompanionDock:
    """Open the Factory-owned Forge panel; never create a standalone dialog."""
    from ui.factory_dialog import start_smart_factory

    factory = start_smart_factory()
    factory.open_integrated_forge(
        language=language,
        initial_text=initial_text,
        source_text=source_text,
        learning_mode=learning_mode,
        lane=lane,
        existing_entries=existing_entries,
    )
    return factory.forge_panel


def show_ai_companion(
    *, snapshot: Optional[dict] = None, language: str = "", initial_text: str = "",
) -> AiCompanionDock:
    companion = get_ai_companion(mw)
    companion.open_for_context(snapshot, language=language, initial_text=initial_text)
    return companion


def toggle_ai_companion():
    if str(getattr(mw, "state", "")).lower() != "review":
        showInfo(t("study_reviewer_only"))
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
    "AiCompanionDock", "get_ai_companion",
    "refresh_ai_companion_context",
    "register_companion_shortcut", "show_ai_companion",
    "show_integrated_forge", "toggle_ai_companion",
]
