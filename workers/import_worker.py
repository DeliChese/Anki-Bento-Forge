"""Network-only audio generation for an import.

Collection reads and writes are intentionally handled by Anki ``QueryOp`` and
``CollectionOp`` in the dialog; this worker never imports or accesses ``mw``.
"""

import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from aqt.qt import QThread, pyqtSignal

from audio import get_audio_multilang
from audio.engine import speed_to_edge_rate
from utils.logger import get_logger

logger = get_logger()
_MAX_AUDIO_WORKERS = 4


class ImportWorker(QThread):
    """Generate media tags from pre-read tasks without touching Collection."""

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, audio_tasks, speed=1.0):
        super().__init__()
        self.audio_tasks = list(audio_tasks)
        self.rate = speed_to_edge_rate(speed)
        self.cancel_event = threading.Event()

    def is_cancelled(self):
        return self.cancel_event.is_set()

    def run(self):
        total = len(self.audio_tasks)
        tags = {}
        executor = ThreadPoolExecutor(max_workers=_MAX_AUDIO_WORKERS)
        pending = {}
        task_iter = iter(self.audio_tasks)
        completed = 0
        try:
            while not self.cancel_event.is_set() and len(pending) < _MAX_AUDIO_WORKERS:
                task = next(task_iter, None)
                if task is None:
                    break
                pending[executor.submit(_generate_audio_safe, task["text"], task["lang"], self.rate, self.cancel_event)] = task

            while pending and not self.cancel_event.is_set():
                done, _ = wait(pending, timeout=0.1, return_when=FIRST_COMPLETED)
                for future in done:
                    task = pending.pop(future)
                    try:
                        tags[task["key"]] = future.result()
                    except Exception as exc:
                        logger.warning("Audio generation failed: %s", exc)
                        tags[task["key"]] = ""
                    completed += 1
                    self.progress.emit(completed, f"🎤 Audio: {completed}/{total}")
                    if not self.cancel_event.is_set():
                        next_task = next(task_iter, None)
                        if next_task is not None:
                            pending[executor.submit(_generate_audio_safe, next_task["text"], next_task["lang"], self.rate, self.cancel_event)] = next_task
            if not self.cancel_event.is_set():
                self.finished.emit({"audio_tags": tags, "cancelled": False})
        except Exception as exc:
            logger.warning("Import audio worker failed: %s", exc)
            if not self.cancel_event.is_set():
                self.error.emit(str(exc))
        finally:
            for future in pending:
                future.cancel()
            # Do not hold the UI while an in-flight network request returns.
            executor.shutdown(wait=False, cancel_futures=True)

    def stop(self):
        self.cancel_event.set()


def _generate_audio_safe(text: str, lang: str, rate: str, cancel_event=None) -> str:
    try:
        return get_audio_multilang(text, lang, rate=rate, cancel_event=cancel_event) or ""
    except Exception as exc:
        logger.warning("Audio generation error: %s", exc)
        return ""
