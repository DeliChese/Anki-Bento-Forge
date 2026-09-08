"""Opt-in sequential AI upgrade for all notes in the selected Bento Note Type."""

from __future__ import annotations

from aqt import mw
from aqt.qt import (
    QDialog, QHBoxLayout, QLabel, QProgressBar, QPushButton, QTimer, QVBoxLayout,
)
from aqt.utils import askUser, showInfo

from utils.anki_ops import run_collection, run_query
from utils.bulk_card_upgrade import apply_bulk_upgrade_candidate, build_bulk_upgrade_plan
from utils.card_upgrade import build_upgrade_source, upgrade_instruction
from utils.i18n import t
from utils.logger import get_logger
from workers.card_upgrade_worker import CardUpgradeAiWorker


logger = get_logger()
_OPEN_DIALOGS = {}


def _notes_for_model(col, model_name: str) -> list:
    model = col.models.by_name(str(model_name))
    if model is None:
        return []
    note_ids = col.find_notes(f"mid:{int(model['id'])}")
    return [col.get_note(note_id) for note_id in note_ids]


class BulkCardUpgradeDialog(QDialog):
    """Scan, confirm and process one selected Language Note Type at a time."""

    def __init__(self, parent, *, cfg: dict, language: str, kind: str):
        super().__init__(parent or mw)
        self.cfg, self.language, self.kind = dict(cfg), str(language), str(kind)
        self.plan = {"total": 0, "ai_required": 0, "template_only": 0, "snapshots": []}
        self.index = self.updated = self.failed = 0
        self.cancelled = False
        self.worker = None
        self.setWindowTitle(t("bulk_upgrade_title"))
        self.setModal(False)
        self.resize(620, 260)
        self._build_ui()
        self._scan()

    def _build_ui(self):
        root = QVBoxLayout(self)
        intro = QLabel(t("bulk_upgrade_desc"))
        intro.setWordWrap(True)
        root.addWidget(intro)
        self.summary = QLabel(t("bulk_upgrade_scanning"))
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet("padding: 9px; border: 1px solid rgba(127,127,127,.35); border-radius: 7px;")
        root.addWidget(self.summary)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        root.addWidget(self.progress)
        actions = QHBoxLayout()
        self.start_button = QPushButton(t("bulk_upgrade_start"))
        self.cancel_button = QPushButton(t("bulk_upgrade_cancel"))
        self.close_button = QPushButton(t("card_upgrade_close"))
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        actions.addWidget(self.start_button)
        actions.addStretch(1)
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.close_button)
        root.addLayout(actions)
        self.start_button.clicked.connect(self._start)
        self.cancel_button.clicked.connect(self._cancel)
        self.close_button.clicked.connect(self.close)

    def _scan(self):
        self.start_button.setEnabled(False)
        run_query(
            self,
            lambda col: build_bulk_upgrade_plan(
                _notes_for_model(col, self.cfg["model_name"]), self.cfg,
                language=self.language, kind=self.kind,
            ),
            self._on_scanned,
            self._on_error,
        )

    def _on_scanned(self, plan: dict):
        self.plan = dict(plan or self.plan)
        self.summary.setText(t(
            "bulk_upgrade_summary",
            total=self.plan["total"], ai=self.plan["ai_required"], template=self.plan["template_only"],
        ))
        if not self.plan["total"]:
            self.status.setText(t("bulk_upgrade_empty"))
            return
        if not self.plan["ai_required"]:
            self.status.setText(t("bulk_upgrade_template_ready"))
            return
        self.start_button.setEnabled(True)
        self.status.setText(t("bulk_upgrade_ready"))

    def _start(self):
        count = self.plan["ai_required"]
        if not count:
            return
        if not askUser(t("bulk_upgrade_confirm", count=count), parent=self):
            return
        self.index = self.updated = self.failed = 0
        self.cancelled = False
        self.progress.setRange(0, count)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.close_button.setEnabled(False)
        self._next()

    def _next(self):
        if self.cancelled or self.index >= self.plan["ai_required"]:
            self._finish()
            return
        snapshot = self.plan["snapshots"][self.index]
        self.status.setText(t(
            "bulk_upgrade_progress", current=self.index + 1,
            total=self.plan["ai_required"], target=snapshot["current_target"],
        ))
        self.worker = CardUpgradeAiWorker(
            source=build_upgrade_source(snapshot, snapshot["bento_field_values"]),
            instruction=upgrade_instruction(snapshot), language=self.language,
            kind=self.kind, snapshot=snapshot,
        )
        self.worker.finished.connect(lambda candidate: self._save_candidate(snapshot, candidate))
        self.worker.error.connect(lambda error: self._skip(snapshot, error))
        self.worker.start()

    def _save_candidate(self, snapshot: dict, candidate: dict):
        if self.cancelled:
            self._finish()
            return
        run_collection(
            self,
            lambda col: apply_bulk_upgrade_candidate(col, snapshot, candidate, self.cfg),
            lambda result: self._saved(snapshot, result),
            lambda error: self._skip(snapshot, error),
        )

    def _saved(self, _snapshot: dict, result: dict):
        self.updated += 1
        self._advance()

    def _skip(self, snapshot: dict, error):
        self.failed += 1
        logger.warning("BULK_CARD_UPGRADE_SKIPPED note=%s error=%s", snapshot.get("note_id"), error)
        self._advance()

    def _advance(self):
        self.index += 1
        self.progress.setValue(self.index)
        # Keep provider calls gentle while preserving one-note-at-a-time safety.
        QTimer.singleShot(1_500, self._next)

    def _cancel(self):
        self.cancelled = True
        self.cancel_button.setEnabled(False)
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
        self._finish()

    def _finish(self):
        self.worker = None
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        self.status.setText(t(
            "bulk_upgrade_done", updated=self.updated, failed=self.failed,
            total=self.plan["ai_required"],
        ))

    def _on_error(self, error):
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.status.setText(t("bulk_upgrade_error", error=str(error or "")))
        logger.warning("BULK_CARD_UPGRADE_FAILED: %s", error)
        showInfo(self.status.text(), parent=self)

    def closeEvent(self, event):
        self._cancel()
        _OPEN_DIALOGS.pop((self.language, self.kind), None)
        super().closeEvent(event)


def show_bulk_card_upgrade_dialog(parent, *, cfg: dict, language: str, kind: str):
    key = (str(language), str(kind))
    existing = _OPEN_DIALOGS.get(key)
    if existing is not None:
        existing.raise_()
        existing.activateWindow()
        return existing
    dialog = BulkCardUpgradeDialog(parent, cfg=cfg, language=language, kind=kind)
    _OPEN_DIALOGS[key] = dialog
    dialog.show()
    return dialog
