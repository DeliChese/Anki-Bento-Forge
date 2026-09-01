"""
Batch Workers — Background threads for batch word list processing and deck organization.
"""

import threading

from aqt.qt import QThread, pyqtSignal

from utils.logger import get_logger
from utils.i18n import t
from utils.ai_inventory_scanner import scan_inventory_with_ai
from utils.batch_processor import (
    process_large_word_list,
    organize_decks_with_ai,
    estimate_batch_cost,
    parse_word_list,
)

logger = get_logger()


class InventoryScanThread(QThread):
    """Scan a noisy source into a source-anchored supervised inventory."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, source, lang, custom_instruction="", grammar=False):
        super().__init__()
        self.source = dict(source or {})
        self.lang = lang
        self.custom_instruction = custom_instruction
        self.grammar = bool(grammar)
        self.cancel_event = threading.Event()

    def run(self):
        try:
            if self.cancel_event.is_set():
                return
            result = scan_inventory_with_ai(
                self.source,
                self.lang,
                grammar=self.grammar,
                custom_instruction=self.custom_instruction,
                progress_callback=self.progress.emit,
                should_abort=self.cancel_event.is_set,
            )
            if not self.cancel_event.is_set():
                self.finished.emit(result)
        except Exception as error:
            logger.warning("AI inventory scan error: %s", error)
            if not self.cancel_event.is_set():
                self.error.emit(str(error))

    def stop(self):
        self.cancel_event.set()


class BatchProcessThread(QThread):
    """
    Thread xử lý danh sách từ vựng lớn qua AI.
    
    Flow:
    1. Parse & validate
    2. Batch process từng nhóm từ
    3. Gộp kết quả
    """

    progress = pyqtSignal(str)           # Status text
    batch_progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(list)           # vocab_list
    error = pyqtSignal(str)               # Error message

    def __init__(self, raw_text, lang, custom_instruction="", existing_words=None, batch_size=10, grammar=False, slow_mode=False):
        super().__init__()
        self.raw_text = raw_text
        self.lang = lang
        self.custom_instruction = custom_instruction
        self.existing_words = existing_words or []
        self.batch_size = batch_size
        self.grammar = grammar
        self.slow_mode = slow_mode
        self.cancel_event = threading.Event()
        self.last_report = {}

    def run(self):
        try:
            if self.cancel_event.is_set():
                return

            # Báo cáo ước tính
            word_count = len(parse_word_list(self.raw_text, self.lang))
            estimate = estimate_batch_cost(
                word_count, self.lang, self.batch_size, grammar=self.grammar,
            )
            self.progress.emit(t(
                "batch_worker_estimate",
                batches=estimate["estimated_batches"],
                cost=estimate["estimated_cost_usd"],
                seconds=estimate["estimated_time_seconds"],
            ))

            vocab_list = process_large_word_list(
                raw_text=self.raw_text,
                lang=self.lang,
                custom_instruction=self.custom_instruction,
                existing_words=self.existing_words,
                batch_size=self.batch_size,
                progress_callback=lambda msg: self.progress.emit(msg),
                should_abort=self.cancel_event.is_set,
                grammar=self.grammar,
                slow_mode=self.slow_mode,
                report_callback=lambda report: setattr(self, "last_report", report),
            )

            if self.cancel_event.is_set():
                return

            if not vocab_list:
                label = t("batch_item_pattern") if self.grammar else t("item_label_vocab_lower")
                self.error.emit(t("batch_worker_empty", label=label))
                return

            label = t("batch_item_pattern") if self.grammar else t("item_label_vocab_lower")
            self.progress.emit(t("batch_worker_done", count=len(vocab_list), label=label))
            self.finished.emit(vocab_list)

        except Exception as e:
            logger.warning("Batch process error: %s", e)
            if not self.cancel_event.is_set():
                self.error.emit(str(e))

    def stop(self):
        self.cancel_event.set()


class DeckOrganizerThread(QThread):
    """
    Thread dùng AI để đề xuất và tạo cấu trúc Parent/Sub deck.
    """

    progress = pyqtSignal(str)            # Status text
    finished = pyqtSignal(dict)           # organization dict
    decks_created = pyqtSignal(dict)      # created decks mapping
    error = pyqtSignal(str)

    def __init__(self, vocab_list, lang, auto_create=False):
        super().__init__()
        self.vocab_list = vocab_list
        self.lang = lang
        self.auto_create = auto_create
        self.cancel_event = threading.Event()

    def run(self):
        try:
            if self.cancel_event.is_set():
                return

            # Step 1: AI đề xuất tổ chức
            self.progress.emit(t("worker_progress_organize"))

            organization = organize_decks_with_ai(
                vocab_list=self.vocab_list,
                lang=self.lang,
                progress_callback=lambda msg: self.progress.emit(msg),
                should_abort=self.cancel_event.is_set,
            )

            if self.cancel_event.is_set():
                return

            if not organization or not organization.get("decks"):
                self.error.emit(t("worker_error_no_deck"))
                return

            # Báo cáo cấu trúc
            total_parents = len(organization.get("decks", []))
            total_subs = sum(len(p.get("sub_decks", [])) for p in organization.get("decks", []))
            suggestion = organization.get("suggestion", "")
            
            summary = t("worker_summary_deck", parents=total_parents, subs=total_subs)
            if suggestion:
                summary += f"\n💡 {suggestion}"
            self.progress.emit(summary)

            self.finished.emit(organization)

        except Exception as e:
            logger.warning("Deck organizer error: %s", e)
            if not self.cancel_event.is_set():
                self.error.emit(str(e))

    def stop(self):
        self.cancel_event.set()
