"""V18.2 contextual AI surfaces with a shared V18.1.1 backend.

Reviewer remains a current-card tutor. Forge gets a source-oriented workshop.
The module installs thin UI wrappers around ``ui.ai_companion`` so no provider,
session, artifact, validation, or request-ownership contract is forked.
"""

from __future__ import annotations

from typing import Optional

from aqt import mw
from aqt.qt import QDialog, QLabel, QPushButton, QVBoxLayout, Qt

from utils.ai_workspace_policy import (
    WORKSPACE_FORGE,
    WORKSPACE_REVIEWER,
    forge_context_line,
    get_workspace_policy,
    reviewer_context_line,
)
from utils.i18n import get_language, t
from utils.language_identity import try_normalize_language
from ui.theme import apply_theme

from . import ai_companion as _ai_companion


_INSTALLED = False
_FORGE_DIALOG = None
_ORIGINAL_GET_COMPANION = None
_ORIGINAL_SHOW_COMPANION = None
_ORIGINAL_GET_STUDY_DIALOG = None
_ORIGINAL_SHOW_STUDY_DIALOG = None

_ORIGINAL_QUICK_KEYS = (
    "study_quick_explain",
    "study_quick_contrast",
    "study_quick_usage",
    "study_quick_example",
    "study_quick_check",
    "study_quick_hint",
)

_STATION_STYLE = """
QWidget#forgeAiCompanionRoot[stationSurface="reviewer"],
QWidget#forgeAiCompanionRoot[stationSurface="forge"] {
    border-radius: 16px;
}
QLabel#stationContext {
    padding: 8px 11px;
    border: 1px solid rgba(120, 160, 190, 0.30);
    border-radius: 10px;
    background: rgba(110, 150, 180, 0.10);
    font-size: 11px;
    font-weight: 650;
}
QLabel#stationRoute {
    padding: 7px 10px;
    border-radius: 9px;
    background: rgba(90, 130, 160, 0.08);
    font-size: 10px;
    letter-spacing: 1px;
}
QTextBrowser#stationTranscript {
    border-radius: 13px;
    padding: 4px;
}
QTextEdit#stationInput {
    border-radius: 12px;
    padding: 8px;
}
QPushButton[stationQuick="true"] {
    min-height: 30px;
    padding: 5px 9px;
    border-radius: 9px;
    font-weight: 600;
}
QPushButton[stationPrimary="true"] {
    min-height: 32px;
    padding-left: 14px;
    padding-right: 14px;
    border-radius: 10px;
    font-weight: 700;
}
"""


def _ui_lang() -> str:
    return "en" if get_language() == "en" else "vi"


def _replace_header_copy(dock, workspace: str) -> None:
    policy = get_workspace_policy(workspace)
    ui_lang = _ui_lang()
    old_title = t("study_title")
    old_subtitle = t("study_subtitle")
    for label in dock.findChildren(QLabel):
        plain = str(label.text() or "")
        if plain in {old_title, f"<b>{old_title}</b>"} or label.property("stationHeader") == "title":
            label.setProperty("stationHeader", "title")
            label.setText(f"<b>{policy.title(ui_lang)}</b>")
        elif plain == old_subtitle or label.property("stationHeader") == "subtitle":
            label.setProperty("stationHeader", "subtitle")
            label.setText(policy.subtitle(ui_lang))


def _ensure_station_banner(dock, *, workspace: str) -> QLabel:
    banner = getattr(dock, "_station_context_label", None)
    if banner is None:
        banner = QLabel()
        banner.setObjectName("stationContext")
        banner.setWordWrap(True)
        dock._station_context_label = banner
        layout = dock.body.layout()
        layout.insertWidget(0, banner)
    banner.setProperty("stationWorkspace", workspace)
    return banner


def _ensure_route_label(dock) -> QLabel:
    route = getattr(dock, "_station_route_label", None)
    if route is None:
        route = QLabel("SOURCE  →  AI  →  ARTIFACT  →  XƯỞNG")
        route.setObjectName("stationRoute")
        route.setAlignment(Qt.AlignmentFlag.AlignCenter)
        route.setWordWrap(True)
        dock._station_route_label = route
        dock.body.layout().insertWidget(1, route)
    return route


def _apply_station_style(dock, workspace: str) -> None:
    root = dock.widget()
    root.setProperty("stationSurface", workspace)
    root.style().unpolish(root)
    root.style().polish(root)
    dock.transcript.setObjectName("stationTranscript")
    dock.input.setObjectName("stationInput")
    dock.btn_send.setProperty("stationPrimary", True)
    if not dock.property("stationStyleApplied"):
        dock.setStyleSheet((dock.styleSheet() or "") + _STATION_STYLE)
        dock.setProperty("stationStyleApplied", True)


def _discover_quick_buttons(dock) -> list[QPushButton]:
    existing = []
    for button in dock.findChildren(QPushButton):
        value = button.property("stationQuickIndex")
        if value is not None:
            try:
                existing.append((int(value), button))
            except (TypeError, ValueError):
                continue
    if len(existing) >= 6:
        return [button for _, button in sorted(existing)[:6]]

    labels = {t(key): index for index, key in enumerate(_ORIGINAL_QUICK_KEYS)}
    discovered = []
    for button in dock.findChildren(QPushButton):
        index = labels.get(button.text())
        if index is None:
            continue
        button.setProperty("stationQuickIndex", index)
        discovered.append((index, button))
    return [button for _, button in sorted(discovered)]


def _disconnect_button(button: QPushButton) -> None:
    try:
        button.clicked.disconnect()
    except (TypeError, RuntimeError):
        return


def _set_reviewer_action(dock, prompt: str) -> None:
    dock.input.setPlainText(prompt)
    dock.input.setFocus()


def _set_forge_action(dock, prompt: str) -> None:
    source = dock.input.toPlainText().strip()
    if source:
        if prompt not in source:
            dock.input.setPlainText(f"{source}\n\n---\n{prompt}")
    else:
        dock.input.setPlainText(prompt)
    dock.input.setFocus()


def _wire_quick_actions(dock, workspace: str) -> None:
    actions = get_workspace_policy(workspace).actions
    ui_lang = _ui_lang()
    buttons = _discover_quick_buttons(dock)
    if len(buttons) != len(actions):
        return
    for button, action in zip(buttons, actions):
        button.setProperty("stationQuick", True)
        button.setText(action.label(ui_lang))
        button.setToolTip(action.prompt(ui_lang))
        _disconnect_button(button)
        prompt = action.prompt(ui_lang)
        if workspace == WORKSPACE_FORGE:
            button.clicked.connect(
                lambda _checked=False, value=prompt, owner=dock: _set_forge_action(owner, value)
            )
        else:
            button.clicked.connect(
                lambda _checked=False, value=prompt, owner=dock: _set_reviewer_action(owner, value)
            )


def _refresh_reviewer_context(dock) -> None:
    banner = _ensure_station_banner(dock, workspace=WORKSPACE_REVIEWER)
    snapshot = dock._card_context if dock.chk_context.isChecked() else None
    banner.setText(reviewer_context_line(snapshot, ui_lang=_ui_lang()))


def _factory_lane() -> Optional[str]:
    factory = getattr(mw, "factory_dialog", None)
    if factory is None or getattr(factory, "_learning_mode", "language") != "language":
        return None
    return "grammar" if bool(getattr(factory, "_is_grammar", False)) else "vocab"


def _refresh_forge_context(dock) -> None:
    banner = _ensure_station_banner(dock, workspace=WORKSPACE_FORGE)
    session = dock._current_session()
    language = str((session or {}).get("language") or "")
    explicit_mode = dock.cbo_mode.currentData()
    mode = explicit_mode or _factory_lane()
    banner.setText(forge_context_line(
        language,
        card_mode=mode,
        source_chars=len(dock.input.toPlainText()),
        ui_lang=_ui_lang(),
    ))


def _connect_once(owner, signal, callback, marker: str) -> None:
    if owner.property(marker):
        return
    signal.connect(callback)
    owner.setProperty(marker, True)


def decorate_reviewer_companion(dock) -> None:
    """Turn the shared dock into a clearly scoped current-card study coach."""
    _replace_header_copy(dock, WORKSPACE_REVIEWER)
    _apply_station_style(dock, WORKSPACE_REVIEWER)
    _wire_quick_actions(dock, WORKSPACE_REVIEWER)
    dock.input.setPlaceholderText(
        "Hỏi về thẻ hiện tại, xin gợi ý hoặc kiểm tra hiểu biết…"
        if _ui_lang() == "vi" else
        "Ask about the current card, request a hint, or check your understanding…"
    )
    dock.btn_back.setText("← Reviewer")
    _refresh_reviewer_context(dock)
    _connect_once(
        dock.chk_context,
        dock.chk_context.toggled,
        lambda _checked=False, owner=dock: _refresh_reviewer_context(owner),
        "stationReviewerContextConnected",
    )


def _close_forge_workspace(dock) -> None:
    host = dock.parentWidget()
    if isinstance(host, QDialog):
        host.hide()
    else:
        dock.hide()
    factory = getattr(mw, "factory_dialog", None)
    if factory is not None:
        factory.show()
        factory.raise_()
        factory.activateWindow()


def decorate_forge_workspace(dock) -> None:
    """Make Forge a source/candidate/artifact workstation, never a fake Reviewer."""
    _replace_header_copy(dock, WORKSPACE_FORGE)
    _apply_station_style(dock, WORKSPACE_FORGE)
    _wire_quick_actions(dock, WORKSPACE_FORGE)
    _ensure_route_label(dock)

    dock.chk_context.setChecked(False)
    dock.chk_context.setVisible(False)
    dock.cbo_mode.setItemText(0, "Trao đổi" if _ui_lang() == "vi" else "Chat")
    dock.cbo_mode.setItemText(1, "Tạo Vocab Artifact" if _ui_lang() == "vi" else "Build Vocab Artifact")
    dock.cbo_mode.setItemText(2, "Tạo Grammar Artifact" if _ui_lang() == "vi" else "Build Grammar Artifact")
    dock.input.setPlaceholderText(
        "Dán nguồn / yêu cầu sản xuất ở đây. Forge AI không có current card; hãy nạp nguồn hoặc chọn một hành động bên trên."
        if _ui_lang() == "vi" else
        "Paste source / production instructions here. Forge AI has no current card; load source or choose an action above."
    )
    dock.btn_back.setText("← Trở về Xưởng" if _ui_lang() == "vi" else "← Back to Factory")
    _disconnect_button(dock.btn_back)
    dock.btn_back.clicked.connect(lambda _checked=False, owner=dock: _close_forge_workspace(owner))

    _refresh_forge_context(dock)
    _connect_once(
        dock.cbo_session,
        dock.cbo_session.currentIndexChanged,
        lambda _index=-1, owner=dock: _refresh_forge_context(owner),
        "stationForgeSessionConnected",
    )
    _connect_once(
        dock.cbo_mode,
        dock.cbo_mode.currentIndexChanged,
        lambda _index=-1, owner=dock: _refresh_forge_context(owner),
        "stationForgeModeConnected",
    )
    _connect_once(
        dock.input,
        dock.input.textChanged,
        lambda owner=dock: _refresh_forge_context(owner),
        "stationForgeInputConnected",
    )


class ForgeAiWorkspaceDialog(QDialog):
    """Source-oriented Forge surface backed by the canonical Study Session engine."""

    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setObjectName("bentoForgeAiWorkshopDialog")
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
        self.companion = _ai_companion.AiCompanionDock(mw, dockable=False, parent=self)
        layout.addWidget(self.companion)
        apply_theme(self)
        decorate_forge_workspace(self.companion)
        self._refresh_title()

    def _refresh_title(self) -> None:
        self.setWindowTitle(get_workspace_policy(WORKSPACE_FORGE).title(_ui_lang()))

    def open_session(self, *, language: str = "", initial_text: str = ""):
        canonical = try_normalize_language(language) or ""
        apply_theme(self)
        self.companion._theme_cfg = apply_theme(self.companion)
        self.companion.open_for_context(
            snapshot=None,
            language=canonical,
            initial_text=initial_text,
        )
        self.companion.chk_context.setChecked(False)
        decorate_forge_workspace(self.companion)
        self._refresh_title()
        self.show()
        self.raise_()
        self.activateWindow()


def get_forge_ai_workspace(parent=None) -> ForgeAiWorkspaceDialog:
    global _FORGE_DIALOG
    if _FORGE_DIALOG is None:
        _FORGE_DIALOG = ForgeAiWorkspaceDialog(parent or mw)
    return _FORGE_DIALOG


def show_forge_ai_workspace(*, language: str = "", initial_text: str = "") -> ForgeAiWorkspaceDialog:
    dialog = get_forge_ai_workspace(mw)
    dialog.open_session(language=language, initial_text=initial_text)
    return dialog


def install_ai_workspace_overrides() -> None:
    """Install contextual surfaces while preserving the canonical AI engine."""
    global _INSTALLED
    global _ORIGINAL_GET_COMPANION, _ORIGINAL_SHOW_COMPANION
    global _ORIGINAL_GET_STUDY_DIALOG, _ORIGINAL_SHOW_STUDY_DIALOG
    if _INSTALLED:
        return

    _ORIGINAL_GET_COMPANION = _ai_companion.get_ai_companion
    _ORIGINAL_SHOW_COMPANION = _ai_companion.show_ai_companion
    _ORIGINAL_GET_STUDY_DIALOG = _ai_companion.get_ai_study_dialog
    _ORIGINAL_SHOW_STUDY_DIALOG = _ai_companion.show_ai_study_dialog

    def get_reviewer_companion(main_window=None):
        dock = _ORIGINAL_GET_COMPANION(main_window or mw)
        decorate_reviewer_companion(dock)
        return dock

    def show_reviewer_companion(
        *, snapshot: Optional[dict] = None, language: str = "", initial_text: str = "",
    ):
        dock = get_reviewer_companion(mw)
        dock.open_for_context(snapshot, language=language, initial_text=initial_text)
        decorate_reviewer_companion(dock)
        return dock

    _ai_companion.get_ai_companion = get_reviewer_companion
    _ai_companion.show_ai_companion = show_reviewer_companion
    _ai_companion.get_ai_study_dialog = get_forge_ai_workspace
    _ai_companion.show_ai_study_dialog = show_forge_ai_workspace
    _INSTALLED = True


__all__ = [
    "ForgeAiWorkspaceDialog", "decorate_forge_workspace",
    "decorate_reviewer_companion", "get_forge_ai_workspace",
    "install_ai_workspace_overrides", "show_forge_ai_workspace",
]
