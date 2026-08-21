"""Qt/Anki orchestration owner for the Bento Forge factory dialog.

This module is intentionally the only owner of the large ``AnkiSmartFactory``
view/controller and its direct Qt/``mw`` wiring.  Domain use cases remain in
``utils`` modules; the package root re-exports the public API for compatibility.
"""

import json
import os
import sys
import re
import time
import threading

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import askUser, showInfo, qconnect, tooltip

# ═══════════════════════════════════════════════════════════
#  Đảm bảo thư mục addon có trong sys.path để import
#  subpackages (Language/, mode/, audio/, utils/) hoạt động
# ═══════════════════════════════════════════════════════════
_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

# Lưu trạng thái ô AI theo learning mode rõ ràng:
# {language: {lang: {vocab|grammar: {...}}}}.
# Dữ liệu này phải ở profile Anki để update add-on không thể ghi đè dữ liệu người dùng.
from utils.user_data import get_user_data_path
from utils.factory_state import FactoryStateStore
from utils.learning_mode import (
    DEFAULT_LEARNING_MODE,
    get_learning_mode,
    is_learning_mode_available,
    normalize_learning_mode,
    set_learning_mode,
)

_LEGACY_STATE_PATH = os.path.join(_addon_root, "utils", "factory_state.json")
_STATE_PATH = get_user_data_path("factory_state.json")
_FACTORY_STATE_MAX_AGE_SECONDS = 7 * 24 * 3600
_FACTORY_STATE_MAX_TEXT_CHARS = 12_000
_FACTORY_STATE_MAX_JSON_CHARS = 24_000
_FACTORY_STATE_MAX_ITEMS = 100
_FACTORY_STATE_MAX_FLOW_BYTES = 192 * 1024


def _factory_state_store():
    """Build the state use case from current paths (supports isolated tests)."""
    return FactoryStateStore(
        legacy_path=_LEGACY_STATE_PATH,
        path=_STATE_PATH,
        max_age_seconds=_FACTORY_STATE_MAX_AGE_SECONDS,
        max_text_chars=_FACTORY_STATE_MAX_TEXT_CHARS,
        max_json_chars=_FACTORY_STATE_MAX_JSON_CHARS,
        max_items=_FACTORY_STATE_MAX_ITEMS,
        max_flow_bytes=_FACTORY_STATE_MAX_FLOW_BYTES,
    )

# ═══════════════════════════════════════════════════════════
#  IMPORTS FROM MODULES (Bridge)
# ═══════════════════════════════════════════════════════════
from Language import LANG_CONFIG, LANG_GRAMMAR_CONFIG, LANG_SELECTOR_INFO
from mode import LANG_TEMPLATES, LANG_CSS, LANG_GRAMMAR_TEMPLATES, LANG_GRAMMAR_CSS
from mode.card_render import build_qfmt as _build_qfmt, build_afmt as _build_afmt
from audio.engine import get_voice_options, get_selected_voice, set_selected_voice, VOICE_SAMPLE
from audio.engine import get_default_speed, set_default_speed
from utils import safe_parse_json
from utils.logger import get_logger
from utils.ai_extractor import (
    get_api_config,
    get_ai_session_estimate,
    get_existing_vocab_from_deck, invalidate_deck_cache,
    extract_vocabulary_with_ai, extract_vocabulary_long_text,
    get_effective_json_template, query_anki_context,
)
from utils.knowledge_schema import KnowledgeSchemaError, parse_knowledge_cards
from utils.knowledge_workflow import (
    KNOWLEDGE_IMPORT_CONFIG,
    prepare_knowledge_batch,
    read_knowledge_duplicate_keys,
    read_knowledge_notes_for_deck,
)
from utils.prompt_config import get_knowledge_json_template
from utils.import_history import (
    add_to_import_history, get_history_summary_text, init_import_history,
    load_import_history, needs_import_history_scan,
)
from utils.import_safety import rollback_added_notes, summarize_import_batch
from utils.anki_ops import run_collection, run_query
from utils.import_operations import apply_import, prepare_audio_tasks
from utils.import_operations import apply_knowledge_import, rollback_knowledge_import
from utils.anki_adapter import AnkiCollectionAdapter
from utils.import_quality import find_near_duplicate, normalize_for_comparison
from utils.ai_output_validation import validate_ai_cards
from utils.language_identity import normalize_language
from utils.import_report import write_import_report
from utils.model_lifecycle import ensure_model
from utils.ai_workflow import AiWorkflowCoordinator
from utils.srs_policy import (
    apply_srs_layout_to_config,
    migrate_deck_to_independent,
    needs_legacy_srs_migration,
    prepare_legacy_srs_model,
)

logger = get_logger()

# i18n — dịch UI (vi/en) + listener để refresh mượt mà khi đổi ngôn ngữ
from utils.i18n import (
    t, set_language, get_language, toggle_language,
    add_language_listener, remove_language_listener, SUPPORTED_LANGUAGES,
    study_mode_labels,
)

# Import workers (đã tách ra workers/)
from workers import ImportWorker, PreviewThread, AiExtractThread, AiChatThread

# Import UI dialogs (đã tách ra ui/)
from ui import AiChatDialog, show_ai_settings_dialog, show_diff_meaning_dialog, show_ai_preview_dialog
from ui.deck_manager_dialog import DeckManagerDialog
from ui.usage_history_dialog import AiUsageHistoryDialog
from ui.accessibility import configure_keyboard_navigation
from utils.deck_manager import refresh_anki

# Import glassmorphism theme engine
from ui.theme import (
    load_config as load_theme_config,
    apply_theme, ThemeDialog, snap_maximize, RatioSplitter,
)

# Import hooks (đã tách ra hooks/)
from hooks.reviewer import register_hooks
from hooks.overview_mode import (
    register_overview_hooks,
    get_study_mode,
    set_study_mode,
    get_srs_layout,
    set_srs_layout,
    MODES as STUDY_MODES,
    SRS_LAYOUTS,
    CONF_LANG_KEY,
)

_LANG_LABEL_KEYS = {
    "japanese": "lang_japanese",
    "chinese": "lang_chinese",
    "korean": "lang_korean",
    "english": "lang_english",
}


def _translated_language_label(lang, grammar=False):
    key = _LANG_LABEL_KEYS[normalize_language(lang)]
    if grammar:
        key += "_grammar"
    return t(key)

# ═══════════════════════════════════════════════════════════
#  MAIN DIALOG
# ═══════════════════════════════════════════════════════════
class AnkiSmartFactory(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_imported_note_ids = []
        self.setWindowTitle(t("app_title"))
        # Cho phép kéo thả cửa sổ tự do (thích ứng mọi kích thước, chia đôi màn hình)
        self.setMinimumSize(640, 420)
        self.resize(1300, 900)
        # Cho phép maximize / full màn hình
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        # Cấu hình giao diện glassmorphism (đọc từ utils/ui_theme.json)
        self._theme_cfg = load_theme_config()
        # Cho phép vẽ nền gradient glassmorphism
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.raw_data = []
        self.prepared_data = []
        self._current_lang = "japanese"
        self._is_grammar = False   # False = từ vựng, True = ngữ pháp
        self.import_worker = None
        self._import_cancel_event = None
        self._ai_workflow = AiWorkflowCoordinator()
        self._history_scan_cancel_event = None
        self._history_scan_progress = {}
        self._history_scan_progress_lock = threading.Lock()
        # Danh sách file tài liệu tham khảo đã kẹp: [(name, text), ...] + đường dẫn
        self._ai_attached_files = []
        self._ai_attached_paths = []
        # V18: Language là default tương thích; UI selector Knowledge ở V18-04.
        self._learning_mode = "language"
        # Trạng thái lưu theo learning mode, ngôn ngữ và subtype.
        self._factory_state = self._load_factory_state()
        # Debounce timer cho JSON parsing (tránh parse liên tục khi gõ)
        self._analyze_timer = QTimer(self)
        self._analyze_timer.setSingleShot(True)
        self._analyze_timer.setInterval(500)  # 500ms debounce
        self._analyze_timer.timeout.connect(self._analyze_content)
        self._ui_ready = False
        self._setup_ui()
        self._ui_ready = True
        stored_learning_mode = self._deck_learning_mode()
        # A dormant beta must not reopen merely because an older deck saved
        # its selection.  Do not persist this fallback: the old selection and
        # its isolated draft remain available if the beta is re-enabled.
        self._learning_mode = (
            stored_learning_mode
            if is_learning_mode_available(stored_learning_mode)
            else DEFAULT_LEARNING_MODE
        )
        self._apply_learning_mode_ui()
        if self._learning_mode == "language":
            self._on_lang_changed()
        else:
            self._restore_current_flow()
            self._retranslate_ui()

        # Đăng ký refresh UI khi ngôn ngữ giao diện thay đổi (từ nút toggle VI/EN)
        add_language_listener(self._retranslate_ui)

        # Khởi tạo lịch sử import (quét deck lần đầu nếu cần)
        self._init_history()

    def _init_history(self):
        """Load cached history, then bootstrap it via QueryOp only when needed."""
        try:
            history = load_import_history()
            self._set_history_status(history)
            if not needs_import_history_scan(history):
                return

            self._history_scan_cancel_event = threading.Event()
            self._history_scan_timer = QTimer(self)
            self._history_scan_timer.setInterval(125)
            self._history_scan_timer.timeout.connect(self._refresh_history_scan_progress)
            self._history_scan_timer.start()
            self.btn_history_cancel.setVisible(True)
            self._refresh_history_scan_progress()

            # QueryOp serializes all collection/SQL access with Anki.  The
            # progress callback only writes a lock-protected snapshot; Qt is
            # updated by the timer on the main thread.
            run_query(
                self,
                lambda col: init_import_history(
                    scan_context_factory=lambda: (col, LANG_CONFIG),
                    cancel_event=self._history_scan_cancel_event,
                    progress_callback=self._on_history_scan_progress,
                ),
                self._on_history_scan_finished,
                self._on_history_scan_error,
            )
        except Exception as e:
            logger.warning("Lỗi init history: %s", e)

    def _set_history_status(self, history):
        total = sum(len(v) for v in history.get("entries", {}).values())
        self.lbl_history_status.setText(t("status_history_count", count=total))
        self.lbl_history_status.setStyleSheet("color:#27ae60;font-size:11px;")

    def _on_history_scan_progress(self, progress):
        with self._history_scan_progress_lock:
            self._history_scan_progress = dict(progress)

    def _refresh_history_scan_progress(self):
        with self._history_scan_progress_lock:
            progress = dict(self._history_scan_progress)
        self.lbl_history_status.setText(t(
            "status_history_scanning",
            processed=progress.get("processed", 0),
            total=progress.get("total", 0),
        ))
        self.lbl_history_status.setStyleSheet("color:#e67e22;font-size:11px;")

    def _finish_history_scan(self):
        timer = getattr(self, "_history_scan_timer", None)
        if timer is not None:
            timer.stop()
        self.btn_history_cancel.setVisible(False)
        self._history_scan_cancel_event = None

    def _on_history_scan_finished(self, history):
        self._finish_history_scan()
        if history.get("_scan_cancelled"):
            self.lbl_history_status.setText(t("status_history_scan_cancelled"))
            self.lbl_history_status.setStyleSheet("color:#e67e22;font-size:11px;")
            return
        self._set_history_status(history)

    def _on_history_scan_error(self, err):
        logger.warning("Lỗi quét import history: %s", err)
        self._finish_history_scan()
        self.lbl_history_status.setText(t("status_history_scan_error"))
        self.lbl_history_status.setStyleSheet("color:#e74c3c;font-size:11px;")

    def _cancel_history_scan(self):
        if self._history_scan_cancel_event is not None:
            self._history_scan_cancel_event.set()
            timer = getattr(self, "_history_scan_timer", None)
            if timer is not None:
                timer.stop()
            self.btn_history_cancel.setEnabled(False)
            self.lbl_history_status.setText(t("status_history_scan_cancelling"))

    def _cfg(self):
        # Mức 1 (Field Map Editor): bơm json_field_map + all_fields HIỆU LỰC
        # (defaults từ Language/*.py + ghi đè của người dùng trong ai_prompts.json)
        # vào config → mọi nơi dùng self._cfg() đều tự có field mới.
        if getattr(self, "_learning_mode", DEFAULT_LEARNING_MODE) == "knowledge":
            return dict(KNOWLEDGE_IMPORT_CONFIG)
        from utils.prompt_config import apply_field_map_to_cfg
        is_grammar = bool(getattr(self, '_is_grammar', False))
        base = (LANG_GRAMMAR_CONFIG if is_grammar else LANG_CONFIG)[self._current_lang]
        kind = "grammar" if is_grammar else "vocab"
        cfg = apply_field_map_to_cfg(base, self._current_lang, kind)
        if not is_grammar:
            cfg = apply_srs_layout_to_config(cfg, get_srs_layout(self._current_deck_id()))
        return cfg

    def _current_deck_id(self):
        """Resolve the selected deck without assuming UI setup has completed."""
        try:
            chooser = getattr(self, "deck_chooser", None)
            name = chooser.currentText() if chooser is not None else ""
            return mw.col.decks.id(name) if name else None
        except Exception:
            return None

    def _select_mode(self, is_grammar):
        """Chuyển chế độ Từ vựng ↔ Ngữ pháp (Note Type riêng)"""
        if self._learning_mode != "language":
            return
        # Luôn đồng bộ trạng thái nút (tránh toggle lệch khi bấm lại nút đang active)
        self.btn_mode_vocab.setChecked(not is_grammar)
        self.btn_mode_grammar.setChecked(is_grammar)
        if getattr(self, '_is_grammar', False) == is_grammar:
            return
        # Lưu trạng thái luồng hiện tại TRƯỚC khi đổi mode
        self._save_current_flow()
        self._is_grammar = is_grammar
        self._on_lang_changed()
        tooltip(t("tooltip_switched_grammar") if is_grammar else t("tooltip_switched_vocab"))

    # ═══════════════════════════════════════════════════════
    #  LƯU / KHÔI PHỤC TRẠNG THÁI Ô AI (text + file) theo luồng
    #  {lang: {vocab|grammar: {"text": ..., "files": [paths]}}}
    # ═══════════════════════════════════════════════════════
    def _load_factory_state(self):
        """Delegate persisted draft state to its profile-data use case."""
        return _factory_state_store().load()

    def _save_factory_state(self):
        """Persist bounded draft state without letting the UI own file I/O."""
        self._factory_state = _factory_state_store().save(self._factory_state)

    def _flow_key(self):
        """Return the explicit V18 draft key for Language or Knowledge."""
        if getattr(self, "_learning_mode", DEFAULT_LEARNING_MODE) == "knowledge":
            return "knowledge", "default", "knowledge"
        subtype = "grammar" if self._is_grammar else "vocab"
        return "language", self._current_lang, subtype

    def _flow_state_path(self):
        """Normalize the V18 key and tolerate test/extensions using the V17 key."""
        key = self._flow_key()
        if len(key) == 2:
            lang, subtype = key
            return "language", lang, subtype
        return key

    def _save_current_flow(self):
        """Lưu text + file paths + thẻ trong xưởng (raw_data/prepared_data/JSON) của luồng
        đang hiển thị (gọi TRƯỚC khi đổi ngôn ngữ/mode/đóng)."""
        try:
            learning_mode, lang, mode = self._flow_state_path()
            flow = self._factory_state.setdefault(learning_mode, {}).setdefault(lang, {}).setdefault(mode, {})
            flow["text"] = self.ai_text_input.toPlainText()
            flow["files"] = list(getattr(self, '_ai_attached_paths', []))
            # Lưu thẻ chờ xuất xưởng để KHÔNG bị mất khi đóng Factory
            flow["raw"] = [d for d in getattr(self, 'raw_data', []) if isinstance(d, dict)]
            flow["cards"] = [d for d in getattr(self, 'prepared_data', []) if isinstance(d, dict)]
            try:
                flow["json"] = self.json_input.toPlainText()
            except Exception:
                pass
            self._save_factory_state()
        except Exception as e:
            logger.warning("Lỗi lưu flow state: %s", e)

    def _restore_current_flow(self):
        """Khôi phục text + file kẹp + thẻ trong xưởng cho luồng đang hiển thị (gọi SAU khi setup UI)."""
        try:
            learning_mode, lang, mode = self._flow_state_path()
            flow = self._factory_state.get(learning_mode, {}).get(lang, {}).get(mode, {})
            self.ai_text_input.setPlainText(flow.get("text", ""))
            # Khôi phục danh sách file kẹp (đọc lại nếu file còn tồn tại)
            self._ai_attached_files = []
            self._ai_attached_paths = []
            for p in flow.get("files", []):
                if not os.path.exists(p):
                    continue
                try:
                    from utils.ai_extractor import extract_text_from_file
                    text = extract_text_from_file(p)
                    self._ai_attached_files.append((os.path.basename(p), text))
                    self._ai_attached_paths.append(p)
                except Exception:
                    pass
            self._update_ai_files_label()
            # Khôi phục thẻ chờ xuất xưởng (chỉ khi UI đã dựng xong)
            self.raw_data = [d for d in flow.get("raw", []) if isinstance(d, dict)]
            self.prepared_data = [d for d in flow.get("cards", []) if isinstance(d, dict)]
            if hasattr(self, 'lbl_raw'):
                self.lbl_raw.setText(t("filter_raw_count", count=len(self.raw_data)))
            if hasattr(self, 'json_input'):
                try:
                    self.json_input.blockSignals(True)
                    self.json_input.setPlainText(flow.get("json", ""))
                    self.json_input.blockSignals(False)
                except Exception:
                    pass
            if hasattr(self, 'txt_search'):
                self._rebuild_preview()
                self.btn_import.setEnabled(len(self.prepared_data) > 0)
                self.btn_cancel_order.setEnabled(len(self.prepared_data) > 0)
                if self.prepared_data:
                    self.lbl_ready.setText(t("preview_ready", count=len(self.prepared_data)))
        except Exception as e:
            logger.warning("Lỗi khôi phục flow state: %s", e)

    def closeEvent(self, event):
        """Lưu trạng thái ô AI khi đóng Factory."""
        self._cancel_history_scan()
        try:
            self._save_current_flow()
        except Exception:
            pass
        try:
            super().closeEvent(event)
        except Exception:
            event.accept()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 10)
        root.setSpacing(8)

        # ── TOP TOOLBAR: giao diện + ngôn ngữ + chia cửa sổ ─────────
        top = QHBoxLayout()
        top.setSpacing(6)
        self.lbl_brand = QLabel(t("brand_label"))
        self.lbl_brand.setStyleSheet("font-size:14px;font-weight:bold;")
        top.addWidget(self.lbl_brand)

        self.btn_theme = QPushButton(t("btn_theme"))
        self.btn_theme.setProperty("class", "primary")
        self.btn_theme.setToolTip(t("btn_theme_tip"))
        self.btn_theme.clicked.connect(self._open_theme_dialog)
        top.addWidget(self.btn_theme)

        self.btn_lang_toggle = QPushButton(t("btn_lang_toggle"))
        self.btn_lang_toggle.setProperty("class", "ghost")
        self.btn_lang_toggle.setToolTip(t("btn_lang_toggle_tip"))
        self.btn_lang_toggle.clicked.connect(self._toggle_ui_language)
        top.addWidget(self.btn_lang_toggle)

        self.btn_snap_max = QPushButton(t("btn_snap_max"))
        self.btn_snap_max.setProperty("class", "ghost")
        self.btn_snap_max.setToolTip(t("btn_snap_max_tip"))
        self.btn_snap_max.clicked.connect(lambda: snap_maximize(self))
        top.addWidget(self.btn_snap_max)

        top.addStretch()
        self.lbl_tip = QLabel(t("lbl_tip"))
        self.lbl_tip.setProperty("class", "dim")
        top.addWidget(self.lbl_tip)
        root.addLayout(top)

        # ── MAIN SPLITTER (chia đôi, kéo thả 3:7, thích ứng) ──
        self.main_splitter = RatioSplitter()

        # ── LEFT ─────────────────────────────────────────
        left_panel = QWidget()
        left = QVBoxLayout(left_panel)
        left.setContentsMargins(0, 0, 4, 0)
        left.setSpacing(6)

        # Learning Mode selector (product-level; vocab/grammar stay Language subtypes).
        self.learning_mode_grp = QGroupBox(t("learning_mode_grp_title"))
        learning_mode_layout = QHBoxLayout()
        self.btn_learning_language = QPushButton(t("btn_learning_language"))
        self.btn_learning_language.setCheckable(True)
        self.btn_learning_language.setChecked(True)
        self.btn_learning_language.clicked.connect(lambda checked: self._select_learning_mode("language"))
        learning_mode_layout.addWidget(self.btn_learning_language)
        self.btn_learning_knowledge = QPushButton(t("btn_learning_knowledge"))
        self.btn_learning_knowledge.setCheckable(True)
        self.btn_learning_knowledge.clicked.connect(lambda checked: self._select_learning_mode("knowledge"))
        learning_mode_layout.addWidget(self.btn_learning_knowledge)
        self.learning_mode_grp.setLayout(learning_mode_layout)
        left.addWidget(self.learning_mode_grp)

        # Language selector
        self.lang_grp = QGroupBox(t("lang_grp_title"))
        lang_layout = QHBoxLayout()

        self.btn_lang = {}
        for key, _label, code in LANG_SELECTOR_INFO:
            btn = QPushButton(t(_LANG_LABEL_KEYS[key]))
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self._select_lang(k))
            self.btn_lang[key] = btn
            lang_layout.addWidget(btn)

        self.lang_grp.setLayout(lang_layout)
        left.addWidget(self.lang_grp)

        # Mode selector: Từ vựng / Ngữ pháp
        self.mode_grp = QGroupBox(t("mode_grp_title"))
        mode_layout = QHBoxLayout()
        self.btn_mode_vocab = QPushButton(t("btn_mode_vocab"))
        self.btn_mode_vocab.setCheckable(True)
        self.btn_mode_vocab.setChecked(True)
        self.btn_mode_vocab.setStyleSheet(
            "padding:8px;font-weight:bold;border-radius:10px;"
            "QPushButton:checked{background:#2ecc71;color:white;border:2px solid #27ae60;}"
            "QPushButton:!checked{background:rgba(255,255,255,0.08);color:#eaf0f6;border:1px solid rgba(255,255,255,0.18);}"
        )
        self.btn_mode_vocab.clicked.connect(lambda checked: self._select_mode(False))
        mode_layout.addWidget(self.btn_mode_vocab)
        self.btn_mode_grammar = QPushButton(t("btn_mode_grammar"))
        self.btn_mode_grammar.setCheckable(True)
        self.btn_mode_grammar.setStyleSheet(
            "padding:8px;font-weight:bold;border-radius:10px;"
            "QPushButton:checked{background:#34495e;color:white;border:2px solid #2c3e50;}"
            "QPushButton:!checked{background:rgba(255,255,255,0.08);color:#eaf0f6;border:1px solid rgba(255,255,255,0.18);}"
        )
        self.btn_mode_grammar.clicked.connect(lambda checked: self._select_mode(True))
        mode_layout.addWidget(self.btn_mode_grammar)
        self.mode_grp.setLayout(mode_layout)
        left.addWidget(self.mode_grp)

        # Deck + file
        bar = QHBoxLayout()
        self.deck_chooser = QComboBox()
        self.deck_chooser.addItems(mw.col.decks.all_names())
        self.deck_chooser.currentTextChanged.connect(self._on_deck_changed)
        self.lbl_deck = QLabel(t("deck_label"))
        bar.addWidget(self.lbl_deck, 0)
        bar.addWidget(self.deck_chooser, 1)
        self.btn_refresh_deck = QPushButton("🔄")
        self.btn_refresh_deck.setToolTip(t("btn_refresh_deck_tip"))
        self.btn_refresh_deck.setMaximumWidth(36)
        self.btn_refresh_deck.clicked.connect(self._refresh_deck_chooser)
        bar.addWidget(self.btn_refresh_deck, 0)
        self.btn_manage_deck = QPushButton(t("deck_manage_btn"))
        self.btn_manage_deck.setProperty("class", "info")
        self.btn_manage_deck.setToolTip(t("btn_manage_deck_tip"))
        self.btn_manage_deck.clicked.connect(self._open_deck_manager)
        bar.addWidget(self.btn_manage_deck, 0)
        self.btn_load = QPushButton(t("open_file_btn"))
        self.btn_load.setProperty("class", "info")
        self.btn_load.clicked.connect(self._load_from_file)
        bar.addWidget(self.btn_load, 0)
        left.addLayout(bar)

        # Sample buttons
        bar2 = QHBoxLayout()
        self.btn_sample = QPushButton(t("sample_json_btn"))
        self.btn_sample.setProperty("class", "ghost")
        self.btn_sample.clicked.connect(self._show_sample_json)
        bar2.addWidget(self.btn_sample)
        self.btn_history = QPushButton(t("btn_history"))
        self.btn_history.setProperty("class", "ghost")
        self.btn_history.setToolTip(t("btn_history_tip"))
        self.btn_history.clicked.connect(self._open_history_browser)
        bar2.addWidget(self.btn_history)
        bar2.addStretch()
        left.addLayout(bar2)

        # ── AI Trích Xuất Từ Vựng ──────────────────────────
        self.ai_grp = QGroupBox(t("ai_group_title"))
        ai_main = QVBoxLayout()

        # Row 1: Buttons
        ai_bar = QHBoxLayout()

        self.btn_ai_settings = QPushButton(t("ai_settings_btn"))
        self.btn_ai_settings.setStyleSheet(
            "padding:5px 8px;background:#8e44ad;color:white;"
            "font-weight:bold;border-radius:6px;border:none;"
        )
        self.btn_ai_settings.clicked.connect(self._show_ai_settings)
        ai_bar.addWidget(self.btn_ai_settings)

        self.btn_ai_clear_text = QPushButton(t("ai_clear_text_btn"))
        self.btn_ai_clear_text.setStyleSheet(
            "padding:5px 8px;background:#95a5a6;color:white;"
            "font-weight:bold;border-radius:6px;border:none;"
        )
        self.btn_ai_clear_text.clicked.connect(self._ai_clear_text)
        ai_bar.addWidget(self.btn_ai_clear_text)

        self.btn_ai_extract = QPushButton(t("ai_extract_btn"))
        self.btn_ai_extract.setStyleSheet(
            "padding:5px 10px;background:#e67e22;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:13px;"
        )
        self.btn_ai_extract.clicked.connect(self._ai_extract)
        self.btn_ai_extract.setEnabled(True)
        ai_bar.addWidget(self.btn_ai_extract)

        self.btn_ai_batch = QPushButton(t("ai_batch_btn"))
        self.btn_ai_batch.setStyleSheet(
            "padding:5px 8px;background:#2ecc71;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:12px;"
        )
        self.btn_ai_batch.setToolTip(t("btn_ai_batch_tip"))
        self.btn_ai_batch.clicked.connect(self._ai_batch_process)
        self.btn_ai_batch.setEnabled(True)
        ai_bar.addWidget(self.btn_ai_batch)

        self.btn_ai_chat = QPushButton(t("ai_chat_btn"))
        self.btn_ai_chat.setStyleSheet(
            "padding:5px 10px;background:#2980b9;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:13px;"
        )
        self.btn_ai_chat.setToolTip(t("btn_ai_chat_tip"))
        self.btn_ai_chat.clicked.connect(self._ai_chat)
        self.btn_ai_chat.setEnabled(True)
        ai_bar.addWidget(self.btn_ai_chat)

        self.btn_ai_stop = QPushButton(t("ai_stop_btn"))
        self.btn_ai_stop.setStyleSheet(
            "padding:5px 8px;background:#e74c3c;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:12px;"
        )
        self.btn_ai_stop.setToolTip(t("btn_ai_stop_tip"))
        self.btn_ai_stop.clicked.connect(self._cancel_ai_chat)
        self.btn_ai_stop.setVisible(False)
        ai_bar.addWidget(self.btn_ai_stop)

        self.btn_history_cancel = QPushButton(t("history_scan_cancel_btn"))
        self.btn_history_cancel.setStyleSheet(
            "padding:5px 8px;background:#e74c3c;color:white;"
            "font-weight:bold;border-radius:6px;border:none;font-size:12px;"
        )
        self.btn_history_cancel.setToolTip(t("history_scan_cancel_tip"))
        self.btn_history_cancel.clicked.connect(self._cancel_history_scan)
        self.btn_history_cancel.setVisible(False)
        ai_bar.addWidget(self.btn_history_cancel)

        self.lbl_history_status = QLabel("")
        self.lbl_history_status.setProperty("class", "dim")
        ai_bar.addWidget(self.lbl_history_status)

        self.lbl_ai_status = QLabel("")
        self.lbl_ai_status.setProperty("class", "dim")
        ai_bar.addWidget(self.lbl_ai_status, 1)

        ai_main.addLayout(ai_bar)

        # Row 1b: Đính kèm file tài liệu tham khảo cho AI
        file_bar = QHBoxLayout()
        self.btn_ai_attach = QPushButton(t("btn_ai_attach"))
        self.btn_ai_attach.setStyleSheet(
            "padding:5px 12px;background:#16a085;color:white;"
            "font-weight:bold;border-radius:6px;border:none;"
        )
        self.btn_ai_attach.setToolTip(t("btn_ai_attach_tip"))
        self.btn_ai_attach.clicked.connect(self._attach_ai_files)
        file_bar.addWidget(self.btn_ai_attach)

        self.btn_ai_attach_clear = QPushButton(t("btn_ai_attach_clear"))
        self.btn_ai_attach_clear.setStyleSheet(
            "padding:5px 12px;background:#95a5a6;color:white;"
            "font-weight:bold;border-radius:6px;border:none;"
        )
        self.btn_ai_attach_clear.setToolTip(t("btn_ai_attach_clear_tip"))
        self.btn_ai_attach_clear.clicked.connect(self._clear_ai_files)
        file_bar.addWidget(self.btn_ai_attach_clear)

        self.lbl_ai_files = QLabel("")
        self.lbl_ai_files.setStyleSheet("color:#27ae60;font-size:11px;")
        self.lbl_ai_files.setWordWrap(True)
        file_bar.addWidget(self.lbl_ai_files, 1)
        ai_main.addLayout(file_bar)

        # Row 2: Text input area for AI
        self.ai_text_input = QPlainTextEdit()
        self.ai_text_input.setPlaceholderText(t("ai_input_placeholder_vocab"))
        self.ai_text_input.setMaximumHeight(80)
        self.ai_text_input.setStyleSheet("font-size:12px;")
        ai_main.addWidget(self.ai_text_input)

        # Row 3: Custom instruction
        instr_bar = QHBoxLayout()
        self.lbl_instruction = QLabel(t("ai_instruction_label"))
        instr_bar.addWidget(self.lbl_instruction)
        self.ai_instruction = QLineEdit()
        self.ai_instruction.setPlaceholderText(t("ai_instruction_placeholder"))
        self.ai_instruction.setStyleSheet("font-size:12px;padding:4px;")
        instr_bar.addWidget(self.ai_instruction, 1)
        ai_main.addLayout(instr_bar)

        self.ai_grp.setLayout(ai_main)
        left.addWidget(self.ai_grp)

        self.lbl_json_label = QLabel(t("json_input_label"))
        left.addWidget(self.lbl_json_label)
        self.json_input = QPlainTextEdit()
        self.json_input.textChanged.connect(self._schedule_analyze)
        left.addWidget(self.json_input)

        # Filters
        self.filter_grp = QGroupBox(t("filter_group_title"))
        gl = QGridLayout()

        self.lbl_raw = QLabel(t("filter_raw_count", count=0))
        self.lbl_raw.setStyleSheet("color:#e67e22;font-weight:bold;")
        gl.addWidget(self.lbl_raw, 0, 0, 1, 2)

        self.lbl_level = QLabel(t("filter_level_label"))
        self.cbo_level = QComboBox()
        gl.addWidget(self.lbl_level, 1, 0)
        gl.addWidget(self.cbo_level, 1, 1)

        self.txt_topic = QLineEdit()
        self.txt_topic.setPlaceholderText(t("filter_topic_placeholder"))
        self.lbl_topic = QLabel(t("filter_topic_label"))
        gl.addWidget(self.lbl_topic, 2, 0)
        gl.addWidget(self.txt_topic, 2, 1)

        audio_box = QHBoxLayout()
        self.chk_audio_vocab = QCheckBox(t("filter_audio_vocab"))
        self.chk_audio_vocab.setChecked(True)
        self.chk_audio_ex1 = QCheckBox(t("filter_audio_ex1"))
        self.chk_audio_ex1.setChecked(True)
        self.chk_audio_ex2 = QCheckBox(t("filter_audio_ex2"))
        self.chk_audio_ex2.setChecked(True)
        for c in (self.chk_audio_vocab, self.chk_audio_ex1, self.chk_audio_ex2):
            audio_box.addWidget(c)
        self.lbl_audio = QLabel(t("filter_audio_label"))
        gl.addWidget(self.lbl_audio, 3, 0)
        gl.addLayout(audio_box, 3, 1)

        self.btn_verify = QPushButton(t("btn_verify"))
        self.btn_verify.setProperty("class", "warning")
        self.btn_verify.setMinimumHeight(42)
        self.btn_verify.setToolTip(t("btn_verify_tip"))
        self.btn_verify.clicked.connect(self._verify_batch)

        self.btn_rebuild = QPushButton(t("btn_rebuild"))
        self.btn_rebuild.setProperty("class", "purple")
        self.btn_rebuild.setMinimumHeight(42)
        self.btn_rebuild.setToolTip(t("btn_rebuild_tip"))
        self.btn_rebuild.clicked.connect(self._force_rebuild_model)

        self.btn_diff_meaning = QPushButton(t("btn_diff_meaning"))
        self.btn_diff_meaning.setProperty("class", "warning")
        self.btn_diff_meaning.setMinimumHeight(42)
        self.btn_diff_meaning.setEnabled(False)
        self.btn_diff_meaning.setToolTip(t("btn_diff_meaning_tip"))
        self.btn_diff_meaning.clicked.connect(self._show_diff_meaning_report)

        # Hàng ngang 3 nút
        action_bar = QHBoxLayout()
        action_bar.addWidget(self.btn_verify, 1)
        action_bar.addWidget(self.btn_rebuild, 1)
        action_bar.addWidget(self.btn_diff_meaning, 1)
        gl.addLayout(action_bar, 4, 0, 1, 2)

        # ── Voice Selection ───────────────────────────────
        self.voice_grp = QGroupBox(t("voice_group_title"))
        vgl = QVBoxLayout()
        voice_row = QHBoxLayout()
        self.lbl_voice = QLabel(t("voice_label"))
        voice_row.addWidget(self.lbl_voice, 0)
        self.cbo_voice = QComboBox()
        self.cbo_voice.setMinimumWidth(150)
        self.cbo_voice.currentIndexChanged.connect(self._on_voice_changed)
        voice_row.addWidget(self.cbo_voice, 1)
        self.btn_preview_voice = QPushButton(t("voice_preview_btn"))
        self.btn_preview_voice.setProperty("class", "purple")
        self.btn_preview_voice.clicked.connect(self._preview_voice)
        voice_row.addWidget(self.btn_preview_voice, 0)
        voice_row.addSpacing(12)
        self.lbl_speed = QLabel(t("voice_speed_label"))
        voice_row.addWidget(self.lbl_speed, 0)
        self.spin_speed = QDoubleSpinBox()
        self.spin_speed.setRange(0.25, 4.0)
        self.spin_speed.setSingleStep(0.05)
        self.spin_speed.setDecimals(2)
        self.spin_speed.setSuffix(" ×")
        self.spin_speed.setValue(1.0)
        self.spin_speed.setMinimumWidth(70)
        self.spin_speed.setToolTip(t("spin_speed_tip"))
        self.spin_speed.valueChanged.connect(self._on_speed_changed)
        voice_row.addWidget(self.spin_speed, 0)
        vgl.addLayout(voice_row)
        # ── Chế độ học mặc định (đồng bộ với Study now của Onigiri) ──
        study_row = QHBoxLayout()
        self.lbl_study_mode = QLabel(t("study_mode_label"))
        study_row.addWidget(self.lbl_study_mode, 0)
        self.cbo_study_mode = QComboBox()
        self.cbo_study_mode.setMinimumWidth(130)
        self.cbo_study_mode.currentIndexChanged.connect(self._on_study_mode_changed)
        study_row.addWidget(self.cbo_study_mode, 1)
        study_row.addSpacing(12)
        self.lbl_srs_layout = QLabel(t("srs_layout_label"))
        study_row.addWidget(self.lbl_srs_layout, 0)
        self.cbo_srs_layout = QComboBox()
        self.cbo_srs_layout.setMinimumWidth(155)
        self.cbo_srs_layout.currentIndexChanged.connect(self._on_srs_layout_changed)
        study_row.addWidget(self.cbo_srs_layout, 1)
        self.btn_migrate_srs = QPushButton(t("srs_migrate_btn"))
        self.btn_migrate_srs.setProperty("class", "info")
        self.btn_migrate_srs.clicked.connect(self._migrate_current_deck_srs)
        study_row.addWidget(self.btn_migrate_srs, 0)
        vgl.addLayout(study_row)
        self.voice_grp.setLayout(vgl)
        left.addWidget(self.voice_grp)

        self.main_splitter.addWidget(left_panel)

        # ── RIGHT ────────────────────────────────────────
        right_panel = QWidget()
        right = QVBoxLayout(right_panel)
        right.setContentsMargins(4, 0, 0, 0)
        right.setSpacing(6)

        # Bộ Lọc & Gác Cổng V5+ (chuyển sang cột phải)
        self.filter_grp.setLayout(gl)
        right.addWidget(self.filter_grp)

        self.lbl_preview_title = QLabel(t("preview_label"))
        right.addWidget(self.lbl_preview_title)

        # ── Tìm kiếm + lọc nhanh theo loại thẻ ──
        sf = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(t("search_placeholder"))
        self.txt_search.textChanged.connect(self._rebuild_preview)
        sf.addWidget(self.txt_search, 1)
        self.cbo_filter = QComboBox()
        self._repopulate_filter_combo()
        self.cbo_filter.setToolTip(t("cbo_filter_tip"))
        self.cbo_filter.currentIndexChanged.connect(self._rebuild_preview)
        sf.addWidget(self.cbo_filter, 0)
        right.addLayout(sf)

        self.preview_list = QListWidget()
        self.preview_list.setMinimumHeight(120)  # thích ứng theo kích thước kéo thả
        self.preview_list.itemChanged.connect(self._update_selection_label)
        right.addWidget(self.preview_list)

        # ── Nút chọn nhanh + số thẻ đã chọn ──
        sel = QHBoxLayout()
        self.btn_select_all = QPushButton(t("btn_select_all"))
        self.btn_select_all.setToolTip(t("btn_select_all_tip"))
        self.btn_select_all.clicked.connect(self._select_all_visible)
        sel.addWidget(self.btn_select_all)
        self.btn_select_none = QPushButton(t("btn_select_none"))
        self.btn_select_none.setToolTip(t("btn_select_none_tip"))
        self.btn_select_none.clicked.connect(self._select_none_visible)
        sel.addWidget(self.btn_select_none)
        sel.addStretch()
        self.lbl_sel = QLabel(t("lbl_sel_count", selected=0, total=0))
        self.lbl_sel.setStyleSheet("color:#2980b9;font-weight:bold;")
        sel.addWidget(self.lbl_sel)
        right.addLayout(sel)

        rng = QHBoxLayout()
        self.spin_start = QSpinBox()
        self.spin_start.setRange(1, 9999)
        self.spin_start.setToolTip(t("rng_tip"))
        self.spin_start.valueChanged.connect(self._on_range_changed)
        self.spin_end = QSpinBox()
        self.spin_end.setRange(1, 9999)
        self.spin_end.setToolTip(t("rng_tip"))
        self.spin_end.valueChanged.connect(self._on_range_changed)
        self.lbl_rng_from = QLabel(t("rng_from_label"))
        self.lbl_rng_to = QLabel(t("rng_to_label"))
        self.lbl_rng_hint = QLabel(t("rng_hint"))
        rng.addWidget(self.lbl_rng_from)
        rng.addWidget(self.spin_start)
        rng.addWidget(self.lbl_rng_to)
        rng.addWidget(self.spin_end)
        rng.addWidget(self.lbl_rng_hint)
        rng.addStretch()
        right.addLayout(rng)

        self.lbl_ready = QLabel(t("preview_ready", count=0))
        self.lbl_ready.setStyleSheet("color:#27ae60;font-weight:bold;")
        right.addWidget(self.lbl_ready)

        self.pbar = QProgressBar()
        self.pbar.setVisible(False)
        right.addWidget(self.pbar)

        self.lbl_status = QLabel("")
        self.lbl_status.setProperty("class", "dim")
        right.addWidget(self.lbl_status)

        self.btn_import = QPushButton(t("btn_import"))
        self.btn_import.setProperty("class", "success")
        self.btn_import.setMinimumHeight(52)
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self._process_import)
        right.addWidget(self.btn_import)

        self.btn_rollback_import = QPushButton(t("btn_rollback_import"))
        self.btn_rollback_import.setProperty("class", "warning")
        self.btn_rollback_import.setMinimumHeight(40)
        self.btn_rollback_import.setEnabled(False)
        self.btn_rollback_import.clicked.connect(self._rollback_last_import)
        right.addWidget(self.btn_rollback_import)

        op_row = QHBoxLayout()
        self.btn_cancel = QPushButton(t("btn_cancel"))
        self.btn_cancel.setProperty("class", "danger")
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel_import)
        op_row.addWidget(self.btn_cancel)
        self.btn_cancel_order = QPushButton(t("btn_cancel_order"))
        self.btn_cancel_order.setProperty("class", "danger")
        self.btn_cancel_order.setMinimumHeight(40)
        self.btn_cancel_order.setEnabled(False)
        self.btn_cancel_order.setToolTip(t("btn_cancel_order_tip"))
        self.btn_cancel_order.clicked.connect(self._cancel_order)
        op_row.addWidget(self.btn_cancel_order)
        right.addLayout(op_row)

        self.main_splitter.addWidget(right_panel)
        self.main_splitter.setStretchFactor(0, 5)
        self.main_splitter.setStretchFactor(1, 5)
        self.main_splitter.setSizes([660, 640])
        # Thanh phân cách kéo mượt, mỗi cột giới hạn 30%–70% (3:7)
        self.main_splitter.setHandleWidth(8)
        root.addWidget(self.main_splitter, 1)

        # ── 💰 Thanh chi phí AI (góc dưới) — theo dõi ngân sách ──
        cost_bar = QHBoxLayout()
        # Giữ nguyên giao diện dạng text nhưng dùng nút thật để click luôn ổn định.
        self.lbl_cost = QPushButton("")
        self.lbl_cost.setProperty("class", "dim")
        self.lbl_cost.setFlat(True)
        self.lbl_cost.setStyleSheet(
            "QPushButton { color:#95a5a6;font-size:11px;padding:2px 4px;"
            "border:none;background:transparent;text-align:left; }"
            "QPushButton:hover { color:#3498db;text-decoration:underline; }"
        )
        self.lbl_cost.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_cost.setToolTip(t("usage_history_open_tip"))
        self.lbl_cost.clicked.connect(self._show_usage_history)
        cost_bar.addWidget(self.lbl_cost, 1)
        self.btn_reset_cost = QPushButton(t("btn_reset_cost"))
        self.btn_reset_cost.setStyleSheet(
            "padding:3px 10px;font-size:11px;background:#34495e;color:#fff;"
            "border:none;border-radius:8px;cursor:pointer;"
        )
        self.btn_reset_cost.clicked.connect(self._reset_cost)
        cost_bar.addWidget(self.btn_reset_cost)
        root.addLayout(cost_bar)

        # QTimer poll chi phí AI (cập nhật tự động mỗi 2s)
        self.cost_timer = QTimer(self)
        self.cost_timer.setInterval(2000)
        self.cost_timer.timeout.connect(self._update_cost_label)
        self.cost_timer.start()
        self._update_cost_label()

        # Áp theme glassmorphism
        self._theme_cfg = apply_theme(self, self._theme_cfg)

        # Đồng bộ toàn bộ chuỗi hiển thị theo ngôn ngữ UI hiện tại
        self._retranslate_ui()
        self._configure_accessibility()

    def _configure_accessibility(self):
        """Keep the main workflow fully reachable by keyboard and screen readers."""
        controls = [
            (self.btn_theme, t("btn_theme")),
            (self.btn_lang_toggle, t("btn_lang_toggle")),
            (self.deck_chooser, t("deck_label")),
            (self.cbo_study_mode, t("study_mode_label")),
            (self.cbo_srs_layout, t("srs_layout_label")),
            (self.btn_migrate_srs, t("srs_migrate_btn")),
            (self.btn_load, t("open_file_btn")),
            (self.ai_text_input, t("ai_input_accessible_name")),
            (self.ai_instruction, t("ai_instruction_label")),
            (self.btn_ai_extract, t("ai_extract_btn")),
            (self.btn_ai_chat, t("ai_chat_btn")),
            (self.json_input, t("json_input_label")),
            (self.cbo_level, t("filter_level_label")),
            (self.txt_topic, t("filter_topic_label")),
            (self.btn_verify, t("btn_verify")),
            (self.txt_search, t("search_accessible_name")),
            (self.cbo_filter, t("cbo_filter_tip")),
            (self.preview_list, t("preview_label")),
            (self.spin_start, t("rng_from_label")),
            (self.spin_end, t("rng_to_label")),
            (self.btn_import, t("btn_import")),
            (self.btn_cancel, t("btn_cancel")),
        ]
        configure_keyboard_navigation(
            self, controls, description=t("accessibility_control_description"),
            focus_policy=Qt.FocusPolicy.StrongFocus,
        )

    def _update_cost_label(self):
        """Cập nhật chi phí AI tích lũy ở góc dưới (poll từ ai_extractor)."""
        try:
            from utils.ai_extractor import get_total_cost
            st = get_total_cost()
            self.lbl_cost.setText(
                t("cost_label", cost=f"${float(st.get('total_usd', 0.0)):.6f}", calls=int(st.get('calls', 0)))
            )
        except Exception:
            pass

    def _show_usage_history(self, _link=""):
        """Open the persistent per-request AI usage details."""
        dialog = AiUsageHistoryDialog(self)
        dialog.exec()

    def _reset_cost(self):
        """Đặt lại bộ đếm chi phí AI."""
        try:
            from utils.ai_extractor import reset_cost
            reset_cost()
            self._update_cost_label()
        except Exception:
            pass

    def _toggle_ui_language(self):
        """Chuyển ngôn ngữ giao diện giữa Tiếng Việt ⇄ English (mượt mà, không đóng cửa sổ)."""
        try:
            toggle_language()
            # _retranslate_ui được gọi tự động qua listener trong set_language
        except Exception as e:
            logger.warning("Lỗi chuyển ngôn ngữ: %s", e)

    def _update_window_title(self):
        """Update the title without representing Knowledge as a language flow."""
        try:
            if self._learning_mode == "knowledge":
                self.setWindowTitle(t("app_title_knowledge"))
            else:
                language = _translated_language_label(
                    self._current_lang, grammar=self._is_grammar
                )
                self.setWindowTitle(t("app_title_language", language=language))
        except Exception as e:
            logger.warning("Lỗi cập nhật tiêu đề: %s", e)

    def _sync_level_combo(self):
        """Translate the display-only 'All' option while keeping stable filter data."""
        cfg = self._cfg()
        current = self.cbo_level.currentData() if self.cbo_level.count() else ""
        self.cbo_level.blockSignals(True)
        self.cbo_level.clear()
        self.cbo_level.addItem(t("filter_all_levels"), "")
        for choice in cfg["level_choices"][1:]:
            self.cbo_level.addItem(choice, choice)
        index = self.cbo_level.findData(current)
        self.cbo_level.setCurrentIndex(index if index >= 0 else 0)
        self.cbo_level.blockSignals(False)

    def _repopulate_filter_combo(self):
        """Điền lại các mục lọc thẻ theo ngôn ngữ UI hiện tại (giữ nguyên lựa chọn)."""
        try:
            current = self.cbo_filter.currentText() if hasattr(self, 'cbo_filter') else ""
            items = [
                t("cbo_filter_all"), t("cbo_filter_new"), t("cbo_filter_update"),
                t("cbo_filter_conflict"), t("cbo_filter_diff"),
            ]
            self.cbo_filter.blockSignals(True)
            self.cbo_filter.clear()
            self.cbo_filter.addItems(items)
            if current in items:
                self.cbo_filter.setCurrentText(current)
            self.cbo_filter.blockSignals(False)
        except Exception as e:
            logger.warning("Lỗi repopulate filter combo: %s", e)

    def _retranslate_ui(self):
        """Cập nhật toàn bộ chuỗi hiển thị theo ngôn ngữ UI hiện tại (live refresh)."""
        try:
            # Toolbar
            self.lbl_brand.setText(t("brand_label"))
            self.btn_theme.setText(t("btn_theme"))
            self.btn_theme.setToolTip(t("btn_theme_tip"))
            self.btn_lang_toggle.setText(t("btn_lang_toggle"))
            self.btn_lang_toggle.setToolTip(t("btn_lang_toggle_tip"))
            self.btn_snap_max.setText(t("btn_snap_max"))
            self.btn_snap_max.setToolTip(t("btn_snap_max_tip"))
            self.lbl_tip.setText(t("lbl_tip"))
            self.btn_reset_cost.setText(t("btn_reset_cost"))

            # Selectors
            self.learning_mode_grp.setTitle(t("learning_mode_grp_title"))
            self.btn_learning_language.setText(t("btn_learning_language"))
            self.btn_learning_knowledge.setText(t("btn_learning_knowledge"))
            if self._learning_mode == "language":
                self.lang_grp.setTitle(_translated_language_label(
                    self._current_lang, grammar=self._is_grammar
                ))
            for lang, button in self.btn_lang.items():
                button.setText(t(_LANG_LABEL_KEYS[lang]))
            self.mode_grp.setTitle(t("mode_grp_title"))
            self.btn_mode_vocab.setText(t("btn_mode_vocab"))
            self.btn_mode_grammar.setText(t("btn_mode_grammar"))
            self.lbl_deck.setText(t("deck_label"))
            self.btn_refresh_deck.setToolTip(t("btn_refresh_deck_tip"))
            self.btn_manage_deck.setText(t("deck_manage_btn"))
            self.btn_manage_deck.setToolTip(t("btn_manage_deck_tip"))
            self.btn_load.setText(t("open_file_btn"))
            self.btn_sample.setText(t("sample_json_btn"))
            self.btn_history.setText(t("btn_history"))
            self.btn_history.setToolTip(t("btn_history_tip"))

            # AI group
            self.ai_grp.setTitle(t(
                "ai_group_title_knowledge" if self._learning_mode == "knowledge" else "ai_group_title"
            ))
            self.btn_ai_settings.setText(t("ai_settings_btn"))
            self.btn_ai_clear_text.setText(t("ai_clear_text_btn"))
            if self._learning_mode == "knowledge":
                self.btn_ai_extract.setText(t("knowledge_generate_btn"))
                self.btn_ai_extract.setToolTip(t("knowledge_generate_tip"))
            else:
                self.btn_ai_extract.setText(t("ai_extract_btn"))
                self.btn_ai_extract.setToolTip("")
            self.btn_ai_batch.setText(t("ai_batch_btn"))
            self.btn_ai_batch.setToolTip(t("btn_ai_batch_tip"))
            self.btn_ai_chat.setText(t("ai_chat_btn"))
            self.btn_ai_chat.setToolTip(t("btn_ai_chat_tip"))
            self.btn_ai_stop.setText(t("ai_stop_btn"))
            self.btn_ai_stop.setToolTip(t("btn_ai_stop_tip"))
            self.btn_history_cancel.setText(t("history_scan_cancel_btn"))
            self.btn_history_cancel.setToolTip(t("history_scan_cancel_tip"))
            self.btn_ai_attach.setText(t("btn_ai_attach"))
            self.btn_ai_attach.setToolTip(t("btn_ai_attach_tip"))
            self.btn_ai_attach_clear.setText(t("btn_ai_attach_clear"))
            self.btn_ai_attach_clear.setToolTip(t("btn_ai_attach_clear_tip"))
            self.ai_text_input.setPlaceholderText(t(self._ai_input_placeholder_key()))
            self.lbl_instruction.setText(t(
                "knowledge_instruction_label" if self._learning_mode == "knowledge" else "ai_instruction_label"
            ))
            self.ai_instruction.setPlaceholderText(t(
                "knowledge_instruction_placeholder" if self._learning_mode == "knowledge" else "ai_instruction_placeholder"
            ))
            self.lbl_json_label.setText(t(
                "knowledge_json_input_label" if self._learning_mode == "knowledge" else "json_input_label"
            ))
            if self._ai_attached_files:
                self._update_ai_files_label()

            # Filters
            self.filter_grp.setTitle(t("filter_group_title"))
            self.lbl_topic.setText(t("filter_topic_label"))
            self.txt_topic.setPlaceholderText(t("filter_topic_placeholder"))
            self.lbl_audio.setText(t("filter_audio_label"))
            self.chk_audio_vocab.setText(t("filter_audio_vocab"))
            self.chk_audio_ex1.setText(t("filter_audio_ex1"))
            self.chk_audio_ex2.setText(t("filter_audio_ex2"))
            self.btn_verify.setText(t("btn_verify"))
            self.btn_verify.setToolTip(t("btn_verify_tip"))
            self.btn_rebuild.setText(t("btn_rebuild"))
            self.btn_rebuild.setToolTip(t("btn_rebuild_tip"))
            self.btn_diff_meaning.setText(t("btn_diff_meaning"))
            self.btn_diff_meaning.setToolTip(t("btn_diff_meaning_tip"))
            if self._learning_mode == "language":
                self._sync_level_combo()

            # Voice
            self.voice_grp.setTitle(t("voice_group_title"))
            self.lbl_voice.setText(t("voice_label"))
            self.lbl_speed.setText(t("voice_speed_label"))
            self.lbl_study_mode.setText(t("study_mode_label"))
            self.lbl_srs_layout.setText(t("srs_layout_label"))
            self.btn_migrate_srs.setText(t("srs_migrate_btn"))
            self.cbo_srs_layout.setToolTip(t("srs_layout_tip"))
            self.btn_migrate_srs.setToolTip(t("srs_migrate_tip"))
            self.btn_preview_voice.setText(t("voice_preview_btn"))
            self.spin_speed.setToolTip(t("spin_speed_tip"))
            self.chk_audio_vocab.setToolTip(t("voice_tooltip"))
            self.chk_audio_ex1.setToolTip(t("voice_tooltip"))
            self.chk_audio_ex2.setToolTip(t("voice_tooltip"))
            if self._learning_mode == "language":
                self._sync_srs_layout_combo()

            # Preview area
            self.lbl_preview_title.setText(t(
                "knowledge_preview_label" if self._learning_mode == "knowledge" else "preview_label"
            ))
            self.txt_search.setPlaceholderText(t("search_placeholder"))
            self._repopulate_filter_combo()
            self.cbo_filter.setToolTip(t("cbo_filter_tip"))
            self.btn_select_all.setText(t("btn_select_all"))
            self.btn_select_all.setToolTip(t("btn_select_all_tip"))
            self.btn_select_none.setText(t("btn_select_none"))
            self.btn_select_none.setToolTip(t("btn_select_none_tip"))
            self.lbl_rng_from.setText(t("rng_from_label"))
            self.lbl_rng_to.setText(t("rng_to_label"))
            self.lbl_rng_hint.setText(t("rng_hint"))
            self.spin_start.setToolTip(t("rng_tip"))
            self.spin_end.setToolTip(t("rng_tip"))
            self.btn_import.setText(t("btn_import"))
            self.btn_rollback_import.setText(t("btn_rollback_import"))
            self.btn_cancel.setText(t("btn_cancel"))
            self.btn_cancel_order.setText(t("btn_cancel_order"))
            self.btn_cancel_order.setToolTip(t("btn_cancel_order_tip"))
            self._configure_accessibility()

            # Counts theo dữ liệu hiện tại
            self.lbl_raw.setText(t("filter_raw_count", count=len(self.raw_data)))
            self.lbl_ready.setText(t("preview_ready", count=len(self.prepared_data)))
            # Dựng lại danh sách thẻ để cập nhật các hậu tố (Nghĩa khác/Cập nhật/Trùng mờ)
            if hasattr(self, 'preview_list') and self.prepared_data:
                self._rebuild_preview()
            else:
                self._update_selection_label()
            self._update_window_title()
        except Exception as e:
            logger.warning("Lỗi retranslate UI: %s", e)

    def _open_theme_dialog(self):
        """Mở hộp thoại tùy chỉnh giao diện glassmorphism"""
        dlg = ThemeDialog(self)
        dlg.exec()

    def _open_deck_manager(self):
        """Mở dialog quản lý Parent/Sub Deck (tạo/sửa/xóa, đồng bộ tức thì)."""
        dlg = DeckManagerDialog(self)
        dlg.exec()
        # Sau khi đóng dialog, làm mới deck_chooser để phản ánh thay đổi
        self._refresh_deck_chooser()

    def _refresh_deck_chooser(self):
        """Làm mới danh sách deck trong deck_chooser từ Anki collection."""
        try:
            current = self.deck_chooser.currentText()
            names = mw.col.decks.all_names()
            self.deck_chooser.blockSignals(True)
            self.deck_chooser.clear()
            self.deck_chooser.addItems(names)
            if current in names:
                self.deck_chooser.setCurrentText(current)
            self.deck_chooser.blockSignals(False)
        except Exception as e:
            logger.warning("Lỗi làm mới deck_chooser: %s", e)

    def _apply_lang_button_styles(self):
        """Áp dụng style chuẩn quốc kỳ cho nút ngôn ngữ"""
        default_style = """
        QPushButton {
            padding: 8px 14px;
            font-weight: bold;
            font-size: 13px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.18);
            background: rgba(255,255,255,0.08);
            color: #eaf0f6;
        }
        QPushButton:hover {
            background: rgba(255,255,255,0.15);
        }
        """

        selected_styles = {
            "japanese": """
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ffffff, stop:1 #f5f5f5);
                    color: #bc002d;
                    border: 2px solid #bc002d;
                    font-size: 15px;
                }
            """,
            "chinese": """
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #fff5f5, stop:1 #fef0e0);
                    color: #de2910;
                    border: 2px solid #de2910;
                    font-size: 15px;
                }
            """,
            "korean": """
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ffffff, stop:1 #f5f5f5);
                    color: #c60c30;
                    border: 2px solid #c60c30;
                    font-size: 15px;
                }
            """,
            "english": """
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f5f9ff, stop:1 #fff3f5);
                    color: #1f5fa8;
                    border: 2px solid #1f5fa8;
                    font-size: 15px;
                }
            """,
        }

        for key, btn in self.btn_lang.items():
            style = default_style + selected_styles.get(key, "")
            btn.setStyleSheet(style)

    def _deck_learning_mode(self):
        """Read the selected deck's explicit V18 mode without changing config."""
        try:
            return get_learning_mode(mw.col.conf, self._current_deck_id())
        except Exception as error:
            logger.warning("Could not read learning mode for deck: %s", error)
            return DEFAULT_LEARNING_MODE

    def _persist_learning_mode(self, mode):
        """Persist a user-selected mode only for the currently selected deck."""
        deck_id = self._current_deck_id()
        if deck_id is None:
            return
        try:
            set_learning_mode(mw.col.conf, mode, deck_id)
            mw.col.setMod()
        except Exception as error:
            logger.warning("Could not save learning mode for deck %s: %s", deck_id, error)

    def _ai_input_placeholder_key(self):
        if getattr(self, "_learning_mode", "language") == "knowledge":
            return "ai_input_placeholder_knowledge"
        return "ai_input_placeholder_grammar" if self._is_grammar else "ai_input_placeholder_vocab"

    def _apply_learning_mode_ui(self):
        """Show only controls that apply to the selected product-level mode."""
        if not hasattr(self, "btn_learning_language"):
            return
        knowledge_available = is_learning_mode_available("knowledge")
        if not knowledge_available and self._learning_mode != DEFAULT_LEARNING_MODE:
            # Defensive boundary for callers/tests that bypass __init__.
            # This intentionally leaves the per-deck preference untouched.
            self._learning_mode = DEFAULT_LEARNING_MODE
        is_language = self._learning_mode == "language"
        self.btn_learning_language.setChecked(is_language)
        self.btn_learning_knowledge.setChecked(not is_language)
        self.btn_learning_knowledge.setVisible(knowledge_available)
        if hasattr(self, "learning_mode_grp"):
            # A one-option selector is noise in the focused Language UI.
            self.learning_mode_grp.setVisible(knowledge_available)
        # These controls encode language, level, audio or Language model policy.
        for widget in (self.lang_grp, self.mode_grp, self.voice_grp):
            widget.setVisible(is_language)
        for widget in (self.btn_ai_extract, self.btn_sample, self.btn_verify):
            widget.setVisible(True)
        # This opens the Language-only vocabulary/grammar batch dialog.
        # Knowledge already accepts multiple strict cards through AI extract.
        self.btn_ai_batch.setVisible(is_language)
        self.btn_ai_chat.setVisible(is_language)
        self.filter_grp.setVisible(True)
        for widget in (
            self.lbl_level, self.cbo_level, self.lbl_topic, self.txt_topic,
            self.lbl_audio, self.chk_audio_vocab, self.chk_audio_ex1, self.chk_audio_ex2,
            self.btn_rebuild, self.btn_diff_meaning,
        ):
            widget.setVisible(is_language)
        if hasattr(self, "json_input"):
            self.json_input.setEnabled(True)
        if hasattr(self, "btn_import"):
            self.btn_import.setEnabled(bool(self.prepared_data))
        if hasattr(self, "btn_cancel_order"):
            self.btn_cancel_order.setEnabled(bool(self.prepared_data))

    def _clear_mode_preview(self):
        """Clear only the displayed data before restoring the target mode draft."""
        self.raw_data = []
        self.prepared_data = []
        if hasattr(self, "preview_list"):
            self.preview_list.clear()
        if hasattr(self, "json_input"):
            self.json_input.clear()
        if hasattr(self, "btn_import"):
            self.btn_import.setEnabled(False)
        if hasattr(self, "btn_cancel_order"):
            self.btn_cancel_order.setEnabled(False)
        if hasattr(self, "btn_diff_meaning"):
            self.btn_diff_meaning.setEnabled(False)

    def _select_learning_mode(self, mode, *, persist=True, announce=True):
        """Switch modes without invoking Language extraction or model lifecycle."""
        mode = normalize_learning_mode(mode)
        if not is_learning_mode_available(mode):
            return
        if mode == self._learning_mode:
            self._apply_learning_mode_ui()
            return
        self._save_current_flow()
        self._learning_mode = mode
        if persist:
            self._persist_learning_mode(mode)
        if mode == "language":
            self._on_lang_changed()
        else:
            self._clear_mode_preview()
            self._apply_learning_mode_ui()
            self._restore_current_flow()
            self._apply_learning_mode_ui()
            self._retranslate_ui()
        if announce:
            tooltip(t("tooltip_switched_learning_knowledge" if mode == "knowledge" else "tooltip_switched_learning_language"))

    def _select_lang(self, lang_key):
        if self._learning_mode != "language":
            return
        if lang_key != self._current_lang:
            # Lưu trạng thái luồng hiện tại trước khi chuyển ngôn ngữ
            self._save_current_flow()
        self._current_lang = lang_key
        # Lưu ngôn ngữ đang chọn để selector Overview hiển thị đúng label mode
        try:
            mw.col.conf[CONF_LANG_KEY] = lang_key
        except Exception:
            pass
        self._on_lang_changed()

    def _on_lang_changed(self):
        if self._learning_mode != "language":
            return
        self._apply_learning_mode_ui()
        cfg = self._cfg()
        for k, btn in self.btn_lang.items():
            btn.setChecked(k == self._current_lang)

        self._apply_lang_button_styles()

        # Cập nhật tiêu đề group box ngôn ngữ + tiêu đề cửa sổ
        self.lang_grp.setTitle(_translated_language_label(
            self._current_lang, grammar=self._is_grammar
        ))
        self._update_window_title()

        self.lbl_level.setText(cfg["level_label"])
        self._sync_level_combo()

        tooltip_text = t("voice_tooltip")
        self.chk_audio_vocab.setToolTip(tooltip_text)
        self.chk_audio_ex1.setToolTip(tooltip_text)
        self.chk_audio_ex2.setToolTip(tooltip_text)

        self.raw_data = []
        self.prepared_data = []
        self.preview_list.clear()
        self.btn_import.setEnabled(False)
        self.json_input.clear()
        self.btn_diff_meaning.setEnabled(False)

        # Bỏ file tham khảo cũ khi đổi ngôn ngữ / chế độ
        self._ai_attached_files = []
        if hasattr(self, 'lbl_ai_files'):
            self.lbl_ai_files.setText("")

        # Cập nhật placeholder theo chế độ
        self.ai_text_input.setPlaceholderText(t(self._ai_input_placeholder_key()))

        # Sync voice dropdown với ngôn ngữ hiện tại
        lang = cfg["lang_code"]
        voices = get_voice_options(lang)
        self.cbo_voice.blockSignals(True)
        self.cbo_voice.clear()
        sel_id = get_selected_voice(lang)
        for i, v in enumerate(voices):
            icon = "👩" if v["gender"] == "female" else "👨"
            self.cbo_voice.addItem(f"{icon} {v['name']}")
            if v["id"] == sel_id:
                self.cbo_voice.setCurrentIndex(i)
        self.cbo_voice.blockSignals(False)

        # Sync speed spinner với ngôn ngữ hiện tại
        self.spin_speed.blockSignals(True)
        self.spin_speed.setValue(get_default_speed(lang))
        self.spin_speed.blockSignals(False)

        is_vocab = not self._is_grammar
        for widget in (self.lbl_study_mode, self.cbo_study_mode, self.lbl_srs_layout,
                       self.cbo_srs_layout, self.btn_migrate_srs):
            widget.setVisible(is_vocab)
        if is_vocab:
            self._sync_srs_layout_combo()
        self.get_or_create_model()

        # Đồng bộ dropdown chế độ học với cấu hình hiện tại
        if hasattr(self, 'cbo_study_mode'):
            self._sync_study_mode_combo()

        # Khôi phục text + file kẹp cho luồng (ngôn ngữ + mode) đang hiển thị
        self._restore_current_flow()

        # Đồng bộ toàn bộ chuỗi hiển thị theo ngôn ngữ UI hiện tại
        self._retranslate_ui()

    def _on_voice_changed(self, index):
        lang = self._cfg()["lang_code"]
        voices = get_voice_options(lang)
        if 0 <= index < len(voices):
            set_selected_voice(lang, voices[index]["id"])

    def _on_speed_changed(self, value):
        lang = self._cfg()["lang_code"]
        set_default_speed(lang, round(value, 2))

    def _sync_study_mode_combo(self):
        """Đồng bộ dropdown mode với cấu hình hiện tại."""
        try:
            lang = self._current_lang
            # Nhãn theo ngôn ngữ UI (vi: "1. Nhật→Việt" / en: "1. Japanese→English")
            lbl = study_mode_labels(lang)
            current = get_study_mode(self._current_deck_id())
            self.cbo_study_mode.blockSignals(True)
            self.cbo_study_mode.clear()
            for k in STUDY_MODES:
                self.cbo_study_mode.addItem(lbl.get(k, k), k)
            idx = self.cbo_study_mode.findData(current)
            self.cbo_study_mode.setCurrentIndex(idx if idx >= 0 else 0)
            self.cbo_study_mode.blockSignals(False)
        except Exception as e:
            logger.warning("Lỗi đồng bộ mode combo: %s", e)

    def _on_study_mode_changed(self, index):
        """Lưu chế độ học đã chọn vào config (đồng bộ với Study now Onigiri)."""
        try:
            data = self.cbo_study_mode.itemData(index)
            if data:
                set_study_mode(data, self._current_deck_id())
        except Exception as e:
            logger.warning("Lỗi lưu study mode: %s", e)

    def _sync_srs_layout_combo(self):
        """Show the selected deck's policy for notes created from now on."""
        if not hasattr(self, "cbo_srs_layout"):
            return
        try:
            current = get_srs_layout(self._current_deck_id())
            labels = {
                "combo": t("srs_layout_combo"),
                "independent": t("srs_layout_independent"),
            }
            self.cbo_srs_layout.blockSignals(True)
            self.cbo_srs_layout.clear()
            for layout in SRS_LAYOUTS:
                self.cbo_srs_layout.addItem(labels[layout], layout)
            index = self.cbo_srs_layout.findData(current)
            self.cbo_srs_layout.setCurrentIndex(index if index >= 0 else 0)
            self.cbo_srs_layout.blockSignals(False)
        except Exception as exc:
            logger.warning("Lỗi đồng bộ SRS layout: %s", exc)

    def _on_srs_layout_changed(self, index):
        """Change defaults for future imports; never mutate existing notes here."""
        try:
            layout = self.cbo_srs_layout.itemData(index)
            if layout:
                set_srs_layout(layout, self._current_deck_id())
                tooltip(t("srs_layout_changed"))
        except Exception as exc:
            logger.warning("Lỗi lưu SRS layout: %s", exc)

    def _on_deck_changed(self, _name=None):
        if not getattr(self, "_ui_ready", False):
            return
        deck_mode = self._deck_learning_mode()
        if deck_mode != self._learning_mode:
            self._select_learning_mode(deck_mode, persist=False, announce=False)
        if self._learning_mode == "language" and hasattr(self, "cbo_study_mode"):
            self._sync_study_mode_combo()
        if self._learning_mode == "language" and hasattr(self, "cbo_srs_layout"):
            self._sync_srs_layout_combo()

    def _migrate_current_deck_srs(self):
        """Opt existing Combo notes into five schedules under one undo checkpoint."""
        if self._is_grammar:
            return
        deck_id = self._current_deck_id()
        if deck_id is None:
            showInfo(t("srs_migrate_no_deck"))
            return
        if not askUser(t("srs_migrate_confirm"), parent=self):
            return
        try:
            mw.checkpoint(t("srs_migrate_checkpoint"))
            model = self.get_or_create_model()
            result = migrate_deck_to_independent(mw.col, model, deck_id)
            set_srs_layout("independent", deck_id)
            self._sync_srs_layout_combo()
            mw.reset()
            key = "srs_migrate_done" if result.changed_notes else "srs_migrate_none"
            showInfo(t(key, count=result.changed_notes))
        except Exception as exc:
            logger.warning("SRS deck migration failed: %s", exc)
            showInfo(t("srs_migrate_failed", error=str(exc)))

    def _preview_voice(self):
        lang = self._cfg()["lang_code"]
        voices = get_voice_options(lang)
        idx = self.cbo_voice.currentIndex()
        if not voices or idx < 0 or idx >= len(voices):
            return
        voice_id = voices[idx]["id"]
        sample = VOICE_SAMPLE.get(lang, "Hello!")

        previous_preview = getattr(self, "_preview_thread", None)
        if previous_preview is not None and previous_preview.isRunning():
            previous_preview.stop()

        self.btn_preview_voice.setEnabled(False)
        self.btn_preview_voice.setText("⏳")

        speed = self.spin_speed.value()
        self._preview_thread = PreviewThread(
            sample, voice_id, lang, speed=speed, media_dir=mw.col.media.dir()
        )
        self._preview_thread.done.connect(self._on_preview_done)
        self._preview_thread.start()

    def _on_preview_done(self, filepath):
        self.btn_preview_voice.setEnabled(True)
        self.btn_preview_voice.setText(t("voice_preview_btn"))
        if filepath and os.path.exists(filepath):
            try:
                from aqt.sound import av_player
                from anki.sound import SoundOrVideoTag
                av_player.play_tags([SoundOrVideoTag(filename=os.path.basename(filepath))])
            except Exception:
                try:
                    import subprocess
                    subprocess.Popen([filepath], shell=True)
                except Exception:
                    tooltip(t("tooltip_audio_preview_fail"))
        else:
            tooltip(t("tooltip_audio_gen_fail"))

    def _show_sample_json(self):
        if getattr(self, "_learning_mode", "language") == "knowledge":
            self.json_input.setPlainText(get_knowledge_json_template())
            self._schedule_analyze()
            return
        samples = {
            "japanese": '''{
  "front": "食べる",
  "furigana": "たべる",
  "meaning": "ăn",
  "sino-vietnamese": "",
  "jlptlevel": "N5",
  "topic": "Động từ",
  "example": "毎日ご飯を食べる。",
  "example_vn": "Hàng ngày tôi ăn cơm.",
  "example_2": "友達と一緒に食べました。",
  "example_2_vn": "Tôi đã ăn cùng bạn bè."
}''',
            "chinese": '''{
  "simplified": "学习",
  "traditional": "學習",
  "pinyin": "xuéxí",
  "meaning": "học tập",
  "sino_vietnamese": "học tập",
  "hsk_level": "HSK1",
  "topic": "Động từ",
  "example": "我每天学习中文。",
  "example_pinyin": "Wǒ měitiān xuéxí zhōngwén.",
  "example_vn": "Mỗi ngày tôi học tiếng Trung.",
  "example_2": "他在图书馆学习。",
  "example_2_pinyin": "Tā zài túshūguǎn xuéxí.",
  "example_2_vn": "Anh ấy học ở thư viện."
}''',
            "korean": '''{
  "front": "먹다",
  "romanization": "meokda",
  "meaning": "ăn",
  "sino_vietnamese": "",
  "topik_level": "TOPIK I",
  "topic": "Động từ",
  "example": "아침에 밥을 먹어요.",
  "example_romanization": "achime babeul meogeoyo.",
  "example_vn": "Buổi sáng tôi ăn cơm.",
  "example_2": "친구와 함께 저녁을 먹었어요.",
  "example_2_romanization": "chin-guwa hamkke jeonyeogeul meogeosseoyo.",
  "example_2_vn": "Tôi đã ăn tối cùng bạn bè."
}'''
        }

        # Mẫu JSON ngữ pháp khi đang ở chế độ Ngữ pháp
        grammar_samples = {
            "japanese": '''{
  "pattern": "〜てもいい",
  "reading": "てもいい",
  "meaning": "được phép làm gì đó",
  "jlptlevel": "N5",
  "topic": "Cho phép / Xin phép",
  "usage": "Vて + もいいです",
  "explanation": "Dùng để xin phép hoặc cho phép. Thân mật: 〜てもいいよ",
  "example": "ここで写真を撮ってもいいですか。",
  "example_vn": "Tôi chụp ảnh ở đây được không?",
  "example_2": "明日は休んでもいいよ。",
  "example_2_vn": "Mai nghỉ cũng được nhé."
}''',
            "chinese": '''{
  "pattern": "把 + N + V",
  "pinyin": "bǎ + N + V",
  "meaning": "đem/ làm gì đó với ... (nhấn mạnh kết quả)",
  "hsk_level": "HSK3",
  "topic": "Cấu trúc câu",
  "usage": "Chủ ngữ + 把 + 宾语 + V + Kết quả",
  "explanation": "Dùng khi nhấn mạnh kết quả của việc tác động lên vật.",
  "example": "我把作业做完了。",
  "example_pinyin": "Wǒ bǎ zuòyè zuò wán le.",
  "example_vn": "Tôi đã làm xong bài tập.",
  "example_2": "请把门关上。",
  "example_2_pinyin": "Qǐng bǎ mén guān shàng.",
  "example_2_vn": "Làm ơn đóng cửa lại."
}''',
            "korean": '''{
  "pattern": "~아/어요",
  "romanization": "a/eoyo",
  "meaning": "dạng lịch sự thân mật (hiện tại)",
  "topik_level": "TOPIK I",
  "topic": "Kết thúc câu",
  "usage": "Động từ/tính từ + 아요/어요",
  "explanation": "Dạng kết thúc câu lịch sự thông dụng nhất trong giao tiếp.",
  "example": "지금 학교에 가요.",
  "example_romanization": "jigeum hakgyoe gayo.",
  "example_vn": "Bây giờ tôi đi học.",
  "example_2": "밥을 맛있게 먹어요.",
  "example_2_romanization": "babeul masitge meogeoyo.",
  "example_2_vn": "Tôi ăn cơm ngon lành."
}'''
        }

        # Use the effective schema so the sample follows both UI language and
        # any user override made in Prompt Editor.
        raw = get_effective_json_template(
            self._current_lang,
            "grammar" if self._is_grammar else "vocab",
        )

        if isinstance(raw, dict):
            # Multiple sub-samples: show a combo to choose
            sub_keys = list(raw.keys())
            dlg = QDialog(self)
            dlg.setWindowTitle(t(
                "sample_json_title",
                label=_translated_language_label(
                    self._current_lang, grammar=self._is_grammar
                ),
            ))
            dlg.setMinimumWidth(600)
            vl = QVBoxLayout(dlg)

            top_bar = QHBoxLayout()
            top_bar.addWidget(QLabel(t("choose_type_label")))
            cbo = QComboBox()
            cbo.addItems(sub_keys)
            top_bar.addWidget(cbo, 1)
            vl.addLayout(top_bar)

            te = QPlainTextEdit()
            te.setReadOnly(True)
            te.setPlainText(raw[sub_keys[0]])
            te.setStyleSheet("font-family:monospace;font-size:13px;")
            vl.addWidget(te)

            def on_sub_changed(idx):
                te.setPlainText(raw[cbo.currentText()])

            cbo.currentIndexChanged.connect(on_sub_changed)

            btn_copy = QPushButton(t("btn_copy_close"))
            btn_copy.clicked.connect(lambda: (
                QApplication.clipboard().setText(te.toPlainText()),
                dlg.accept()
            ))
            vl.addWidget(btn_copy)
            dlg.exec()
        else:
            dlg = QDialog(self)
            dlg.setWindowTitle(t(
                "sample_json_title",
                label=_translated_language_label(
                    self._current_lang, grammar=self._is_grammar
                ),
            ))
            dlg.setMinimumWidth(600)
            vl = QVBoxLayout(dlg)
            te = QPlainTextEdit()
            te.setReadOnly(True)
            te.setPlainText(raw)
            te.setStyleSheet("font-family:monospace;font-size:13px;")
            vl.addWidget(te)

            btn_copy = QPushButton(t("btn_copy_close"))
            btn_copy.clicked.connect(lambda: (
                QApplication.clipboard().setText(te.toPlainText()),
                dlg.accept()
            ))
            vl.addWidget(btn_copy)
            dlg.exec()

    def _load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("file_dialog_title"), "", t("file_dialog_filter")
        )
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.json_input.setPlainText(f.read())
            except Exception as e:
                showInfo(t("err_file_read", error=e))

    def _schedule_analyze(self):
        """Debounced analyze — chỉ parse JSON khi user ngừng gõ 500ms."""
        self._analyze_timer.start()

    def _analyze_content(self):
        raw = self.json_input.toPlainText().strip()
        if not raw:
            self.raw_data = []
        elif getattr(self, "_learning_mode", "language") == "knowledge":
            try:
                self.raw_data = parse_knowledge_cards(raw)
            except KnowledgeSchemaError as error:
                self.raw_data = []
                self.lbl_raw.setText(t("knowledge_schema_error", error=error))
                return
        else:
            self.raw_data = safe_parse_json(raw)

        self.lbl_raw.setText(t("filter_raw_count", count=len(self.raw_data)))

    def _verify_batch(self):
        try:
            self._verify_batch_impl()
        except Exception as e:
            import traceback
            showInfo(
                t("verify_error_title") + "\n\n" +
                t(
                    "verify_error_message",
                    error=e,
                    details=traceback.format_exc(),
                )
            )

    def _get_model_id(self):
        """Lấy model ID (mid) của model hiện tại — an toàn hơn note: trong find_notes"""
        cfg = self._cfg()
        return AnkiCollectionAdapter(mw.col).model_id_by_name(cfg["model_name"])

    def _verify_batch_impl(self):
        if getattr(self, "_learning_mode", "language") == "knowledge":
            self.preview_list.clear()
            self.prepared_data = []
            if not self.raw_data:
                self.lbl_ready.setText(t("knowledge_no_valid_cards"))
                return
            deck_id = self._current_deck_id()
            if deck_id is None:
                showInfo(t("knowledge_deck_required"))
                return
            run_query(
                self,
                lambda col: read_knowledge_notes_for_deck(col, deck_id),
                self._on_knowledge_duplicate_scan,
                lambda error: showInfo(t("verify_error_message", error=error, details="")),
            )
            return
        cfg = self._cfg()
        self.preview_list.clear()
        self.prepared_data = []

        validation = validate_ai_cards(
            self.raw_data,
            lang=self._current_lang,
            kind="grammar" if self._is_grammar else "vocab",
            require_example="example" in (cfg.get("json_field_map") or {}),
        )
        self._factory_validation_report = validation
        validated_items = list(validation.valid_cards)

        mid = self._get_model_id()
        target_level = self.cbo_level.currentData() or ""
        target_topic = self.txt_topic.text().strip().lower()
        cnt = {
            "dup": validation.duplicate_count,
            "update": 0, "new": 0, "partial": 0, "dup_diff": 0,
        }
        front_field = cfg["front_field"]
        level_field = cfg["level_field"]
        jfm = cfg["json_field_map"]
        meaning_field = jfm.get("meaning", "Meaning")

        def get_front(item):
            dk = cfg["detect_key"]
            return str(item.get(dk, item.get('front', ''))).strip()

        def get_level(item):
            for k, fn in jfm.items():
                if fn == level_field and k in item:
                    return str(item[k]).strip()
            return ''

        # ── Build lookup once: canonical form → notes (tránh N+1 query) ──
        # Canonical keys close Unicode/spacing/punctuation bypasses such as
        # full-width forms or a trailing dash.  The same form is used below
        # for the current batch, not only for cards already in the deck.
        front_to_notes = {}
        front_displays = {}
        meaning_to_notes = {}
        if mid:
            try:
                for note in AnkiCollectionAdapter(mw.col).notes_for_model(mid):
                    try:
                        f = str(note.get(front_field, "")).strip()
                        front_key = normalize_for_comparison(f)
                        if front_key:
                            front_to_notes.setdefault(front_key, []).append(note)
                            front_displays.setdefault(front_key, f)
                        m = str(note.get(meaning_field, "")).strip()
                        meaning_key = normalize_for_comparison(m)
                        if meaning_key:
                            meaning_to_notes.setdefault(meaning_key, []).append(note)
                    except Exception:
                        continue
            except Exception:
                pass

        # The previous verifier only indexed existing notes.  As a result an
        # AI response could repeat an item later in the same batch and both
        # copies would be imported.  Keep a separate in-memory index so every
        # accepted candidate becomes visible to subsequent candidates.
        batch_fronts = {}
        batch_meanings = {}
        batch_identities = set()

        def remember_candidate(front_key, meaning_key, item, front, meaning):
            batch_identities.add((front_key, meaning_key))
            batch_fronts.setdefault(front_key, {
                "item": item, "front": front, "meaning": meaning,
            })
            front_displays.setdefault(front_key, front)
            if meaning_key:
                batch_meanings.setdefault(meaning_key, {
                    "item": item, "front": front, "meaning": meaning,
                })

        def batch_conflict(previous):
            return {
                "existing_front": previous["front"],
                "existing_meaning": previous["meaning"],
                "existing_furigana": "",
                "existing_level": "",
                "existing_nid": None,
            }

        for item in validated_items:

            front = get_front(item)
            level = get_level(item)
            topic = str(item.get('topic', '')).strip().lower()
            meaning = str(item.get('meaning', '')).strip()
            front_key = normalize_for_comparison(front)
            meaning_key = normalize_for_comparison(meaning)

            if not front_key:
                continue
            if target_level and target_level not in level:
                continue
            if target_topic and target_topic not in topic:
                continue

            action, target_nid, updatable = "add", None, []
            conflict_info = None

            # Never permit a later raw item to bypass verification merely
            # because the first duplicate has not been written to Anki yet.
            if (front_key, meaning_key) in batch_identities:
                cnt["dup"] += 1
                continue
            previous = batch_fronts.get(front_key)
            if previous:
                if normalize_for_comparison(previous["meaning"]) == meaning_key:
                    cnt["dup"] += 1
                    continue
                action = "dup_diff"
                cnt["dup_diff"] += 1
                remember_candidate(front_key, meaning_key, item, front, meaning)
                self._add_to_queue(item, action, None, [], cnt, batch_conflict(previous))
                continue

            exact_notes = front_to_notes.get(front_key, [])
            if exact_notes:
                old = exact_notes[0]
                exact_ids = [old.id]
                updatable = self._find_updatable_fields(old, item)
                if updatable:
                    action, target_nid = "update", exact_ids[0]
                    cnt["update"] += 1
                else:
                    # Same spelling/pattern with a different meaning is never
                    # auto-added, including grammar mode.  Legitimate grammar
                    # variants remain available through the explicit approval
                    # dialog instead of acting as a duplicate-detection bypass.
                    try:
                        existing_meaning = old[meaning_field].strip()
                    except Exception:
                        existing_meaning = ""
                    existing_meaning_key = normalize_for_comparison(existing_meaning)

                    if existing_meaning_key and meaning_key and existing_meaning_key != meaning_key:
                        # Cùng mặt chữ nhưng khác nghĩa → đưa vào diện "dup_diff" để người dùng xác nhận
                        action = "dup_diff"
                        cnt["dup_diff"] += 1
                        try:
                            _efuri = str(old[cfg["furi_label"]]).strip()
                        except Exception:
                            _efuri = ""
                        try:
                            _elevel = str(old[level_field]).strip()
                        except Exception:
                            _elevel = ""
                        conflict_info = {
                            "existing_front": str(old[front_field]).strip() if front_field in old else front,
                            "existing_meaning": existing_meaning,
                            "existing_furigana": _efuri,
                            "existing_level": _elevel,
                            "existing_nid": exact_ids[0],
                        }
                    else:
                        cnt["dup"] += 1
                        continue
                remember_candidate(front_key, meaning_key, item, front, meaning)
                self._add_to_queue(item, action, target_nid, updatable, cnt, conflict_info)
                continue

            # A near match is never merged automatically.  It stays in the
            # queue with an explicit warning so the learner retains control.
            near_match = find_near_duplicate(front, front_displays.values())
            if near_match:
                near_front, similarity = near_match
                action = "add_partial"
                cnt["partial"] += 1
                conflict_info = {
                    "near_duplicate": near_front,
                    "similarity": similarity,
                }

            if meaning_key and action == "add":
                same_mean = meaning_to_notes.get(meaning_key) or batch_meanings.get(meaning_key)
                if same_mean:
                    action = "add_partial"
                    cnt["partial"] += 1

            if action in ("add", "add_partial"):
                cnt["new"] += 1
            remember_candidate(front_key, meaning_key, item, front, meaning)
            self._add_to_queue(item, action, target_nid, updatable, cnt, conflict_info)

        self.btn_diff_meaning.setEnabled(cnt["dup_diff"] > 0)
        summary_text = t(
                "verify_summary",
                new=cnt["new"],
                update=cnt["update"],
                partial=cnt["partial"],
                different=cnt["dup_diff"],
                duplicate=cnt["dup"],
            )
        if validation.invalid:
            categories = ", ".join(sorted({issue.category for issue in validation.invalid}))
            summary_text += "\n" + t(
                "factory_validation_blocked",
                count=len(validation.invalid), categories=categories,
            )
        self.lbl_ready.setText(summary_text)
        # Dựng lại danh sách thẻ chờ xuất xưởng (có tìm kiếm + lọc + checkbox)
        self._rebuild_preview()

    def _on_knowledge_duplicate_scan(self, existing_notes):
        result = prepare_knowledge_batch(self.raw_data, existing_notes)
        self.prepared_data = result["prepared"]
        counts = result["counts"]
        self.lbl_ready.setText(t(
            "knowledge_verify_summary",
            new=counts["new"], update=counts["update"], duplicate=counts["duplicate"],
        ))
        self.btn_diff_meaning.setEnabled(False)
        self._rebuild_preview()

    def _add_to_queue(self, item, action, nid, updatable, cnt, conflict_info=None):
        """Thêm thẻ vào hàng chờ xuất xưởng (prepared_data).
        Danh sách hiển thị được dựng lại ở cuối _verify_batch_impl qua _rebuild_preview()."""
        self.prepared_data.append({
            "item": item, "action": action,
            "nid": nid, "update_fields": updatable,
            "conflict_info": conflict_info,
        })

    # ═══════════════════════════════════════════════════════
    #  TÌM KIẾM / LỌC / CHỌN THẺ CHỜ XUẤT XƯỞNG
    # ═══════════════════════════════════════════════════════
    def _rebuild_preview(self):
        """Dựng lại danh sách thẻ chờ xuất xưởng theo tìm kiếm + bộ lọc.
        Mỗi dòng: checkbox + số thứ tự (theo danh sách đang hiển thị) + từ + nghĩa + ghi chú."""
        search = self.txt_search.text().strip().lower()
        filt = self.cbo_filter.currentText()
        action_map = {
            t("cbo_filter_all"): None,
            t("cbo_filter_new"): "add",
            t("cbo_filter_update"): "update",
            t("cbo_filter_conflict"): "add_partial",
            t("cbo_filter_diff"): "dup_diff",
        }
        want_action = action_map.get(filt)
        cfg = self._cfg()
        dk = cfg["detect_key"]

        # Lưu trạng thái check theo index để giữ qua mỗi lần dựng lại
        checked = set()
        for row in range(self.preview_list.count()):
            it = self.preview_list.item(row)
            if it.checkState() == Qt.CheckState.Checked:
                idx = it.data(Qt.ItemDataRole.UserRole)
                if idx is not None:
                    checked.add(idx)

        self._visible_indices = []
        for i, d in enumerate(self.prepared_data):
            item = d["item"]
            action = d["action"]
            if getattr(self, "_learning_mode", "language") == "knowledge":
                front = str(item.get("question") or item.get("cloze_text") or "").strip()
                meaning = str(item.get("answer") or item.get("explanation") or "").strip()
            else:
                front = str(item.get(dk, item.get('front', ''))).strip()
                meaning = str(item.get('meaning', '')).strip()
            if want_action and action != want_action:
                continue
            if search and search not in front.lower() and search not in meaning.lower():
                continue
            self._visible_indices.append(i)

        self.preview_list.blockSignals(True)
        self.preview_list.clear()
        for pos, idx in enumerate(self._visible_indices, start=1):
            d = self.prepared_data[idx]
            item = d["item"]
            action = d["action"]
            updatable = d.get("update_fields", [])
            ci = d.get("conflict_info")
            if getattr(self, "_learning_mode", "language") == "knowledge":
                front = str(item.get("question") or item.get("cloze_text") or "").strip()
                preview_meaning = str(item.get("answer") or item.get("explanation") or "")
            else:
                front = str(item.get(dk, item.get('front', ''))).strip()
                preview_meaning = str(item.get("meaning", ""))
            icon = {"add": "✨", "add_partial": "⚠️", "update": "🔄", "dup_diff": "🔍"}.get(action, "✨")
            if action == "dup_diff" and ci:
                suffix = t("preview_suffix_dup_diff",
                           new=item.get('meaning', ''), old=ci.get('existing_meaning', ''))
            elif action == "update" and updatable:
                suffix = t("preview_suffix_update", fields=", ".join(updatable))
            elif ci and ci.get("near_duplicate"):
                suffix = t("preview_suffix_near_duplicate",
                           match=ci["near_duplicate"], score=ci["similarity"])
            elif action == "add_partial":
                suffix = t("preview_suffix_partial")
            else:
                suffix = ""
            li = QListWidgetItem(f"{icon} {pos}: {front} — {preview_meaning}{suffix}")
            li.setFlags(li.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            li.setCheckState(Qt.CheckState.Checked if idx in checked else Qt.CheckState.Unchecked)
            li.setData(Qt.ItemDataRole.UserRole, idx)
            self.preview_list.addItem(li)
        self.preview_list.blockSignals(False)

        # Khóa khoảng số theo số thẻ đang hiển thị
        # (bật cờ để không kích hoạt tự động tích chọn khi đang dựng lại danh sách)
        self._updating_range = True
        try:
            vis_count = len(self._visible_indices)
            if vis_count == 0:
                self.spin_start.setRange(1, 1)
                self.spin_end.setRange(1, 1)
                self.spin_start.setValue(1)
                self.spin_end.setValue(1)
            else:
                self.spin_start.setRange(1, vis_count)
                self.spin_end.setRange(1, vis_count)
                if self.spin_start.value() > vis_count:
                    self.spin_start.setValue(vis_count)
                if self.spin_end.value() > vis_count:
                    self.spin_end.setValue(vis_count)
                if self.spin_start.value() > self.spin_end.value():
                    self.spin_end.setValue(self.spin_start.value())
        finally:
            self._updating_range = False

        self.btn_import.setEnabled(len(self.prepared_data) > 0)
        self.btn_cancel_order.setEnabled(len(self.prepared_data) > 0)
        self._update_selection_label()

    def _on_range_changed(self):
        """Khi đổi khoảng 'Từ số … đến' → tự động tích chọn các thẻ trong khoảng đó."""
        if getattr(self, '_updating_range', False):
            return
        if not hasattr(self, 'preview_list'):
            return
        start = self.spin_start.value()
        end = self.spin_end.value()
        self.preview_list.blockSignals(True)
        for row in range(self.preview_list.count()):
            checked = (start <= row + 1 <= end)
            self.preview_list.item(row).setCheckState(
                Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )
        self.preview_list.blockSignals(False)
        self._update_selection_label()

    def _update_selection_label(self):
        """Cập nhật nhãn số thẻ đã chọn."""
        if not hasattr(self, 'lbl_sel'):
            return
        n_checked = 0
        for row in range(self.preview_list.count()):
            if self.preview_list.item(row).checkState() == Qt.CheckState.Checked:
                n_checked += 1
        vis = len(getattr(self, '_visible_indices', []))
        self.lbl_sel.setText(t("lbl_sel_count", selected=n_checked, total=vis))

    def _select_all_visible(self):
        """Tích chọn tất cả thẻ đang hiển thị."""
        self.preview_list.blockSignals(True)
        for row in range(self.preview_list.count()):
            self.preview_list.item(row).setCheckState(Qt.CheckState.Checked)
        self.preview_list.blockSignals(False)
        self._update_selection_label()

    def _select_none_visible(self):
        """Bỏ chọn tất cả thẻ đang hiển thị."""
        self.preview_list.blockSignals(True)
        for row in range(self.preview_list.count()):
            self.preview_list.item(row).setCheckState(Qt.CheckState.Unchecked)
        self.preview_list.blockSignals(False)
        self._update_selection_label()

    def _get_export_indices(self):
        """Trả về các index (trong prepared_data) sẽ xuất xưởng.
        Ưu tiên các thẻ được tích chọn; nếu không chọn thẻ nào → dùng khoảng Từ-đến
        (theo danh sách đang hiển thị sau khi lọc)."""
        visible = getattr(self, '_visible_indices', None)
        if visible is None:
            visible = list(range(len(self.prepared_data)))
        checked = []
        for row in range(self.preview_list.count()):
            it = self.preview_list.item(row)
            if it.checkState() == Qt.CheckState.Checked:
                idx = it.data(Qt.ItemDataRole.UserRole)
                if idx is not None:
                    checked.append(idx)
        if checked:
            return sorted(set(checked))
        start = max(1, self.spin_start.value()) - 1
        end = min(len(visible), self.spin_end.value())
        if end < start:
            end = start
        return visible[start:end]

    def _remove_factory_indices(self, indices):
        """Xóa các thẻ (theo index trong prepared_data) khỏi xưởng (prepared_data + raw_data),
        rồi dựng lại danh sách và lưu trạng thái."""
        indices = sorted(set(indices))
        removed_items = []
        for i in sorted(indices, reverse=True):
            if 0 <= i < len(self.prepared_data):
                removed_items.append(self.prepared_data[i]["item"])
                del self.prepared_data[i]
        for it in removed_items:
            try:
                self.raw_data.remove(it)
            except ValueError:
                pass
        self.lbl_raw.setText(t("filter_raw_count", count=len(self.raw_data)))
        self.lbl_ready.setText(t("preview_ready", count=len(self.prepared_data)))
        self._rebuild_preview()
        self._save_current_flow()

    def _cancel_order(self):
        """Hủy hàng: xóa toàn bộ hoặc xóa các thẻ đã chọn khỏi xưởng.
        Thẻ chỉ bị xóa khi người dùng chủ động bấm nút này — không bị mất khi đóng cửa sổ."""
        if not self.prepared_data:
            tooltip(t("cancel_order_empty"))
            return
        export_indices = self._get_export_indices()
        n_sel = len(export_indices)
        box = QMessageBox(self)
        box.setWindowTitle(t("cancel_order_title"))
        box.setText(t(
            "cancel_order_message",
            total=len(self.prepared_data),
            selected=n_sel,
        ))
        btn_selected = box.addButton(
            t("cancel_order_selected"), QMessageBox.ButtonRole.ActionRole
        )
        btn_all = box.addButton(
            t("cancel_order_all"), QMessageBox.ButtonRole.ActionRole
        )
        btn_cancel = box.addButton(
            t("cancel_order_cancel"), QMessageBox.ButtonRole.RejectRole
        )
        box.setDefaultButton(btn_cancel)
        box.exec()
        clicked = box.clickedButton()
        if clicked == btn_selected:
            if n_sel == 0:
                tooltip(t("cancel_order_no_selection"))
                return
            self._remove_factory_indices(export_indices)
            self.lbl_status.setText(t("status_cleared_selected", count=n_sel))
        elif clicked == btn_all:
            self._remove_factory_indices(list(range(len(self.prepared_data))))
            self.lbl_status.setText(t("status_cleared_factory"))

    def _show_diff_meaning_report(self):
        """Hiển thị dialog báo cáo các từ vựng có cùng mặt chữ nhưng khác nghĩa,
        cho phép người dùng chọn từ nào được phép thêm vào."""
        cfg = self._cfg()
        changed = show_diff_meaning_dialog(self, self.prepared_data, cfg)
        if not changed:
            return

        # Đếm lại
        remaining_dup_diff = sum(1 for d in self.prepared_data if d["action"] == "dup_diff")
        self.btn_diff_meaning.setEnabled(remaining_dup_diff > 0)
        self.lbl_ready.setText(t("preview_ready", count=len(self.prepared_data)))
        # Dựng lại danh sách theo bộ lọc/tìm kiếm hiện tại
        self._rebuild_preview()

    def _find_updatable_fields(self, note, item):
        cfg = self._cfg()
        updatable = []
        for jk, fn in cfg["json_field_map"].items():
            if fn not in cfg["all_fields"]:
                continue
            try:
                cur = note[fn].strip()
            except Exception:
                continue
            new_val = str(item.get(jk, '')).strip()
            if not cur and new_val:
                updatable.append(fn)

        for audio_fn, src_fn in cfg["audio_fields"]:
            try:
                if not note[audio_fn].strip() and note[src_fn].strip():
                    updatable.append(audio_fn)
            except Exception:
                pass

        return list(dict.fromkeys(updatable))

    @staticmethod
    def _esc(s):
        return s.replace('\\', '\\\\').replace('"', '\\"')

    def _process_import(self):
        if not self.prepared_data:
            return

        export_indices = self._get_export_indices()
        batch = [self.prepared_data[i] for i in export_indices]
        if not batch:
            tooltip(t("import_no_selection"))
            return

        if getattr(self, "_learning_mode", "language") == "language":
            final_validation = validate_ai_cards(
                [entry.get("item") for entry in batch],
                lang=self._current_lang,
                kind="grammar" if self._is_grammar else "vocab",
                require_example="example" in (self._cfg().get("json_field_map") or {}),
            )
            if final_validation.invalid or len(final_validation.valid_cards) != len(batch):
                categories = ", ".join(sorted({
                    issue.category for issue in final_validation.invalid
                }))
                showInfo(t(
                    "factory_validation_blocked",
                    count=len(final_validation.invalid), categories=categories,
                ))
                return

        summary = summarize_import_batch(batch)
        if not askUser(t("confirm_import_preview", **summary), parent=self):
            return

        # Lưu lại các index đã xuất để cập nhật lại xưởng sau khi import xong
        self._last_export_indices = list(export_indices)
        self._last_import_summary = dict(summary)

        cfg = self._cfg()
        deck_id = mw.col.decks.id(self.deck_chooser.currentText())
        self._import_learning_mode = getattr(self, "_learning_mode", "language")

        audio_options = (
            self.chk_audio_vocab.isChecked(),
            self.chk_audio_ex1.isChecked(),
            self.chk_audio_ex2.isChecked()
        )

        self.btn_import.setEnabled(False)
        self.btn_cancel.setVisible(True)
        self.pbar.setMaximum(len(batch))
        self.pbar.setValue(0)
        self.pbar.setVisible(True)

        self._import_cancel_event = threading.Event()
        self.btn_learning_language.setEnabled(False)
        self.btn_learning_knowledge.setEnabled(False)
        for entry in batch:
            entry["audio_enabled"] = (
                audio_options if self._import_learning_mode == "language" else (False, False, False)
            )
        if self._import_learning_mode == "knowledge":
            self._commit_import(batch, cfg, deck_id, {})
            return
        run_query(
            self,
            lambda col: prepare_audio_tasks(col, batch, cfg),
            lambda tasks: self._start_import_audio(batch, cfg, deck_id, tasks),
            self._on_import_error,
        )

    def _start_import_audio(self, batch, cfg, deck_id, audio_tasks):
        """Run only network/TTS work outside Anki's collection executor."""
        if self._import_cancel_event is None or self._import_cancel_event.is_set():
            return
        if not audio_tasks:
            self._commit_import(batch, cfg, deck_id, {})
            return
        self.lbl_status.setText(t("status_generating_audio", count=len(audio_tasks)))
        self.import_worker = ImportWorker(audio_tasks, speed=self.spin_speed.value())
        self.import_worker.progress.connect(self._on_import_progress)
        self.import_worker.finished.connect(
            lambda result: self._commit_import(batch, cfg, deck_id, result["audio_tags"])
        )
        self.import_worker.error.connect(self._on_import_error)
        self.import_worker.start()

    def _commit_import(self, batch, cfg, deck_id, audio_tags):
        if self._import_cancel_event is None or self._import_cancel_event.is_set():
            return
        self.lbl_status.setText(t("status_saving_notes"))
        operation = (
            (lambda col: apply_knowledge_import(
                col, batch, deck_id, self._import_cancel_event.is_set
            ))
            if getattr(self, "_import_learning_mode", "language") == "knowledge"
            else (lambda col: apply_import(
                col, batch, cfg, deck_id, audio_tags, self._import_cancel_event.is_set
            ))
        )
        run_collection(
            self,
            operation,
            self._on_import_finished,
            self._on_import_error,
        )

    def _on_import_progress(self, current, status_text):
        self.pbar.setValue(current)
        self.lbl_status.setText(status_text)
        mw.app.processEvents()

    def _on_import_finished(self, report):
        if self._import_cancel_event is None or self._import_cancel_event.is_set():
            return
        mw.reset()
        self.pbar.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_import.setEnabled(True)
        self.btn_learning_language.setEnabled(True)
        self.btn_learning_knowledge.setEnabled(True)
        self.lbl_status.setText(t("status_done"))

        import_mode = report.get(
            "learning_mode", getattr(self, "_import_learning_mode", "language")
        )
        self._last_imported_note_ids = list(report.get("added_note_ids", []))
        self._last_knowledge_rollback = report if import_mode == "knowledge" else None
        self.btn_rollback_import.setEnabled(bool(
            self._last_imported_note_ids or report.get("updated_before")
        ))

        try:
            write_import_report(report, getattr(self, "_last_import_summary", {}))
        except Exception as error:
            logger.warning("Could not write privacy-safe import report: %s", error)

        idxs = sorted(set(getattr(self, '_last_export_indices', None) or []))
        # Ghi nhận vào lịch sử import
        try:
            deck_name = self.deck_chooser.currentText()
            if report.get('added', 0) > 0 or (import_mode == "knowledge" and report.get("updated", 0) > 0):
                imported_items = [
                    self.prepared_data[i]["item"] for i in idxs
                    if 0 <= i < len(self.prepared_data)
                    and self.prepared_data[i]["action"] in (
                        ("add", "update") if import_mode == "knowledge" else ("add", "add_partial")
                    )
                ]
                if imported_items:
                    add_to_import_history(
                        imported_items,
                        "knowledge" if import_mode == "knowledge" else self._current_lang,
                        deck_name=deck_name,
                        source="manual",
                        kind=("knowledge" if import_mode == "knowledge" else
                              ("grammar" if getattr(self, '_is_grammar', False) else "vocab")),
                        learning_mode=import_mode,
                    )
                invalidate_deck_cache()
        except Exception as e:
            logger.warning("Lỗi ghi lịch sử import: %s", e)

        # Cập nhật lại xưởng: xóa các thẻ đã xuất xưởng → danh sách giảm dần
        self._last_export_indices = None
        self._remove_factory_indices(idxs)

        msg = t(
            "msg_import_success",
            language=(t("item_label_knowledge") if import_mode == "knowledge" else
                      _translated_language_label(self._current_lang, grammar=self._is_grammar)),
            added=report["added"],
            updated=report["updated"],
            audio=report["audio_gen"],
        )
        if report.get("audio_failed", 0):
            msg += t("import_audio_failed", count=report["audio_failed"])
        if report.get('errors', 0) > 0:
            msg += t("import_errors", count=report["errors"])
            if 'errors_detail' in report:
                msg += "\n".join(report['errors_detail'])

        showInfo(msg)
        self.import_worker = None
        self._import_cancel_event = None

    def _rollback_last_import(self):
        """Undo only notes newly created by the latest completed import batch."""
        knowledge_token = getattr(self, "_last_knowledge_rollback", None)
        if knowledge_token:
            count = (
                len(knowledge_token.get("added_note_ids", []))
                + len(knowledge_token.get("updated_before", []))
            )
            if not askUser(t("confirm_rollback_import", count=count), parent=self):
                return
            self.btn_rollback_import.setEnabled(False)
            run_collection(
                self,
                lambda col: rollback_knowledge_import(col, knowledge_token),
                self._on_knowledge_rollback_finished,
                self._on_import_error,
            )
            return
        note_ids = list(getattr(self, "_last_imported_note_ids", []))
        if not note_ids:
            return
        if not askUser(t("confirm_rollback_import", count=len(note_ids)), parent=self):
            return

        try:
            mw.checkpoint(t("rollback_checkpoint"))
            removed = rollback_added_notes(mw.col, note_ids)
            mw.reset()
            invalidate_deck_cache()
            self._last_imported_note_ids = []
            self.btn_rollback_import.setEnabled(False)
            tooltip(t("rollback_import_done", count=removed))
        except Exception as e:
            logger.warning("Rollback import batch failed: %s", e)
            showInfo(t("rollback_import_failed", error=str(e)))

    def _on_knowledge_rollback_finished(self, result):
        mw.reset()
        self._last_knowledge_rollback = None
        self._last_imported_note_ids = []
        self.btn_rollback_import.setEnabled(False)
        invalidate_deck_cache()
        tooltip(t(
            "knowledge_rollback_done",
            removed=result["removed"], restored=result["restored"],
        ))

    def _on_import_error(self, error_msg):
        if self._import_cancel_event is not None and self._import_cancel_event.is_set():
            return
        showInfo(t("import_error", error=error_msg))
        self.btn_import.setEnabled(True)
        self.btn_learning_language.setEnabled(True)
        self.btn_learning_knowledge.setEnabled(True)
        self.btn_cancel.setVisible(False)
        self.pbar.setVisible(False)
        # Không xóa thẻ khỏi xưởng khi import lỗi
        self._last_export_indices = None

    def _cancel_import(self):
        if self._import_cancel_event is None or self._import_cancel_event.is_set():
            return
        self._import_cancel_event.set()
        if self.import_worker:
            self.import_worker.stop()
        self._last_export_indices = None
        self.btn_cancel.setVisible(False)
        self.btn_import.setEnabled(True)
        self.btn_learning_language.setEnabled(True)
        self.btn_learning_knowledge.setEnabled(True)
        self.pbar.setVisible(False)
        self.lbl_status.setText(t("status_stopping"))

    def _prepare_legacy_srs_model(self, cfg):
        """Preserve old multi-card notes before installing conditional templates."""
        if self._is_grammar:
            return
        mm = mw.col.models
        model = mm.by_name(cfg["model_name"])
        if model is None:
            for old_name in cfg.get("old_model_names", []):
                model = mm.by_name(old_name)
                if model is not None:
                    break
        if not needs_legacy_srs_migration(model):
            return
        mw.checkpoint(t("srs_legacy_checkpoint"))
        result = prepare_legacy_srs_model(mw.col, mm, model)
        logger.info(
            "SRS legacy migration preserved %d/%d notes",
            result.changed_notes,
            result.matched_notes,
        )

    def _force_rebuild_model(self):
        cfg = self._cfg()
        mm = mw.col.models
        templates, css = self._model_assets()
        self._prepare_legacy_srs_model(cfg)
        result = ensure_model(
            mm, cfg, templates, css, _build_qfmt, _build_afmt,
            rename_primary_template=False,
            prune_extra_templates=self._is_grammar,
        )
        message_key = "model_rebuilt" if result.existed else "model_created"
        showInfo(t(message_key, model=cfg['model_name']))

    def _model_assets(self):
        """Select card assets; model mutation lives in ``utils.model_lifecycle``."""
        if self._is_grammar:
            return LANG_GRAMMAR_TEMPLATES[self._current_lang], LANG_GRAMMAR_CSS[self._current_lang]()
        return LANG_TEMPLATES[self._current_lang], LANG_CSS[self._current_lang]()

    def get_or_create_model(self):
        cfg = self._cfg()
        templates, css = self._model_assets()
        self._prepare_legacy_srs_model(cfg)
        result = ensure_model(
            mw.col.models, cfg, templates, css, _build_qfmt, _build_afmt,
            rename_primary_template=not self._is_grammar,
            prune_extra_templates=self._is_grammar,
        )
        return result.model

    # ═══════════════════════════════════════════════════════
    #  AI SETTINGS DIALOG (wired → ui/ai_settings.py)
    # ═══════════════════════════════════════════════════════
    def _show_ai_settings(self):
        """Mở dialog cấu hình API Key & endpoint cho AI"""
        show_ai_settings_dialog(self)

    def _ensure_ai_access(self, cfg_api):
        """Return True for configured/cloud or local endpoints; otherwise offer settings."""
        if cfg_api.get("api_key") or "localhost" in cfg_api.get("api_base", ""):
            return True
        reply = QMessageBox.question(
            self,
            t("msg_no_api_key_title"),
            t("msg_no_api_key"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._show_ai_settings()
        return False

    # ═══════════════════════════════════════════════════════
    #  AI TEXT INPUT & EXTRACT (quét deck → AI → tránh trùng)
    # ═══════════════════════════════════════════════════════
    @staticmethod
    def _warn_reasoner_model():
        """Cảnh báo nếu đang dùng model reasoning (chậm, dễ timeout)"""
        cfg_api = get_api_config()
        model = cfg_api.get("model", "")
        if "reasoner" in model.lower():
            tooltip(t("msg_reasoner_warning", model=model))

    def _ai_clear_text(self):
        """Xóa text input, file kẹp và reset trạng thái (lưu luồng rỗng)"""
        self.ai_text_input.clear()
        self.lbl_ai_status.setText("")
        self.lbl_ai_status.setStyleSheet("color:rgba(234,240,246,0.7);font-size:11px;font-weight:normal;")
        self._ai_attached_files = []
        self._ai_attached_paths = []
        self.lbl_ai_files.setText("")
        self._save_current_flow()

    def _attach_ai_files(self):
        """📎 Đính kèm file tài liệu tham khảo → AI đọc text để trích xuất.

        DeepSeek/OpenAI chat chỉ nhận TEXT → add-on tự trích text từ file tại máy
        (txt/md/csv/pdf/docx/doc/xlsx/xls) rồi đưa vào ô AI làm tham khảo.
        """
        paths, _ = QFileDialog.getOpenFileNames(
            self, t("file_attach_dialog_title"),
            "",
            t("file_attach_dialog_filter"),
        )
        if not paths:
            return

        from utils.ai_extractor import MissingDocumentDependencyError, extract_text_from_file
        self.lbl_ai_status.setText(t("status_reading_file"))
        mw.app.processEvents()

        new_files = []
        ok_paths = []
        combined_parts = []
        errors = []
        for p in paths:
            name = os.path.basename(p)
            try:
                text = extract_text_from_file(p)
            except MissingDocumentDependencyError as e:
                errors.append(
                    f"• {name}: "
                    + t(
                        "status_document_dependency_missing",
                        package=e.requirement,
                        command=e.install_command,
                    )
                )
                continue
            except Exception as e:
                errors.append(f"• {name}: {e}")
                continue
            if not text.strip():
                errors.append(f"• {name}: {t('file_content_unreadable')}")
                continue
            new_files.append((name, text))
            ok_paths.append(p)
            combined_parts.append(f"===== 📄 FILE: {name} =====\n{text}")

        if not new_files:
            self.lbl_ai_status.setText("")
            showInfo(t("status_no_file_content", errors="\n".join(errors)))
            return

        self._ai_attached_files.extend(new_files)
        self._ai_attached_paths.extend(ok_paths)

        # Đưa nội dung file vào ô AI để làm tài liệu tham khảo
        combined = "\n\n".join(combined_parts)
        current = self.ai_text_input.toPlainText()
        if current.strip():
            self.ai_text_input.setPlainText(current.rstrip() + "\n\n" + combined)
        else:
            self.ai_text_input.setPlainText(combined)

        self._update_ai_files_label()
        self.lbl_ai_status.setText("")
        self._save_current_flow()

        if errors:
            tooltip(t(
                "tooltip_files_attached_partial",
                count=len(new_files),
                errors="\n".join(errors),
            ))
        else:
            tooltip(t("tooltip_files_attached", count=len(new_files)))

    def _clear_ai_files(self):
        """🧹 Bỏ toàn bộ file đã kẹp và xóa nội dung ô AI (lưu luồng rỗng)."""
        self._ai_attached_files = []
        self._ai_attached_paths = []
        self.ai_text_input.clear()
        self.lbl_ai_files.setText("")
        self._save_current_flow()
        tooltip(t("tooltip_files_cleared"))

    def _update_ai_files_label(self):
        names = ", ".join(n for n, _ in self._ai_attached_files)
        total_chars = sum(len(t) for _, t in self._ai_attached_files)
        self.lbl_ai_files.setText(t(
            "status_attached_files",
            count=len(self._ai_attached_files),
            chars=total_chars,
            names=names,
        ))

    def _get_existing_words_for_ai(self):
        """Lấy danh sách từ hiện có trong deck (có cache 30 phút)"""
        if getattr(self, "_learning_mode", "language") == "knowledge":
            return list(getattr(self, "_ai_existing_words", []) or [])
        cfg = self._cfg()
        deck_name = self.deck_chooser.currentText()
        if not deck_name:
            return []
        try:
            deck_id = mw.col.decks.id(deck_name)
            words = get_existing_vocab_from_deck(
                cfg["model_name"], deck_id, cfg["front_field"]
            )
            return words
        except Exception as e:
            logger.warning("Lỗi lấy deck vocab: %s", e)
            return []

    def _confirm_ai_budget(self, text):
        """Show a privacy-safe AI estimate and require explicit confirmation."""
        try:
            estimate = get_ai_session_estimate(text)
        except Exception as error:
            logger.warning("Could not estimate AI session budget: %s", error)
            showInfo(t("ai_budget_estimate_failed"))
            return False
        if estimate.get("input_truncated") or estimate.get("blocked_reason"):
            showInfo(t(
                "ai_budget_blocked",
                input_limit=estimate["max_input_chars"],
                token_limit=estimate["max_tokens"],
                cost_limit=estimate["max_cost_usd"],
            ))
            return False
        remaining_tokens = max(0, estimate["max_tokens"] - estimate["used_tokens"])
        remaining_cost = max(0.0, estimate["max_cost_usd"] - estimate["used_cost_usd"])
        return askUser(t(
            "confirm_ai_budget",
            calls=estimate["calls"], tokens=estimate["total_tokens"], cost=estimate["cost_usd"],
            remaining_tokens=remaining_tokens, remaining_cost=remaining_cost,
        ), parent=self)

    def _ai_extract(self):
        """Quét deck → gọi AI với context tránh trùng → preview"""
        text = self.ai_text_input.toPlainText().strip()
        if not text:
            tooltip(t("err_no_text"))
            return

        cfg_api = get_api_config()
        if not self._ensure_ai_access(cfg_api):
            return

        # Cảnh báo nếu dùng model reasoning (chậm)
        self._warn_reasoner_model()

        custom_instr = self.ai_instruction.text().strip()

        # Disable UI
        self.btn_ai_extract.setEnabled(False)
        self.btn_ai_chat.setEnabled(False)
        self.btn_ai_batch.setEnabled(False)
        self.btn_ai_settings.setEnabled(False)
        self.btn_ai_clear_text.setEnabled(False)
        self.btn_learning_language.setEnabled(False)
        self.btn_learning_knowledge.setEnabled(False)
        self.lbl_ai_status.setText(t("status_scanning_deck"))
        self.lbl_ai_status.setStyleSheet("color:#e67e22;font-size:11px;font-weight:bold;")
        self.btn_ai_stop.setVisible(True)
        mw.app.processEvents()

        # Lưu params để dùng trong callback
        self._ai_pending_text = text
        self._ai_pending_instr = custom_instr
        self._ai_workflow.begin()

        # Collection reads use Anki's serialized QueryOp; the following AI
        # request remains network-only.
        cfg = self._cfg()
        deck_name = self.deck_chooser.currentText()
        if deck_name:
            try:
                deck_id = mw.col.decks.id(deck_name)
                scan = (
                    (lambda col: read_knowledge_duplicate_keys(col, deck_id))
                    if getattr(self, "_learning_mode", "language") == "knowledge"
                    else (lambda col: get_existing_vocab_from_deck(
                        cfg["model_name"], deck_id, cfg["front_field"], collection=col
                    ))
                )
                run_query(
                    self,
                    scan,
                    self._on_deck_scan_finished,
                    self._on_deck_scan_error,
                )
                return
            except Exception as e:
                logger.warning("Lỗi khởi tạo deck scan: %s", e)

        # Fallback: nếu không scan được deck, gọi AI luôn
        self._start_ai_extract(text, custom_instr, [])

    def _on_deck_scan_progress(self, msg):
        self.lbl_ai_status.setText(msg)
        mw.app.processEvents()

    def _on_deck_scan_finished(self, existing_words):
        self._ai_existing_words = list(existing_words or [])
        text = getattr(self, '_ai_pending_text', '')
        instr = getattr(self, '_ai_pending_instr', '')
        self._start_ai_extract(text, instr, existing_words)

    def _on_deck_scan_error(self, err_msg):
        logger.warning("Deck scan error: %s", err_msg)
        text = getattr(self, '_ai_pending_text', '')
        instr = getattr(self, '_ai_pending_instr', '')
        self._start_ai_extract(text, instr, [])

    def _start_ai_extract(self, text, custom_instr, existing_words):
        """Khởi động AI extract thread sau khi đã có existing_words"""
        if self._ai_workflow.is_cancelled():
            return

        if not self._confirm_ai_budget(text):
            self._enable_ai_buttons()
            return
        if existing_words:
            self.lbl_ai_status.setText(t("status_deck_count", count=len(existing_words)))
        else:
            self.lbl_ai_status.setText(t("status_calling_ai"))
        mw.app.processEvents()

        self._ai_workflow.start_extract(
            AiExtractThread,
            text=text,
            lang=self._current_lang,
            custom_instruction=custom_instr,
            existing_words=existing_words,
            grammar=self._is_grammar,
            learning_mode=getattr(self, "_learning_mode", "language"),
            on_progress=self._on_ai_progress,
            on_finished=self._on_ai_finished,
            on_error=self._on_ai_error,
        )

    def _on_ai_progress(self, msg):
        self.lbl_ai_status.setText(msg)
        self.lbl_ai_status.setStyleSheet("color:#e67e22;font-size:11px;font-weight:bold;")
        mw.app.processEvents()

    def _on_ai_finished(self, vocab_list):
        self._enable_ai_buttons()

        # Giữ nguyên status từ progress_callback (đã chứa token/cost info)
        # chỉ thêm emoji check nếu chưa có
        current = self.lbl_ai_status.text()
        if not current.startswith("✅"):
            self.lbl_ai_status.setText(f"✅ {current}")
        self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")

        # Lưu tạm để preview
        self._ai_vocab_list = vocab_list

        # Mở dialog Xem Trước & Chỉnh Sửa
        self._show_ai_preview(vocab_list)

        self._ai_workflow.clear_extract_worker()

    def _on_ai_error(self, error_msg):
        self._enable_ai_buttons()

        self.lbl_ai_status.setText(t("batch_status_error", error=error_msg[:80]))
        self.lbl_ai_status.setStyleSheet("color:#e74c3c;font-size:11px;font-weight:bold;")

        showInfo(t("err_ai_extract_title") + f"\n\n{error_msg}")
        self._ai_workflow.clear_extract_worker()

    def _enable_ai_buttons(self):
        self.btn_ai_extract.setEnabled(True)
        self.btn_ai_chat.setEnabled(True)
        self.btn_ai_batch.setEnabled(self._learning_mode == "language")
        self.btn_ai_settings.setEnabled(True)
        self.btn_ai_clear_text.setEnabled(True)
        self.btn_mode_vocab.setEnabled(True)
        self.btn_mode_grammar.setEnabled(True)
        self.btn_learning_language.setEnabled(True)
        self.btn_learning_knowledge.setEnabled(True)
        self.btn_ai_stop.setVisible(False)

    # ═══════════════════════════════════════════════════════
    #  AI BATCH PROCESS — Xử lý danh sách từ vựng lớn
    # ═══════════════════════════════════════════════════════
    def _ai_batch_process(self):
        """Mở dialog xử lý danh sách từ vựng lớn qua AI"""
        if getattr(self, "_learning_mode", "language") == "knowledge":
            # Guard programmatic/stale signal calls as well as hiding the UI.
            return
        cfg_api = get_api_config()
        if not self._ensure_ai_access(cfg_api):
            return

        cfg = self._cfg()
        try:
            deck_id = mw.col.decks.id(self.deck_chooser.currentText())
            run_query(
                self,
                lambda col: get_existing_vocab_from_deck(
                    cfg.get("model_name", ""), deck_id, cfg.get("front_field", "Front"), collection=col
                ),
                self._open_batch_dialog,
                lambda _error: self._open_batch_dialog([]),
            )
        except Exception:
            self._open_batch_dialog([])

    def _open_batch_dialog(self, existing_words):
        from ui.batch_dialog import BatchWordListDialog
        dlg = BatchWordListDialog(
            lang=self._current_lang,
            existing_words=existing_words,
            parent=self,
            grammar=self._is_grammar,
        )
        if dlg.exec():
            vocab_list = dlg.get_result_vocab()
            if vocab_list:
                label = t("item_label_grammar_short") if self._is_grammar else t("item_label_vocab_short")
                reliability = dlg.get_reliability_report()
                if reliability.get("missing"):
                    self.lbl_ai_status.setText(t(
                        "batch_status_partial_complete",
                        requested=reliability.get("requested", len(vocab_list)),
                        valid=len(vocab_list), unresolved=reliability["missing"],
                        retries=reliability.get("retries", 0),
                    ))
                    self.lbl_ai_status.setStyleSheet("color:#e67e22;font-size:11px;font-weight:bold;")
                else:
                    self.lbl_ai_status.setText(t("status_batch_done", count=len(vocab_list), label=label))
                    self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")
                # Đổ JSON vào text input để hiển thị trong xưởng
                import json as _json
                json_str = _json.dumps(vocab_list, indent=2, ensure_ascii=False)
                self.json_input.setPlainText(json_str)
                self.raw_data = list(vocab_list)
                self.lbl_raw.setText(t("filter_raw_count", count=len(self.raw_data)))
                # Mở preview dialog để người dùng xem và chỉnh sửa
                self._show_ai_preview(vocab_list)
            else:
                self.lbl_ai_status.setText(t("status_batch_empty"))
                self.lbl_ai_status.setStyleSheet("color:#e67e22;font-size:11px;")

    # ═══════════════════════════════════════════════════════
    #  AI CHAT — Gửi câu hỏi/yêu cầu đến AI (không cần text)
    # ═══════════════════════════════════════════════════════
    def _ai_chat(self):
        """Open Forge Workspace with source and production instruction separated."""
        source_text = self.ai_text_input.toPlainText().strip()
        custom_instr = self.ai_instruction.text().strip()
        from ui.ai_companion import show_ai_study_dialog

        show_ai_study_dialog(
            language=self._current_lang,
            initial_text=custom_instr,
            source_text=source_text,
            learning_mode=getattr(self, "_learning_mode", "language"),
            lane="grammar" if self._is_grammar else "vocab",
        )

    def _ai_chat_legacy(self):
        """Legacy one-shot dialog retained temporarily for compatibility."""
        user_msg = self.ai_text_input.toPlainText().strip()
        custom_instr = self.ai_instruction.text().strip()

        # Kết hợp message
        full_message = ""
        if custom_instr:
            full_message = custom_instr
        if user_msg:
            if full_message:
                full_message += "\n\n---\n" + user_msg
            else:
                full_message = user_msg

        if not full_message:
            # Cho phép gửi trống — AI sẽ phản hồi dựa trên ngữ cảnh Anki
            full_message = t("chat_default_message")

        # Bảo vệ context: cắt theo max_chars trong Cài Đặt AI (mặc định 45k), không cứng 30k
        _chat_cfg = get_api_config()
        _MAX_CHAT_CHARS = int(_chat_cfg.get("max_chars", 45000) or 45000)
        _MAX_CHAT_CHARS = max(10000, min(45000, _MAX_CHAT_CHARS))
        if len(full_message) > _MAX_CHAT_CHARS:
            tooltip(t(
                "chat_truncated_warning",
                length=len(full_message),
                limit=_MAX_CHAT_CHARS,
            ))
            full_message = (
                full_message[:_MAX_CHAT_CHARS]
                + "\n\n"
                + t("chat_truncated_suffix")
            )

        cfg_api = get_api_config()
        if not self._ensure_ai_access(cfg_api):
            return

        # Cảnh báo nếu dùng model reasoning (chậm)
        self._warn_reasoner_model()

        # Disable UI
        self.btn_ai_chat.setEnabled(False)
        self.btn_ai_extract.setEnabled(False)
        self.btn_ai_batch.setEnabled(False)
        self.btn_ai_settings.setEnabled(False)
        self.btn_ai_clear_text.setEnabled(False)
        self.btn_mode_vocab.setEnabled(False)
        self.btn_mode_grammar.setEnabled(False)

        # Khởi tạo conversation history nếu chưa có
        if not hasattr(self, '_ai_chat_history'):
            self._ai_chat_history = []

        # Ước tính thời gian
        import time as _time
        model = cfg_api.get("model", "")
        is_reasoner = "reasoner" in model.lower()
        est_seconds = 300 if is_reasoner else 30
        est_text = f"~{est_seconds // 60}ph" if est_seconds >= 60 else f"~{est_seconds}s"

        # Bắt đầu đếm thời gian
        self._ai_chat_start_time = _time.time()
        if not hasattr(self, '_ai_chat_timer'):
            self._ai_chat_timer = QTimer(self)
            self._ai_chat_timer.timeout.connect(self._update_ai_chat_timer)
        self._ai_chat_timer.start(1000)

        self.lbl_ai_status.setText(t("status_connecting_elapsed", elapsed="00:00", estimate=est_text))
        self.lbl_ai_status.setStyleSheet("color:#2980b9;font-size:11px;font-weight:bold;")

        # Hiện nút dừng
        self.btn_ai_stop.setVisible(True)
        mw.app.processEvents()

        # Snapshot Collection context through QueryOp before starting the
        # network-only chat worker.
        self._ai_workflow.begin()
        run_query(
            self,
            lambda col: query_anki_context(full_message, self._current_lang, collection=col),
            lambda context: self._start_ai_chat_thread(full_message, context),
            self._on_ai_chat_error,
        )

    def _start_ai_chat_thread(self, full_message, anki_context):
        if self._ai_workflow.is_cancelled():
            return

        if not self._confirm_ai_budget(full_message):
            return
        self._ai_workflow.start_chat(
            AiChatThread,
            message=full_message,
            lang=self._current_lang,
            conversation_history=self._ai_chat_history if len(self._ai_chat_history) > 0 else None,
            anki_context=anki_context,
            card_kind="grammar" if self._is_grammar else "vocab",
            on_progress=self._on_ai_chat_progress,
            on_finished=self._on_ai_chat_finished,
            on_error=self._on_ai_chat_error,
        )

    def _on_ai_chat_progress(self, msg):
        elapsed = self._get_elapsed_str()
        self.lbl_ai_status.setText(f"⏱ {elapsed} | {msg}")
        self.lbl_ai_status.setStyleSheet("color:#2980b9;font-size:11px;font-weight:bold;")
        mw.app.processEvents()

    def _on_ai_chat_finished(self, result: dict):
        self._stop_ai_chat_timer()
        self._enable_ai_buttons()
        elapsed = self._get_elapsed_str()
        token_info = result.get("token_info")
        status_text = t("status_chat_done", elapsed=elapsed)
        if token_info:
            from utils.ai_extractor import _format_token_report
            status_text += f" | {_format_token_report(token_info)}"
        self.lbl_ai_status.setText(status_text)
        self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")

        # Lưu vào conversation history để lần sau AI có context
        reply_text = result.get("reply", "")
        if reply_text:
            worker = self._ai_workflow.chat_worker
            if worker is not None:
                self._ai_chat_history.append({"role": "user", "content": worker.message})
            self._ai_chat_history.append({"role": "assistant", "content": reply_text[:3000]})
            # Giới hạn 30 tin nhắn
            if len(self._ai_chat_history) > 30:
                self._ai_chat_history = self._ai_chat_history[-30:]

        self._ai_workflow.clear_chat_worker()

        # Mở dialog chat hiển thị kết quả
        self._show_ai_chat_dialog(result)

    def _on_ai_chat_error(self, error_msg):
        self._stop_ai_chat_timer()
        self._enable_ai_buttons()
        elapsed = self._get_elapsed_str()
        self.lbl_ai_status.setText(t("status_chat_error", elapsed=elapsed, error=error_msg[:60]))
        self.lbl_ai_status.setStyleSheet("color:#e74c3c;font-size:11px;font-weight:bold;")
        showInfo(t("err_ai_chat_title") + f"\n\n{error_msg}")
        self._ai_workflow.clear_chat_worker()

    def _get_elapsed_str(self) -> str:
        """Trả về thời gian đã trôi qua dạng MM:SS"""
        if not hasattr(self, '_ai_chat_start_time'):
            return "00:00"
        import time as _time
        elapsed = int(_time.time() - self._ai_chat_start_time)
        return f"{elapsed // 60:02d}:{elapsed % 60:02d}"

    def _update_ai_chat_timer(self):
        """Cập nhật hiển thị đồng hồ đếm"""
        if hasattr(self, '_ai_chat_start_time') and self._ai_chat_timer.isActive():
            elapsed = self._get_elapsed_str()
            current = self.lbl_ai_status.text()
            # Chỉ cập nhật phần thời gian
            import re
            new_text = re.sub(r'⏱ \d{2}:\d{2}', f'⏱ {elapsed}', current)
            self.lbl_ai_status.setText(new_text)

    def _stop_ai_chat_timer(self):
        """Dừng đồng hồ đếm và ẩn nút dừng"""
        if hasattr(self, '_ai_chat_timer'):
            self._ai_chat_timer.stop()
        self.btn_ai_stop.setVisible(False)

    def _cancel_ai_chat(self):
        """Dừng tác vụ AI (cả chat và extract)"""
        # Signal cancellation only. Never block the UI waiting for a network
        # thread, and never forcibly terminate one.
        self._ai_workflow.cancel()

        self._stop_ai_chat_timer()
        self._enable_ai_buttons()
        elapsed = self._get_elapsed_str() if hasattr(self, '_ai_chat_start_time') else "?"
        self.lbl_ai_status.setText(t("status_stopped_ai", elapsed=elapsed))
        self.lbl_ai_status.setStyleSheet("color:#e67e22;font-size:11px;font-weight:bold;")
        tooltip(t("tooltip_stopped_ai"))

    def _show_ai_chat_dialog(self, result: dict):
        """Hiển thị dialog chat với phản hồi của AI"""
        reply_text = result.get("reply", "")
        vocab_json = result.get("card_json", result.get("vocab_json"))
        card_kind = result.get("card_kind", "vocab")
        error = result.get("error")
        card_warning = result.get("card_warning")

        dlg = AiChatDialog(
            reply_text=reply_text,
            vocab_json=vocab_json,
            error=error,
            card_warning=card_warning,
            card_kind=card_kind,
            parent=self,
        )

        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.accepted_vocab:
            # Đổ đúng card kind đã snapshot khi gửi request vào RAW/Xưởng.
            wants_grammar = card_kind == "grammar"
            if bool(getattr(self, "_is_grammar", False)) != wants_grammar:
                self._select_mode(wants_grammar)
            json_str = json.dumps(dlg.accepted_vocab, indent=2, ensure_ascii=False)
            self.json_input.setPlainText(json_str)
            self._schedule_analyze()

            # Ghi nhận vào lịch sử import
            try:
                deck_name = self.deck_chooser.currentText()
                add_to_import_history(
                    dlg.accepted_vocab,
                    self._current_lang,
                    deck_name=deck_name,
                    source="ai_chat",
                    kind=card_kind,
                )
            except Exception as e:
                logger.warning("Lỗi ghi lịch sử AI chat: %s", e)

            status_key = (
                "status_poured_grammar" if card_kind == "grammar"
                else "status_poured_vocab"
            )
            message_key = (
                "msg_chat_poured_grammar" if card_kind == "grammar"
                else "msg_chat_poured"
            )
            self.lbl_ai_status.setText(t(status_key, count=len(dlg.accepted_vocab)))
            self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")
            showInfo(t(message_key, count=len(dlg.accepted_vocab)))

    # ═══════════════════════════════════════════════════════
    #  DIALOG XEM TRƯỚC & CHỈNH SỬA THẺ SAU AI (wired → ui/ai_preview.py)
    # ═══════════════════════════════════════════════════════
    def _show_ai_preview(self, vocab_list):
        """Mở dialog cho phép xem, sửa, xóa, tái tạo từng thẻ"""
        show_ai_preview_dialog(
            parent=self,
            vocab_list=vocab_list,
            lang=self._current_lang,
            ai_text_input=self.ai_text_input,
            ai_instruction=self.ai_instruction,
            lbl_ai_status=self.lbl_ai_status,
            get_existing_words_fn=self._get_existing_words_for_ai,
            on_finalize_callback=self._finalize_ai_vocab,
            grammar=self._is_grammar,
            learning_mode=getattr(self, "_learning_mode", "language"),
        )

    def load_card_artifact(self, artifact):
        """Load a validated Study Session snapshot into Xưởng without AI."""
        from utils.ai_card_artifacts import artifact_to_factory_payload

        language, kind, cards = artifact_to_factory_payload(artifact)
        if getattr(self, "_learning_mode", "language") != "language":
            self._select_learning_mode("language", persist=False, announce=False)
        if self._current_lang != language:
            self._select_lang(language)
        self._select_mode(kind == "grammar")
        self.json_input.setPlainText(json.dumps(cards, indent=2, ensure_ascii=False))
        self._schedule_analyze()
        self.lbl_ai_status.setText(t("study_sent_forge"))
        self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")

    def _finalize_ai_vocab(self, final_list):
        """Nhận dữ liệu cuối cùng từ AI preview, đổ vào json_input và phân tích"""
        if not final_list:
            tooltip(t("err_no_words"))
            return

        if getattr(self, "_learning_mode", "language") == "knowledge":
            try:
                final_list = parse_knowledge_cards(json.dumps(final_list, ensure_ascii=False))
            except KnowledgeSchemaError as error:
                showInfo(t("knowledge_schema_error", error=error))
                return

        # Đổ vào json_input
        json_str = json.dumps(final_list, indent=2, ensure_ascii=False)
        self.json_input.setPlainText(json_str)
        self._schedule_analyze()

        final_kind = (
            "grammar"
            if getattr(self, "_learning_mode", "language") == "language"
            and getattr(self, "_is_grammar", False)
            else "vocab"
        )

        # Language preserves its legacy preview history. Knowledge is recorded
        # only after a successful CollectionOp import.
        if getattr(self, "_learning_mode", "language") == "language":
            try:
                deck_name = self.deck_chooser.currentText()
                add_to_import_history(
                    final_list,
                    self._current_lang,
                    deck_name=deck_name,
                    source="ai_extract",
                    kind=final_kind,
                )
            except Exception as e:
                logger.warning("Lỗi ghi lịch sử AI extract: %s", e)

        status_key = (
            "status_poured_grammar" if final_kind == "grammar"
            else "status_poured_vocab"
        )
        self.lbl_ai_status.setText(t(status_key, count=len(final_list)))
        self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")

        showInfo(t("msg_extract_poured", count=len(final_list)))

    # ═══════════════════════════════════════════════════════
    #  LỊCH SỬ AI — Xem lại & đưa vào xưởng để import lại
    # ═══════════════════════════════════════════════════════
    def _open_history_browser(self):
        """Mở dialog xem lịch sử từ vựng đã lưu (AI/import) và đưa lại vào xưởng."""
        from ui.history_dialog import HistoryBrowserDialog

        current_history = (
            "knowledge" if getattr(self, "_learning_mode", "language") == "knowledge"
            else self._current_lang
        )
        dlg = HistoryBrowserDialog(parent=self, current_lang=current_history)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.accepted_items:
            self._load_history_to_factory(dlg.accepted_lang, dlg.accepted_items)

    def _load_history_to_factory(self, lang, items):
        """Đưa các từ đã chọn từ lịch sử vào xưởng (json_input + kho hàng) để kiểm định lại."""
        if not items:
            return
        if lang == "knowledge":
            if not hasattr(self, "_learning_mode"):
                self._learning_mode = "language"
            self._select_learning_mode("knowledge", persist=True, announce=False)
        elif lang and lang in LANG_CONFIG and lang != self._current_lang:
            if hasattr(self, "_learning_mode") and self._learning_mode != "language":
                self._select_learning_mode("language", persist=True, announce=False)
            self._current_lang = lang
            self._on_lang_changed()
        json_str = json.dumps(items, indent=2, ensure_ascii=False)
        self.json_input.setPlainText(json_str)
        self._analyze_content()
        # Strict Knowledge parsing remains authoritative; Language preserves
        # the legacy fallback used for old history entries.
        if getattr(self, "_learning_mode", "language") == "language":
            self.raw_data = list(items)
        self.lbl_raw.setText(t("filter_raw_count", count=len(self.raw_data)))
        self.lbl_ai_status.setText(t("status_pulled_history", count=len(items)))
        self.lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")
        tooltip(t("tooltip_pulled_history", count=len(items)))


# ═══════════════════════════════════════════════════════════
#  REVIEWER HOOKS (wired → hooks/reviewer.py) + OVERVIEW MODE
# ═══════════════════════════════════════════════════════════
register_hooks()
register_overview_hooks()


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════
def start_smart_factory():
    mw.factory_dialog = AnkiSmartFactory(mw)
    mw.factory_dialog.show()


# Đăng ký action trên menu Tools. Khi add-on này là ADD-ON ĐỘC LẬP (nằm thẳng
# trong addons21), Anki tự import nó — `mw.form.menuTools` có thể chưa sẵn sàng
# ở thời điểm module load → bọc guard để không crash, defer qua main_window_did_init.
def _register_tools_menu_action():
    try:
        if mw is None or getattr(mw, "form", None) is None:
            return False
        tools = getattr(mw.form, "menuTools", None)
        if tools is None:
            return False
        action = QAction(t("menu_entry"), mw)
        action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        qconnect(action.triggered, start_smart_factory)
        tools.addAction(action)
        try:
            from ui.ai_companion import register_companion_shortcut
            register_companion_shortcut()
        except Exception as exc:
            logger.warning("AI companion shortcut unavailable: %s", exc.__class__.__name__)
        return True
    except Exception:
        return False


if not _register_tools_menu_action():
    try:
        gui_hooks.main_window_did_init.append(_register_tools_menu_action)
    except Exception:
        pass

