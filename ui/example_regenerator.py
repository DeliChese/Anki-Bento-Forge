"""Responsive Reviewer dialog for editing and versioning examples."""

from __future__ import annotations

from aqt import mw
from aqt.qt import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout,
)
from aqt.utils import askUser, showInfo

from utils.anki_ops import run_collection
from utils.example_note_ops import (
    activate_example_version,
    delete_example_version,
    save_example_version,
)
from utils.i18n import t
from workers.example_worker import ExampleAiWorker, ExampleAudioWorker


_OPEN_DIALOGS = {}
_LANG_CODES = {"japanese": "ja", "chinese": "zh", "korean": "ko", "english": "en"}


class ExampleRegeneratorDialog(QDialog):
    def __init__(self, reviewer, snapshot: dict, slot: int, state: dict):
        super().__init__(mw)
        self.reviewer = reviewer
        self.snapshot = dict(snapshot or {})
        self.note_id = int(self.snapshot.get("note_id") or 0)
        self.language = str(self.snapshot.get("language") or "")
        self.slot = int(slot)
        self.versions = list(state.get("versions") or [])
        self.current_index = int(state.get("active", -1))
        self.ai_worker = None
        self.audio_worker = None
        self._pending_record = None
        self._ai_result_text = ""

        self.setWindowTitle(t("example_regen_title", slot=self.slot))
        self.setModal(False)
        self.resize(680, 570)
        self._build_ui()
        self._load_current()

    def _build_ui(self):
        root = QVBoxLayout(self)
        intro = QLabel(t("example_regen_desc"))
        intro.setWordWrap(True)
        root.addWidget(intro)

        nav = QHBoxLayout()
        self.btn_prev = QPushButton("‹")
        self.lbl_counter = QLabel("0/0")
        self.btn_next = QPushButton("›")
        self.btn_delete = QPushButton(t("example_regen_delete"))
        nav.addWidget(self.btn_prev)
        nav.addWidget(self.lbl_counter)
        nav.addWidget(self.btn_next)
        nav.addStretch(1)
        nav.addWidget(self.btn_delete)
        root.addLayout(nav)

        options = QFormLayout()
        self.cbo_difficulty = QComboBox()
        for key in ("mixed", "beginner", "intermediate", "advanced"):
            self.cbo_difficulty.addItem(t(f"example_difficulty_{key}"), key)
        self.cbo_length = QComboBox()
        for key in ("short", "medium", "long"):
            self.cbo_length.addItem(t(f"example_length_{key}"), key)
        options.addRow(t("example_regen_difficulty"), self.cbo_difficulty)
        options.addRow(t("example_regen_length"), self.cbo_length)
        root.addLayout(options)

        self.txt_example = QPlainTextEdit()
        self.txt_example.setPlaceholderText(t("example_regen_example_placeholder"))
        self.txt_example.setMaximumHeight(105)
        self.txt_reading = QPlainTextEdit()
        self.txt_reading.setPlaceholderText(t("example_regen_reading_placeholder"))
        self.txt_reading.setMaximumHeight(85)
        self.txt_translation = QPlainTextEdit()
        self.txt_translation.setPlaceholderText(t("example_regen_translation_placeholder"))
        self.txt_translation.setMaximumHeight(85)
        form = QFormLayout()
        form.addRow(t("example_regen_example"), self.txt_example)
        form.addRow(t("example_regen_reading"), self.txt_reading)
        form.addRow(t("example_regen_translation"), self.txt_translation)
        root.addLayout(form)

        self.chk_audio = QCheckBox(t("example_regen_audio"))
        self.chk_audio.setChecked(True)
        root.addWidget(self.chk_audio)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        root.addWidget(self.progress)
        root.addWidget(self.lbl_status)

        actions = QHBoxLayout()
        self.btn_ai = QPushButton(t("example_regen_ai"))
        self.btn_save = QPushButton(t("example_regen_save"))
        self.btn_close = QPushButton(t("example_regen_close"))
        actions.addWidget(self.btn_ai)
        actions.addStretch(1)
        actions.addWidget(self.btn_save)
        actions.addWidget(self.btn_close)
        root.addLayout(actions)

        self.btn_prev.clicked.connect(lambda: self._activate(self.current_index - 1))
        self.btn_next.clicked.connect(lambda: self._activate(self.current_index + 1))
        self.btn_delete.clicked.connect(self._delete_current)
        self.btn_ai.clicked.connect(self._generate_ai)
        self.btn_save.clicked.connect(self._save_new_version)
        self.btn_close.clicked.connect(self.close)

    def _set_busy(self, busy: bool, status: str = ""):
        self.progress.setVisible(bool(busy))
        self.lbl_status.setText(status)
        for widget in (
            self.btn_prev, self.btn_next, self.btn_delete, self.btn_ai,
            self.btn_save, self.cbo_difficulty, self.cbo_length,
        ):
            widget.setEnabled(not busy)
        self.txt_example.setReadOnly(busy)
        self.txt_reading.setReadOnly(busy)
        self.txt_translation.setReadOnly(busy)

    def _load_current(self):
        record = (
            self.versions[self.current_index]
            if 0 <= self.current_index < len(self.versions) else {}
        )
        self.txt_example.setPlainText(str(record.get("text") or ""))
        self.txt_reading.setPlainText(str(record.get("reading") or ""))
        self.txt_translation.setPlainText(str(record.get("translation") or ""))
        total = len(self.versions)
        current = self.current_index + 1 if total else 0
        self.lbl_counter.setText(f"{current}/{total}")
        self.btn_prev.setEnabled(current > 1)
        self.btn_next.setEnabled(0 < current < total)
        self.btn_delete.setEnabled(bool(total))
        self._ai_result_text = ""

    def _existing_examples(self):
        values = []
        for index in range(1, 5):
            key = "example" if index == 1 else f"example{index}"
            value = str(self.snapshot.get(key) or "").strip()
            if value:
                values.append(value)
        values.extend(str(item.get("text") or "") for item in self.versions)
        return list(dict.fromkeys(value for value in values if value))

    def _generate_ai(self):
        if not askUser(t("example_regen_ai_confirm"), parent=self):
            return
        request = {
            "target": str(self.snapshot.get("current_target") or ""),
            "meaning": str(self.snapshot.get("meaning") or ""),
            "language": self.language,
            "card_kind": str(self.snapshot.get("card_kind") or "vocab"),
            "difficulty": str(self.cbo_difficulty.currentData() or "mixed"),
            "length": str(self.cbo_length.currentData() or "medium"),
            "existing_examples": self._existing_examples(),
        }
        self._set_busy(True, t("example_regen_ai_loading"))
        self.ai_worker = ExampleAiWorker(request)
        self.ai_worker.progress.connect(lambda message: self.lbl_status.setText(str(message)))
        self.ai_worker.finished.connect(self._on_ai_ready)
        self.ai_worker.error.connect(self._on_error)
        self.ai_worker.start()

    def _on_ai_ready(self, result: dict):
        self.txt_example.setPlainText(str(result.get("text") or ""))
        self.txt_reading.setPlainText(str(result.get("reading") or ""))
        self.txt_translation.setPlainText(str(result.get("translation") or ""))
        self._ai_result_text = self.txt_example.toPlainText().strip()
        self._set_busy(False, t("example_regen_ai_ready"))

    def _record_from_editor(self):
        text = self.txt_example.toPlainText().strip()
        if not text:
            showInfo(t("example_regen_text_required"), parent=self)
            return None
        return {
            "text": text,
            "reading": self.txt_reading.toPlainText().strip(),
            "translation": self.txt_translation.toPlainText().strip(),
            "audio": "",
            "source": "ai" if text == self._ai_result_text else "manual",
        }

    def _reusable_audio(self, text: str) -> str:
        for record in self.versions:
            if str(record.get("text") or "").strip() == text and record.get("audio"):
                return str(record["audio"])
        return ""

    def _save_new_version(self):
        record = self._record_from_editor()
        if record is None:
            return
        signature = (
            record["text"].strip(),
            record["reading"].strip(),
            record["translation"].strip(),
        )
        if any(
            (
                str(version.get("text") or "").strip(),
                str(version.get("reading") or "").strip(),
                str(version.get("translation") or "").strip(),
            ) == signature
            for version in self.versions
        ):
            showInfo(t("example_regen_duplicate"), parent=self)
            return
        if self.chk_audio.isChecked():
            reused = self._reusable_audio(record["text"])
            if reused:
                record["audio"] = reused
                self._persist_new(record)
                return
            self._pending_record = record
            self._set_busy(True, t("example_regen_audio_loading"))
            self.audio_worker = ExampleAudioWorker(
                record["text"], _LANG_CODES.get(self.language, "en"),
            )
            self.audio_worker.finished.connect(self._on_audio_ready)
            self.audio_worker.error.connect(self._on_error)
            self.audio_worker.start()
            return
        self._persist_new(record)

    def _on_audio_ready(self, audio_tag: str):
        record = dict(self._pending_record or {})
        self._pending_record = None
        audio_tag = str(audio_tag or "")
        if not audio_tag:
            self._set_busy(False, t("example_regen_audio_failed"))
            showInfo(t("example_regen_audio_failed"), parent=self)
            return
        record["audio"] = audio_tag
        self._persist_new(record)

    def _persist_new(self, record: dict):
        self._set_busy(True, t("example_regen_saving"))
        run_collection(
            self,
            lambda col: save_example_version(
                col, self.note_id, self.language, self.slot, record,
            ),
            self._on_operation_done,
            self._on_error,
        )

    def _activate(self, index: int):
        if index < 0 or index >= len(self.versions):
            return
        self._set_busy(True, t("example_regen_saving"))
        run_collection(
            self,
            lambda col: activate_example_version(
                col, self.note_id, self.language, self.slot, index,
            ),
            self._on_operation_done,
            self._on_error,
        )

    def _delete_current(self):
        if self.current_index < 0:
            return
        if not askUser(t("example_regen_delete_confirm"), parent=self):
            return
        index = self.current_index
        self._set_busy(True, t("example_regen_saving"))
        run_collection(
            self,
            lambda col: delete_example_version(
                col, self.note_id, self.language, self.slot, index,
            ),
            self._on_operation_done,
            self._on_error,
        )

    def _on_operation_done(self, result: dict):
        self.versions = list(result.get("versions") or [])
        self.current_index = int(result.get("current") or 0) - 1
        self._set_busy(False, t("example_regen_saved"))
        self._load_current()
        self._redraw_if_current()

    def _redraw_if_current(self):
        try:
            card = getattr(self.reviewer, "card", None)
            note = card.note() if card is not None else None
            if note is not None and int(getattr(note, "id", 0) or 0) == self.note_id:
                self.reviewer._redraw_current_card()
        except Exception:
            pass

    def _on_error(self, error):
        self._pending_record = None
        self._set_busy(False, "")
        message = str(error or "")
        key = {
            "example_version_duplicate": "example_regen_duplicate",
            "example_history_corrupt": "example_regen_history_corrupt",
        }.get(message)
        showInfo(t(key) if key else t("example_regen_error", error=message), parent=self)

    def closeEvent(self, event):
        for worker in (self.ai_worker, self.audio_worker):
            if worker is not None and worker.isRunning():
                worker.stop()
        _OPEN_DIALOGS.pop((self.note_id, self.slot), None)
        super().closeEvent(event)


def show_example_regenerator(reviewer, snapshot: dict, slot: int, state: dict):
    key = (int(snapshot.get("note_id") or 0), int(slot))
    existing = _OPEN_DIALOGS.get(key)
    if existing is not None:
        existing.raise_()
        existing.activateWindow()
        return existing
    dialog = ExampleRegeneratorDialog(reviewer, snapshot, slot, state)
    _OPEN_DIALOGS[key] = dialog
    dialog.show()
    return dialog
