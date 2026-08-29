"""Background pipeline for structured-source AI Deck Blueprint."""

import threading

from aqt.qt import QThread, pyqtSignal

from utils.batch_processor import organize_decks_with_ai, process_large_word_list
from utils.deck_blueprint import (
    attach_source_context,
    flatten_section_content,
    parse_structured_source,
)
from utils.i18n import t
from utils.logger import get_logger


logger = get_logger()


class DeckBlueprintWorker(QThread):
    """Parse headings, enrich vocabulary, then propose an editable deck tree."""

    progress = pyqtSignal(str)
    outline_ready = pyqtSignal(list)
    blueprint_ready = pyqtSignal(dict, list, list)
    error = pyqtSignal(str)

    def __init__(
        self,
        source_text,
        source_html,
        lang,
        custom_instruction="",
        existing_words=None,
        batch_size=80,
    ):
        super().__init__()
        self.source_text = str(source_text or "")
        self.source_html = str(source_html or "")
        self.lang = lang
        self.custom_instruction = str(custom_instruction or "")
        self.existing_words = list(existing_words or ())
        self.batch_size = int(batch_size or 80)
        self.cancel_event = threading.Event()

    def run(self):
        try:
            self.progress.emit(t("blueprint_status_reading_source"))
            sections = parse_structured_source(
                self.source_text,
                self.source_html,
                unsectioned_title=t("blueprint_unsectioned"),
            )
            if self.cancel_event.is_set():
                return
            raw_vocab = flatten_section_content(sections)
            if not raw_vocab.strip():
                self.error.emit(t("blueprint_error_empty_source"))
                return
            self.outline_ready.emit(sections)

            self.progress.emit(t("blueprint_status_enriching"))
            vocab_list = process_large_word_list(
                raw_text=raw_vocab,
                lang=self.lang,
                custom_instruction=self.custom_instruction,
                existing_words=self.existing_words,
                batch_size=self.batch_size,
                progress_callback=self.progress.emit,
                should_abort=self.cancel_event.is_set,
            )
            if self.cancel_event.is_set():
                return
            if not vocab_list:
                self.error.emit(t("blueprint_error_no_vocab"))
                return

            vocab_list = attach_source_context(vocab_list, sections)
            self.progress.emit(t("blueprint_status_organizing"))
            organization = organize_decks_with_ai(
                vocab_list=vocab_list,
                lang=self.lang,
                progress_callback=self.progress.emit,
                should_abort=self.cancel_event.is_set,
                source_sections=sections,
                custom_instruction=self.custom_instruction,
            )
            if self.cancel_event.is_set():
                return
            self.blueprint_ready.emit(organization, vocab_list, sections)
        except Exception as exc:
            logger.warning("Deck Blueprint worker failed: %s", exc)
            if not self.cancel_event.is_set():
                self.error.emit(str(exc))

    def stop(self):
        self.cancel_event.set()
