"""
AI Workers — Background threads for AI extract, AI chat, and audio preview.
"""

import os
import re
import threading
import unicodedata

from aqt.qt import QThread, pyqtSignal

from utils.logger import get_logger
from utils.i18n import t
from utils.ai_extractor import (
    extract_vocabulary_with_ai,
    extract_grammar_with_ai,
    chat_with_ai,
)
from utils.ai_candidate_extractor import extract_source_candidates_with_ai
from utils.knowledge_extractor import extract_knowledge_with_ai

logger = get_logger()

SMALL_RUN_MIN_CARDS = 5
SMALL_RUN_DEFAULT_CARDS = 10
SMALL_RUN_MAX_CARDS = 20
SMALL_RUN_MAX_SOURCE_CHARS = 4_000


def normalize_extraction_source(text):
    """Make pasted lists compact without discarding their learning meaning."""
    normalized_lines = []
    seen = set()
    for raw_line in unicodedata.normalize("NFKC", str(text or "")).splitlines():
        line = re.sub(r"^\s*(?:[-*•▪◦]+|\d{1,3}\s*[.)、:-])\s*", "", raw_line)
        line = " ".join(line.split())
        if not line:
            continue
        key = line.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized_lines.append(line)
    return "\n".join(normalized_lines)


def clamp_small_run_card_count(value):
    """Keep every caller, including legacy ones, inside the focused card range."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = SMALL_RUN_DEFAULT_CARDS
    return max(SMALL_RUN_MIN_CARDS, min(SMALL_RUN_MAX_CARDS, value))


def build_relevant_history_context(source, history_entries, instruction="", max_items=12):
    """Return only history that can clarify this source, within a small token budget."""
    source_folded = f"{source}\n{instruction}".casefold()
    if not source_folded.strip() or not history_entries:
        return ""

    scored = []
    for entry in history_entries:
        if not isinstance(entry, dict):
            continue
        front = str(entry.get("front", "")).strip()
        meaning = str(entry.get("meaning", "")).strip()
        topic = str(entry.get("topic", "")).strip()
        if not front:
            continue
        score = 0
        if len(front) > 1 and front.casefold() in source_folded:
            score += 100
        if len(topic) > 1 and topic.casefold() in source_folded:
            score += 40
        if meaning and len(meaning) > 2 and meaning.casefold() in source_folded:
            score += 20
        if score:
            scored.append((score, front.casefold(), front, meaning, topic))

    if not scored:
        return ""
    scored.sort(key=lambda item: (-item[0], item[1]))
    selected = []
    seen = set()
    for _, key, front, meaning, topic in scored:
        if key in seen:
            continue
        seen.add(key)
        topic_text = f" [{topic}]" if topic else ""
        selected.append(f"- {front} = {meaning}{topic_text}".rstrip())
        if len(selected) >= max_items:
            break
    return "\n".join((
        "ĐỐI CHIẾU LỊCH SỬ LIÊN QUAN (ngắn gọn, có thể đã cũ):",
        *selected,
        "Nguồn và yêu cầu hiện tại luôn ưu tiên; chỉ dùng lịch sử để tránh lặp "
        "và giữ nghĩa/chủ đề nhất quán.",
    ))


def _small_run_instruction(custom_instruction, max_cards=SMALL_RUN_DEFAULT_CARDS,
                           history_context=""):
    """Keep one request focused enough to review and learn immediately."""
    max_cards = clamp_small_run_card_count(max_cards)
    limit = (
        f"Chỉ tạo tối đa {max_cards} thẻ có giá trị học cao nhất. "
        "Nếu nguồn là danh sách dán lộn xộn, hãy tách đúng từng mục, bỏ bản sao "
        "và suy ra chủ đề từ ngữ cảnh gần nhất trước khi tạo thẻ. "
        "Không tạo danh mục chủ đề, không mô tả quy trình và không trả thêm mục ngoài thẻ."
    )
    custom = str(custom_instruction or "").strip()
    return "\n".join(part for part in (custom, history_context, limit) if part)


class AzureVoiceRefreshThread(QThread):
    """Fetch the Azure Neural catalogue away from the Qt UI thread."""

    loaded = pyqtSignal(str, list)
    error = pyqtSignal(str, str)

    def __init__(self, lang):
        super().__init__()
        self.lang = lang
        self._is_running = True

    def run(self):
        try:
            from audio.tts import fetch_azure_voice_options
            voices = fetch_azure_voice_options(self.lang)
            if self._is_running:
                self.loaded.emit(self.lang, voices)
        except Exception as exc:
            logger.warning("Could not refresh Azure Neural voices: %s", exc)
            if self._is_running:
                self.error.emit(self.lang, str(exc))

    def stop(self):
        self._is_running = False


class PreviewThread(QThread):
    """Thread preview giọng đọc theo nguồn TTS đang chọn."""

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
            from audio.engine import get_audio_multilang, speed_to_edge_rate
            rate = speed_to_edge_rate(self.speed)
            tag = get_audio_multilang(
                self.text, self.lang, voice=self.voice_id,
                rate=rate, cancel_event=self.cancel_event,
            )
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
                 cancel_event=None, learning_mode="language", card_kind=None,
                 max_cards=SMALL_RUN_DEFAULT_CARDS, history_entries=None):
        super().__init__()
        self.text = text
        self.lang = lang
        self.custom_instruction = custom_instruction
        self.existing_words = existing_words or []
        self.grammar = grammar
        self.card_kind = card_kind or ("grammar" if grammar else "vocab")
        self.learning_mode = learning_mode
        self.max_cards = clamp_small_run_card_count(max_cards)
        self.history_entries = list(history_entries or [])
        self.cancel_event = cancel_event or threading.Event()

    def run(self):
        try:
            if self.cancel_event.is_set():
                return
            source = normalize_extraction_source(self.text)
            if len(source) > SMALL_RUN_MAX_SOURCE_CHARS:
                self.error.emit(t(
                    "small_run_source_too_large",
                    length=len(source),
                    limit=SMALL_RUN_MAX_SOURCE_CHARS,
                ))
                return
            if self.existing_words:
                label = (
                    t("item_label_knowledge") if self.learning_mode == "knowledge" else
                    (t("item_label_collocation_lower") if self.card_kind == "collocation" else
                     t("item_label_grammar_lower") if self.grammar else t("item_label_vocab_lower"))
                )
                self.progress.emit(t("status_deck_avoid", count=len(self.existing_words), label=label))

            history_context = build_relevant_history_context(
                source, self.history_entries, self.custom_instruction,
            ) if self.learning_mode == "language" else ""
            generation_instruction = _small_run_instruction(
                self.custom_instruction, self.max_cards, history_context,
            )

            if self.learning_mode == "knowledge":
                self.progress.emit(t("worker_progress_knowledge"))
                result_list = extract_knowledge_with_ai(
                    source,
                    generation_instruction,
                    existing_keys=self.existing_words,
                    progress_callback=lambda msg: self.progress.emit(msg),
                    should_abort=self.cancel_event.is_set,
                )
                empty_msg = t("empty_knowledge")
            elif self.grammar:
                self.progress.emit(t("worker_progress_grammar"))
                result_list = extract_grammar_with_ai(
                    source,
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
                result_list = extract_vocabulary_with_ai(
                    source,
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
            if not result_list:
                self.error.emit(empty_msg)
                return

            self.finished.emit(result_list[:self.max_cards])

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
