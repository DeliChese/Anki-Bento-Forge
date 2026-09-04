"""Network-only workers for Reviewer example regeneration."""

import threading

from aqt.qt import QThread, pyqtSignal

from audio import get_audio_multilang
from utils.review_example_ai import generate_review_example_with_ai


class ExampleAiWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, request: dict):
        super().__init__()
        self.request = dict(request or {})
        self.cancel_event = threading.Event()

    def run(self):
        try:
            result = generate_review_example_with_ai(
                **self.request,
                progress_callback=self.progress.emit,
                should_abort=self.cancel_event.is_set,
            )
            if self.cancel_event.is_set():
                return
            if result.get("error"):
                self.error.emit(str(result["error"]))
            else:
                self.finished.emit(result)
        except Exception as error:
            if not self.cancel_event.is_set():
                self.error.emit(str(error))

    def stop(self):
        self.cancel_event.set()


class ExampleAudioWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, text: str, lang_code: str):
        super().__init__()
        self.text = str(text or "").strip()
        self.lang_code = str(lang_code or "").strip()
        self.cancel_event = threading.Event()

    def run(self):
        try:
            tag = get_audio_multilang(
                self.text, self.lang_code, cancel_event=self.cancel_event,
            ) or ""
            if not self.cancel_event.is_set():
                self.finished.emit(tag)
        except Exception as error:
            if not self.cancel_event.is_set():
                self.error.emit(str(error))

    def stop(self):
        self.cancel_event.set()
