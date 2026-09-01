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
from utils.ai_candidate_extractor import extract_source_candidates_with_ai
from utils.ai_inventory_scanner import (
    apply_prepared_inventory,
    inventory_source_from_text,
    scan_inventory_with_ai,
    topic_catalog_instruction,
)
from utils.knowledge_extractor import extract_knowledge_long_text

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

    def __init__(self, text, lang, custom_instruction="", existing_words=None, grammar=False,
                 cancel_event=None, learning_mode="language", card_kind=None):
        super().__init__()
        self.text = text
        self.lang = lang
        self.custom_instruction = custom_instruction
        self.existing_words = existing_words or []
        self.grammar = grammar
        self.card_kind = card_kind or ("grammar" if grammar else "vocab")
        self.learning_mode = learning_mode
        self.cancel_event = cancel_event or threading.Event()

    def run(self):
        try:
            if self.cancel_event.is_set():
                return
            if self.existing_words:
                label = (
                    t("item_label_knowledge") if self.learning_mode == "knowledge" else
                    (t("item_label_collocation_lower") if self.card_kind == "collocation" else
                     t("item_label_grammar_lower") if self.grammar else t("item_label_vocab_lower"))
                )
                self.progress.emit(t("status_deck_avoid", count=len(self.existing_words), label=label))

            preflight = None
            generation_instruction = self.custom_instruction
            if self.learning_mode != "knowledge":
                self.progress.emit(t("worker_progress_topic_inventory"))
                preflight = scan_inventory_with_ai(
                    inventory_source_from_text(self.text, name="Forge AI source"),
                    self.lang,
                    card_kind=self.card_kind,
                    progress_callback=lambda msg: self.progress.emit(msg),
                    should_abort=self.cancel_event.is_set,
                    turbo=True,
                )
                if self.cancel_event.is_set():
                    return
                topic_instruction = topic_catalog_instruction(preflight.get("topic_catalog", ()))
                generation_instruction = "\n".join(
                    part for part in (self.custom_instruction.strip(), topic_instruction) if part
                )
                approved = sum(
                    1 for item in preflight.get("inventory", ())
                    if item.get("decision") == "keep" and item.get("topic")
                )
                self.progress.emit(t(
                    "worker_progress_topic_inventory_done",
                    topics=len(preflight.get("topic_catalog", ())),
                    count=approved,
                ))
                if not approved:
                    self.error.emit(t("empty_preproduction_inventory"))
                    return

            if self.learning_mode == "knowledge":
                self.progress.emit(t("worker_progress_knowledge"))
                result_list = extract_knowledge_long_text(
                    self.text,
                    generation_instruction,
                    existing_keys=self.existing_words,
                    progress_callback=lambda msg: self.progress.emit(msg),
                    should_abort=self.cancel_event.is_set,
                )
                empty_msg = t("empty_knowledge")
            elif self.grammar:
                self.progress.emit(t("worker_progress_grammar"))
                result_list = extract_grammar_long_text(
                    self.text,
                    self.lang,
                    generation_instruction,
                    existing_patterns=self.existing_words,
                    progress_callback=lambda msg: self.progress.emit(msg),
                    should_abort=self.cancel_event.is_set,
                )
                empty_msg = t("empty_grammar")
            else:
                self.progress.emit(t(
                    "worker_progress_collocation" if self.card_kind == "collocation"
                    else "worker_progress_vocab"
                ))
                result_list = extract_vocabulary_long_text(
                    self.text,
                    self.lang,
                    generation_instruction,
                    existing_words=self.existing_words,
                    progress_callback=lambda msg: self.progress.emit(msg),
                    should_abort=self.cancel_event.is_set,
                    kind=self.card_kind,
                )
                empty_msg = t(
                    "empty_collocation" if self.card_kind == "collocation" else "empty_vocab"
                )

            if self.cancel_event.is_set():
                return
            if preflight is not None:
                result_list = apply_prepared_inventory(
                    result_list,
                    preflight.get("inventory", ()),
                    preflight.get("topic_catalog", ()),
                    card_kind=self.card_kind,
                )
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

    def __init__(
        self, message, lang, conversation_history=None, anki_context=None,
        card_kind="vocab", card_mode=None, candidate_mode=False, study_session=None,
        use_card_context=False, session_id="", runtime_config=None, cancel_event=None,
        workspace="reviewer", workspace_request=None, study_library_context=None,
    ):
        super().__init__()
        self.message = message
        self.lang = lang
        self.conversation_history = conversation_history
        self.anki_context = anki_context
        self.card_kind = card_kind
        self.card_mode = card_mode
        self.candidate_mode = bool(candidate_mode)
        self.study_session = study_session
        self.use_card_context = bool(use_card_context)
        self.session_id = session_id
        self.runtime_config = runtime_config
        self.workspace = workspace
        self.workspace_request = workspace_request
        self.study_library_context = study_library_context
        self.cancel_event = cancel_event or threading.Event()

    def run(self):
        try:
            self.progress.emit(t("worker_progress_context"))
            if self.candidate_mode:
                result = extract_source_candidates_with_ai(
                    self.message,
                    lang=self.lang,
                    workspace_request=self.workspace_request,
                    progress_callback=lambda msg: self.progress.emit(msg),
                    should_abort=self.cancel_event.is_set,
                    session_id=self.session_id,
                    runtime_config=self.runtime_config,
                )
            else:
                result = chat_with_ai(
                    user_message=self.message,
                    lang=self.lang,
                    conversation_history=self.conversation_history,
                    progress_callback=lambda msg: self.progress.emit(msg),
                    should_abort=self.cancel_event.is_set,
                    anki_context=self.anki_context,
                    card_kind=self.card_kind,
                    card_mode=self.card_mode,
                    study_session=self.study_session,
                    use_card_context=self.use_card_context,
                    session_id=self.session_id,
                    runtime_config=self.runtime_config,
                    workspace=self.workspace,
                    workspace_request=self.workspace_request,
                    study_library_context=self.study_library_context,
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
