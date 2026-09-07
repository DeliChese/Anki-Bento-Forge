"""Preview-and-apply dialog for upgrading one existing Language card."""

from __future__ import annotations

from aqt import mw
from aqt.qt import (
    QCheckBox, QDialog, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QTableWidget, QTableWidgetItem, Qt, QVBoxLayout,
)
from aqt.utils import askUser, showInfo

from Language import LANG_COLLOCATION_CONFIG, LANG_CONFIG, LANG_GRAMMAR_CONFIG
from utils.anki_ops import run_collection
from utils.card_upgrade import (
    CURRENT_QUALITY_VERSION, QUALITY_FIELD, apply_card_upgrade, build_upgrade_source,
    normalized_kind, proposed_field_changes, upgrade_instruction,
)
from utils.i18n import t
from utils.logger import get_logger
from utils.model_lifecycle import ensure_model
from utils.prompt_config import apply_field_map_to_cfg
from workers.card_upgrade_worker import CardUpgradeAiWorker, CardUpgradeAudioWorker


_OPEN_DIALOGS = {}
logger = get_logger()


def _config(language: str, kind: str) -> dict:
    registry = {"vocab": LANG_CONFIG, "grammar": LANG_GRAMMAR_CONFIG, "collocation": LANG_COLLOCATION_CONFIG}[kind]
    return apply_field_map_to_cfg(dict(registry[language]), language, kind)


def _apply_upgrade_with_current_template(
    col, *, cfg: dict, language: str, kind: str, note_type: str,
    note_id: int, expected_target: str, changes: list[dict],
    audio_tags: dict, mark_current: bool,
):
    """Update owned Bento template assets before writing the upgraded note."""
    from mode import (
        LANG_COLLOCATION_CSS, LANG_COLLOCATION_TEMPLATES,
        LANG_CSS, LANG_GRAMMAR_CSS, LANG_GRAMMAR_TEMPLATES, LANG_TEMPLATES,
    )
    from mode.card_render import build_afmt, build_qfmt

    assets = {
        "vocab": (LANG_TEMPLATES, LANG_CSS),
        "grammar": (LANG_GRAMMAR_TEMPLATES, LANG_GRAMMAR_CSS),
        "collocation": (LANG_COLLOCATION_TEMPLATES, LANG_COLLOCATION_CSS),
    }
    templates_by_lang, css_by_lang = assets[kind]
    sync_cfg = dict(cfg)
    sync_cfg["model_name"] = str(note_type or cfg["model_name"])
    sync_cfg["old_model_names"] = []
    ensure_model(
        col.models, sync_cfg, templates_by_lang[language], css_by_lang[language](),
        build_qfmt, build_afmt, rename_primary_template=False,
        prune_extra_templates=False,
    )
    return apply_card_upgrade(
        col, note_id, expected_target, cfg["detect_key"], changes,
        audio_tags, mark_current,
    )


class CardUpgradeDialog(QDialog):
    def __init__(self, reviewer, snapshot: dict):
        super().__init__(mw)
        self.reviewer, self.snapshot = reviewer, dict(snapshot or {})
        self.note_id = int(self.snapshot.get("note_id") or 0)
        self.kind = normalized_kind(self.snapshot.get("card_kind"))
        self.language = str(self.snapshot.get("language") or "")
        self.cfg = _config(self.language, self.kind)
        self.fields = dict(self.snapshot.get("bento_field_values") or {})
        self.candidate, self.changes = None, []
        self.ai_worker = self.audio_worker = None

        self.setWindowTitle(t("card_upgrade_title"))
        self.setModal(False)
        self.resize(880, 580)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        intro = QLabel(t("card_upgrade_desc", revision=CURRENT_QUALITY_VERSION))
        intro.setWordWrap(True)
        root.addWidget(intro)

        result_title = QLabel(t("card_upgrade_result_title"))
        result_title.setStyleSheet("font-weight: 600; margin-top: 8px;")
        root.addWidget(result_title)
        self.result_hint = QLabel(t("card_upgrade_result_empty"))
        self.result_hint.setWordWrap(True)
        self.result_hint.setStyleSheet(
            "padding: 8px 10px; border: 1px solid rgba(127,127,127,.35); "
            "border-radius: 7px;"
        )
        root.addWidget(self.result_hint)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([t("card_upgrade_field"), t("card_upgrade_before"), t("card_upgrade_after")])
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 310)
        self.table.setColumnWidth(2, 310)
        self.table.setMinimumHeight(280)
        self.table.setWordWrap(True)
        root.addWidget(self.table, 1)
        self.chk_audio = QCheckBox(t("card_upgrade_audio"))
        self.chk_audio.setChecked(True)
        root.addWidget(self.chk_audio)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        root.addWidget(self.progress)
        root.addWidget(self.status)
        actions = QHBoxLayout()
        self.btn_generate = QPushButton(t("card_upgrade_generate"))
        self.btn_apply = QPushButton(t("card_upgrade_apply"))
        self.btn_close = QPushButton(t("card_upgrade_close"))
        self.btn_apply.setEnabled(False)
        actions.addWidget(self.btn_generate)
        actions.addStretch(1)
        actions.addWidget(self.btn_apply)
        actions.addWidget(self.btn_close)
        root.addLayout(actions)
        self.btn_generate.clicked.connect(self._generate)
        self.btn_apply.clicked.connect(self._apply)
        self.btn_close.clicked.connect(self.close)

    def _set_busy(self, busy: bool, status: str = ""):
        self.progress.setVisible(busy)
        self.status.setText(status)
        self.btn_generate.setEnabled(not busy)
        self.btn_apply.setEnabled(not busy and self.candidate is not None)
        self.chk_audio.setEnabled(not busy)
        self.table.setEnabled(not busy)

    def _generate(self):
        if not askUser(t("card_upgrade_generate_confirm"), parent=self):
            return
        self.candidate, self.changes = None, []
        self.table.setRowCount(0)
        self.result_hint.setText(t("card_upgrade_generating"))
        self._set_busy(True, t("card_upgrade_generating"))
        self.ai_worker = CardUpgradeAiWorker(
            source=build_upgrade_source(self.snapshot, self.fields),
            instruction=upgrade_instruction(self.snapshot), language=self.language,
            kind=self.kind, snapshot=self.snapshot,
        )
        self.ai_worker.progress.connect(lambda value: self.status.setText(str(value)))
        self.ai_worker.finished.connect(self._on_candidate)
        self.ai_worker.error.connect(self._on_error)
        self.ai_worker.start()

    def _on_candidate(self, candidate: dict):
        try:
            self.candidate = dict(candidate or {})
            self.changes = proposed_field_changes(self.fields, self.candidate, self.cfg)
            self.table.setRowCount(len(self.changes))
            for row, change in enumerate(self.changes):
                name = QTableWidgetItem(change["field"])
                name.setCheckState(
                    Qt.CheckState.Checked if change["missing"]
                    else Qt.CheckState.Unchecked
                )
                name.setToolTip(t("card_upgrade_select_hint"))
                self.table.setItem(row, 0, name)
                self.table.setItem(row, 1, QTableWidgetItem(change["current"]))
                self.table.setItem(row, 2, QTableWidgetItem(change["proposed"]))
            self.table.resizeRowsToContents()
            if self.changes:
                message = t("card_upgrade_result_ready", count=len(self.changes))
            else:
                message = t("card_upgrade_no_changes")
            self.result_hint.setText(message)
            self._set_busy(False, message)
        except Exception as error:
            logger.exception("CARD_UPGRADE_RENDER_FAILED: %s", error)
            self.candidate, self.changes = None, []
            self.table.setRowCount(0)
            self._on_error(error)

    def _selected_changes(self) -> list[dict]:
        return [change for row, change in enumerate(self.changes)
                if self.table.item(row, 0) is not None
                and self.table.item(row, 0).checkState() == Qt.CheckState.Checked]

    def _apply(self):
        selected = self._selected_changes()
        if self.changes and not selected:
            showInfo(t("card_upgrade_select_required"), parent=self)
            return
        if not askUser(t("card_upgrade_apply_confirm"), parent=self):
            return
        audio_tasks = self._audio_tasks(selected) if self.chk_audio.isChecked() else []
        self._pending_changes = selected
        self._pending_mark_current = not self.changes or len(selected) == len(self.changes)
        if audio_tasks:
            self._set_busy(True, t("card_upgrade_audio_loading"))
            self.audio_worker = CardUpgradeAudioWorker(audio_tasks)
            self.audio_worker.progress.connect(lambda value: self.status.setText(t("card_upgrade_audio_progress", progress=value)))
            self.audio_worker.finished.connect(self._persist)
            self.audio_worker.error.connect(self._on_error)
            self.audio_worker.start()
            return
        self._persist({})

    def _audio_tasks(self, selected: list[dict]) -> list[dict]:
        proposed = {item["field"]: item["proposed"] for item in selected}
        selected_fields = set(proposed)
        tasks = []
        for audio_field, source_field in self.cfg.get("audio_fields") or []:
            source = proposed.get(source_field, str(self.fields.get(source_field) or "").strip())
            if source and (source_field in selected_fields or not str(self.fields.get(audio_field) or "").strip()):
                tasks.append({"field": audio_field, "text": source, "lang": self.cfg["lang_code"]})
        return tasks

    def _persist(self, audio_tags: dict):
        self._set_busy(True, t("card_upgrade_saving"))
        run_collection(
            self,
            lambda col: _apply_upgrade_with_current_template(
                col, cfg=self.cfg, language=self.language, kind=self.kind,
                note_type=self.snapshot.get("note_type", ""),
                note_id=self.note_id,
                expected_target=self.snapshot.get("current_target", ""),
                changes=self._pending_changes, audio_tags=audio_tags,
                mark_current=self._pending_mark_current,
            ),
            self._on_saved, self._on_error,
        )

    def _on_saved(self, result: dict):
        self._set_busy(False, t("card_upgrade_saved"))
        try:
            self.reviewer._redraw_current_card()
        except Exception as error:
            logger.debug("Card redraw after upgrade unavailable: %s", error)
        self.close()

    def _on_error(self, error):
        key = {
            "card_upgrade_identity_mismatch": "card_upgrade_identity_mismatch",
            "card_upgrade_stale_note": "card_upgrade_stale_note",
        }.get(str(error or ""))
        message = t(key) if key else t("card_upgrade_error", error=str(error or ""))
        self.result_hint.setText(message)
        self._set_busy(False, message)
        logger.warning("CARD_UPGRADE_FAILED: %s", error)
        showInfo(message, parent=self)

    def closeEvent(self, event):
        for worker in (self.ai_worker, self.audio_worker):
            if worker is not None and worker.isRunning():
                worker.stop()
        _OPEN_DIALOGS.pop(self.note_id, None)
        super().closeEvent(event)


def show_card_upgrade_dialog(reviewer, snapshot: dict):
    note_id = int((snapshot or {}).get("note_id") or 0)
    existing = _OPEN_DIALOGS.get(note_id)
    if existing is not None:
        existing.raise_()
        existing.activateWindow()
        return existing
    dialog = CardUpgradeDialog(reviewer, snapshot)
    _OPEN_DIALOGS[note_id] = dialog
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
    return dialog
