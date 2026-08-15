"""
AI Workers — Background threads for AI extract, AI chat, and audio preview.
"""

import os
import threading

from aqt.qt import QThread, pyqtSignal

from utils.logger import get_logger
from utils.i18n import t
from utils.ai_extractor import (
    extract_vocabulary_long_text,
    extract_grammar_long_text,
    chat_with_ai,
)

logger = get_logger()


class PreviewThread(QThread):
    """Thread preview giọng đọc Edge TTS."""

    done = pyqtSignal(str)  # filepath hoặc ""

    def __init__(self, text, voice_id, lang, speed=1.0, media_dir=""):
        super().__init__()
        self.text = text
        self.voice_id = voice_id
        self.lang = lang
        self.speed = speed
        self.media_dir = media_dir
        self.cancel_event = threading.Event()

    def run(self):
        try:
            from audio.tts import get_audio_edge_tts, _install_edge_tts
            from audio.engine import speed_to_edge_rate
            if not _install_edge_tts():
                self.done.emit("")
                return
            rate = speed_to_edge_rate(self.speed)
            tag = get_audio_edge_tts(self.text, self.voice_id, self.lang, rate=rate, cancel_event=self.cancel_event)
            if tag:
                filename = tag.replace("[sound:", "").replace("]", "")
                filepath = os.path.join(self.media_dir, filename)
                self.done.emit(filepath if os.path.exists(filepath) else "")
            else:
                self.done.emit("")
        except Exception as e:
            logger.warning("Preview error: %s", e)
            self.done.emit("")

    def stop(self):
        self.cancel_event.set()


class AiExtractThread(QThread):
    """Thread gọi AI trích xuất từ vựng."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, text, lang, custom_instruction="", existing_words=None, grammar=False, cancel_event=None):
        super().__init__()
        self.text = text
        self.lang = lang
        self.custom_instruction = custom_instruction
        self.existing_words = existing_words or []
        self.grammar = grammar
        self.cancel_event = cancel_event or threading.Event()

    def run(self):
        try:
            if self.cancel_event.is_set():
                return
            if self.existing_words:
                label = (
                    t("item_label_grammar_lower")
                    if self.grammar else t("item_label_vocab_lower")
                )
                self.progress.emit(t("status_deck_avoid", count=len(self.existing_words), label=label))

            if self.grammar:
                self.progress.emit(t("worker_progress_grammar"))
                result_list = extract_grammar_long_text(
                    self.text,
                    self.lang,
                    self.custom_instruction,
                    existing_patterns=self.existing_words,
                    progress_callback=lambda msg: self.progress.emit(msg),
                    should_abort=self.cancel_event.is_set,
                )
                empty_msg = t("empty_grammar")
            else:
                self.progress.emit(t("worker_progress_vocab"))
                result_list = extract_vocabulary_long_text(
                    self.text,
                    self.lang,
                    self.custom_instruction,
                    existing_words=self.existing_words,
                    progress_callback=lambda msg: self.progress.emit(msg),
                    should_abort=self.cancel_event.is_set,
                )
                empty_msg = t("empty_vocab")

            if self.cancel_event.is_set():
                return
            if not result_list:
                self.error.emit(empty_msg)
                return

            self.finished.emit(result_list)

        except Exception as e:
            if not self.cancel_event.is_set():
                self.error.emit(str(e))

    def stop(self):
        self.cancel_event.set()


class AiChatThread(QThread):
    """Thread gọi AI chat."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, message, lang, conversation_history=None, anki_context=None, cancel_event=None):
        super().__init__()
        self.message = message
        self.lang = lang
        self.conversation_history = conversation_history
        self.anki_context = anki_context
        self.cancel_event = cancel_event or threading.Event()

    def run(self):
        try:
            self.progress.emit(t("worker_progress_context"))
            result = chat_with_ai(
                user_message=self.message,
                lang=self.lang,
                conversation_history=self.conversation_history,
                progress_callback=lambda msg: self.progress.emit(msg),
                should_abort=self.cancel_event.is_set,
                anki_context=self.anki_context,
            )

            if self.cancel_event.is_set():
                return

            if result.get("error"):
                self.error.emit(result["error"])
                return

            self.finished.emit(result)

        except Exception as e:
            if not self.cancel_event.is_set():
                self.error.emit(str(e))

    def stop(self):
        self.cancel_event.set()
