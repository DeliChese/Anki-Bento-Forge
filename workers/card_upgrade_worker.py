"""Network-only workers for an opt-in Reviewer card-quality upgrade."""

from __future__ import annotations

import threading

from aqt.qt import QThread, pyqtSignal

from audio import get_audio_multilang
from utils.ai_extractor import extract_grammar_with_ai, extract_vocabulary_with_ai
from utils.card_upgrade import select_upgrade_candidate


class CardUpgradeAiWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, *, source: str, instruction: str, language: str, kind: str, snapshot: dict):
        super().__init__()
        self.source, self.instruction = str(source), str(instruction)
        self.language, self.kind, self.snapshot = str(language), str(kind), dict(snapshot)
        self.cancel_event = threading.Event()

    def run(self):
        try:
            if self.kind == "grammar":
                cards = extract_grammar_with_ai(
                    self.source, self.language, self.instruction, existing_patterns=[],
                    force_refresh=True, progress_callback=self.progress.emit,
                    should_abort=self.cancel_event.is_set,
                )
            else:
                cards = extract_vocabulary_with_ai(
                    self.source, self.language, self.instruction, existing_words=[],
                    force_refresh=True, progress_callback=self.progress.emit,
                    should_abort=self.cancel_event.is_set, kind=self.kind,
                )
            if not self.cancel_event.is_set():
                self.finished.emit(select_upgrade_candidate(cards, self.snapshot))
        except Exception as error:
            if not self.cancel_event.is_set():
                self.error.emit(str(error))

    def stop(self):
        self.cancel_event.set()


class CardUpgradeAudioWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, tasks: list[dict]):
        super().__init__()
        self.tasks = [dict(task) for task in tasks]
        self.cancel_event = threading.Event()

    def run(self):
        try:
            tags = {}
            for index, task in enumerate(self.tasks, 1):
                if self.cancel_event.is_set():
                    return
                field = str(task.get("field") or "")
                text = str(task.get("text") or "").strip()
                if field and text:
                    tags[field] = get_audio_multilang(
                        text, str(task.get("lang") or ""), cancel_event=self.cancel_event,
                    ) or ""
                self.progress.emit(f"{index}/{len(self.tasks)}")
            if not self.cancel_event.is_set():
                self.finished.emit(tags)
        except Exception as error:
            if not self.cancel_event.is_set():
                self.error.emit(str(error))

    def stop(self):
        self.cancel_event.set()
