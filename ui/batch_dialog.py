"""Supervised production for large vocabulary/grammar inventories."""

import json

from aqt.qt import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    Qt,
    QTimer,
    QVBoxLayout,
)
from aqt.utils import tooltip

from utils.ai_extractor import get_api_config, is_openrouter
from utils.ai_inventory_scanner import (
    canonicalize_topics,
    inventory_from_scan_rows,
    inventory_source_from_file,
    inventory_source_from_files,
    inventory_source_from_text,
)
from utils.batch_processor import (
    apply_supervised_metadata,
    estimate_batch_cost,
    filter_supervised_inventory,
    load_supervised_progress,
    recommended_quality_v2_batch_size,
    recommended_supervised_run_size,
    save_supervised_progress,
    supervised_existing_ids,
    supervised_result_ids,
)
from utils.i18n import t
from utils.language_identity import normalize_language


_UNCLASSIFIED = "__unclassified__"


class BatchWordListDialog(QDialog):
    """Prepare reviewable production runs instead of processing a source blindly."""

    def __init__(
        self,
        lang="japanese",
        existing_words=None,
        parent=None,
        grammar=False,
        workshop_text="",
        workshop_paths=None,
    ):
        super().__init__(parent)
        self.grammar = bool(grammar)
        self.lang = normalize_language(lang)
        self.existing_words = list(existing_words or ())
        self._workshop_text = str(workshop_text or "")
        self._workshop_paths = list(workshop_paths or ())
        self._inventory = []
        self._inventory_source = None
        self._scan_rows = []
        self._scan_counts = {}
        self._topic_catalog = []
        self._topic_catalog_ready = False
        self._source_id = ""
        self._persisted_completed_ids = set()
        self._existing_completed_ids = set()
        self._session_completed_ids = set()
        self._active_items = []
        self._batch_thread = None
        self._scan_thread = None
        self._refreshing = False
        self._last_report = {}
        self.result_vocab = []
        self._is_openrouter = is_openrouter()
        self.slow_mode = self._is_openrouter

        self.setWindowTitle(t(
            "supervised_title_grammar" if self.grammar else "supervised_title_vocab"
        ))
        self.setMinimumSize(860, 720)
        self.resize(980, 820)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self._setup_ui()
        self._update_selection(reset_quantity=True)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        language = {
            "japanese": t("lang_japanese"),
            "chinese": t("lang_chinese"),
            "korean": t("lang_korean"),
            "english": t("lang_english"),
        }[self.lang]
        header_key = "supervised_header_grammar" if self.grammar else "supervised_header_vocab"
        header = QLabel(
            f"<h3>{t(header_key, language=language)}</h3>"
            f"<p style='color:#555;font-size:11px;'>{t('supervised_desc')}</p>"
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        source_group = QGroupBox(t("supervised_source_group"))
        source_layout = QVBoxLayout(source_group)
        source_actions = QHBoxLayout()
        self.btn_take_workshop = QPushButton(t("supervised_take_workshop"))
        self.btn_take_workshop.setEnabled(bool(
            self._workshop_text.strip() or self._workshop_paths
        ))
        self.btn_take_workshop.setToolTip(t("supervised_take_workshop_tip"))
        self.btn_take_workshop.clicked.connect(self._take_workshop_source)
        source_actions.addWidget(self.btn_take_workshop)
        self.btn_open_file = QPushButton(t("supervised_open_file"))
        self.btn_open_file.clicked.connect(self._open_source_file)
        source_actions.addWidget(self.btn_open_file)
        self.btn_analyze = QPushButton(t("supervised_analyze"))
        self.btn_analyze.clicked.connect(self._analyze_inventory)
        source_actions.addWidget(self.btn_analyze)
        self.btn_scan_details = QPushButton(t("supervised_scan_details"))
        self.btn_scan_details.clicked.connect(self._show_scan_details)
        self.btn_scan_details.setEnabled(False)
        source_actions.addWidget(self.btn_scan_details)
        source_actions.addStretch(1)
        source_layout.addLayout(source_actions)

        self.txt_input = QTextEdit()
        self.txt_input.setPlaceholderText(t("supervised_source_placeholder"))
        self.txt_input.setMinimumHeight(150)
        self.txt_input.textChanged.connect(self._source_edited)
        source_layout.addWidget(self.txt_input)
        layout.addWidget(source_group)

        filter_group = QGroupBox(t("supervised_filter_group"))
        filter_layout = QGridLayout(filter_group)
        filter_layout.addWidget(QLabel(t("supervised_topic")), 0, 0)
        self.cbo_topic = QComboBox()
        self.cbo_topic.currentIndexChanged.connect(self._filter_changed)
        filter_layout.addWidget(self.cbo_topic, 0, 1)
        filter_layout.addWidget(QLabel(t("supervised_level")), 0, 2)
        self.cbo_level = QComboBox()
        self.cbo_level.currentIndexChanged.connect(self._filter_changed)
        filter_layout.addWidget(self.cbo_level, 0, 3)
        filter_layout.addWidget(QLabel(t("supervised_decision")), 1, 0)
        self.cbo_decision = QComboBox()
        self.cbo_decision.currentIndexChanged.connect(self._decision_changed)
        filter_layout.addWidget(self.cbo_decision, 1, 1)
        filter_layout.addWidget(QLabel(t("supervised_quantity")), 2, 0)
        self.spin_quantity = QSpinBox()
        self.spin_quantity.setRange(0, 0)
        self.spin_quantity.valueChanged.connect(self._quantity_changed)
        filter_layout.addWidget(self.spin_quantity, 2, 1)
        self.lbl_recommended = QLabel(t("supervised_recommended_empty"))
        self.lbl_recommended.setWordWrap(True)
        filter_layout.addWidget(self.lbl_recommended, 2, 2, 1, 2)
        layout.addWidget(filter_group)

        self.lbl_topic_catalog = QLabel(t("supervised_topic_catalog_pending"))
        self.lbl_topic_catalog.setWordWrap(True)
        self.lbl_topic_catalog.setStyleSheet(
            "background:#eef9f4;border:1px solid #73b99a;border-radius:8px;"
            "padding:8px;color:#245442;"
        )
        layout.addWidget(self.lbl_topic_catalog)

        self.lbl_inventory = QLabel(t("supervised_inventory_empty"))
        self.lbl_inventory.setWordWrap(True)
        self.lbl_inventory.setStyleSheet(
            "background:#edf6ff;border:1px solid #7db7e8;border-radius:8px;"
            "padding:9px;color:#24445f;"
        )
        layout.addWidget(self.lbl_inventory)

        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setMaximumHeight(115)
        self.txt_preview.setPlaceholderText(t("supervised_preview_empty"))
        layout.addWidget(self.txt_preview)

        settings_group = QGroupBox(t("supervised_settings_group"))
        settings_layout = QHBoxLayout(settings_group)
        settings_layout.addWidget(QLabel(t("batch_instruction_label")))
        self.txt_instruction = QTextEdit()
        self.txt_instruction.setPlaceholderText(t("batch_instruction_placeholder"))
        self.txt_instruction.setMaximumHeight(45)
        settings_layout.addWidget(self.txt_instruction, 1)
        self.chk_turbo_scan = QCheckBox(t("supervised_turbo_scan"))
        self.chk_turbo_scan.setChecked(True)
        self.chk_turbo_scan.setToolTip(t("supervised_turbo_scan_tip"))
        settings_layout.addWidget(self.chk_turbo_scan)
        if self._is_openrouter:
            self.chk_slow_mode = QCheckBox(t("batch_chk_slow_mode"))
            self.chk_slow_mode.setChecked(True)
            self.chk_slow_mode.setToolTip(t("batch_chk_slow_mode_tip"))
            self.chk_slow_mode.toggled.connect(self._quantity_changed)
            settings_layout.addWidget(self.chk_slow_mode)
        layout.addWidget(settings_group)

        self.lbl_estimate = QLabel(t("supervised_estimate_empty"))
        self.lbl_estimate.setWordWrap(True)
        self.lbl_estimate.setStyleSheet(
            "background:#fef9e7;border:1px solid #f39c12;border-radius:8px;"
            "padding:9px;color:#7d6608;"
        )
        layout.addWidget(self.lbl_estimate)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("color:#555;font-size:11px;padding:4px;")
        layout.addWidget(self.lbl_status)

        buttons = QHBoxLayout()
        self.btn_close = QPushButton(t("btn_close"))
        self.btn_close.clicked.connect(self.reject)
        buttons.addWidget(self.btn_close)
        buttons.addStretch(1)
        self.btn_stop = QPushButton(t("btn_stop"))
        self.btn_stop.clicked.connect(self._stop_processing)
        self.btn_stop.setVisible(False)
        buttons.addWidget(self.btn_stop)
        self.btn_use_results = QPushButton(t("supervised_use_results", count=0))
        self.btn_use_results.clicked.connect(self._accept_results)
        self.btn_use_results.setVisible(False)
        buttons.addWidget(self.btn_use_results)
        self.btn_process = QPushButton(t("supervised_produce"))
        self.btn_process.clicked.connect(self._start_processing)
        self.btn_process.setEnabled(False)
        buttons.addWidget(self.btn_process)
        layout.addLayout(buttons)

    def _source_edited(self):
        self._inventory_source = None
        self._clear_inventory()

    def _clear_inventory(self):
        self._inventory = []
        self._scan_rows = []
        self._scan_counts = {}
        self._topic_catalog = []
        self._topic_catalog_ready = False
        self._source_id = ""
        self._persisted_completed_ids.clear()
        self._existing_completed_ids.clear()
        self._session_completed_ids.clear()
        self.result_vocab = []
        self.btn_use_results.setVisible(False)
        self.btn_scan_details.setEnabled(False)
        self._refresh_topic_catalog_label()
        self._populate_filters()
        self._update_selection(reset_quantity=True)

    def _take_workshop_source(self):
        if not self._workshop_text.strip() and not self._workshop_paths:
            tooltip(t("supervised_workshop_empty"))
            return
        try:
            source = inventory_source_from_files(
                self._workshop_paths,
                text=self._workshop_text,
                name="Forge Workshop",
            )
        except Exception as error:
            self.lbl_status.setText(t("supervised_file_error", error=str(error)))
            return
        self.txt_input.blockSignals(True)
        self.txt_input.setPlainText(self._source_preview(source))
        self.txt_input.blockSignals(False)
        self._inventory_source = source
        self._clear_inventory()
        self._analyze_inventory()

    @staticmethod
    def _source_preview(source):
        lines = []
        for row in source.get("rows", ()):
            cells = row.get("cells")
            if isinstance(cells, list):
                lines.append("\t".join(str(cell) for cell in cells))
            else:
                lines.append(str(row.get("text") or ""))
        return "\n".join(lines)

    def _open_source_file(self):
        filepath, _selected_filter = QFileDialog.getOpenFileName(
            self,
            t("supervised_open_file_title"),
            "",
            t("supervised_open_file_filter"),
        )
        if not filepath:
            return
        try:
            source = inventory_source_from_file(filepath)
        except Exception as error:
            self.lbl_status.setText(t("supervised_file_error", error=str(error)))
            return
        if not source.get("rows"):
            self.lbl_status.setText(t("supervised_no_source_rows"))
            return
        self.txt_input.blockSignals(True)
        self.txt_input.setPlainText(self._source_preview(source))
        self.txt_input.blockSignals(False)
        self._inventory_source = source
        self._clear_inventory()
        self.lbl_status.setText(t(
            "supervised_file_loaded",
            name=source.get("name", ""),
            count=len(source.get("rows", ())),
        ))
        self._analyze_inventory()

    def _analyze_inventory(self):
        if self._scan_thread is not None:
            return
        source = self._inventory_source
        if source is None:
            raw_text = self.txt_input.toPlainText().strip()
            if raw_text:
                source = inventory_source_from_text(raw_text)
                self._inventory_source = source
        if not source or not source.get("rows"):
            tooltip(t("supervised_source_required"))
            return
        from workers.batch_workers import InventoryScanThread

        self._clear_inventory()
        self._inventory_source = source
        self._scan_thread = InventoryScanThread(
            source=source,
            lang=self.lang,
            custom_instruction=self.txt_instruction.toPlainText().strip(),
            grammar=self.grammar,
            turbo=self.chk_turbo_scan.isChecked(),
        )
        self._scan_thread.progress.connect(self._on_progress)
        self._scan_thread.finished.connect(self._on_scan_finished)
        self._scan_thread.error.connect(self._on_scan_error)
        self._set_scanning(True)
        self._scan_thread.start()

    def _on_scan_finished(self, result):
        inventory = list(result.get("inventory", ()))
        self._scan_rows = list(result.get("rows", ()))
        self._scan_counts = dict(result.get("counts", {}))
        self._topic_catalog = list(result.get("topic_catalog", ()))
        self._topic_catalog_ready = True
        self._source_id = str(result.get("source_hash") or "")
        self._set_scanning(False)
        if not inventory:
            self.lbl_status.setText(t("supervised_no_inventory"))
            self.btn_scan_details.setEnabled(bool(self._scan_rows))
            self._refresh_topic_catalog_label()
            return
        self._inventory = inventory
        self._persisted_completed_ids = load_supervised_progress(self._source_id)
        self._existing_completed_ids = supervised_existing_ids(
            inventory, self.existing_words, grammar=self.grammar,
        )
        self._session_completed_ids.clear()
        self.result_vocab = []
        self.btn_use_results.setVisible(False)
        self.btn_scan_details.setEnabled(bool(self._scan_rows))
        self._refresh_topic_catalog_label()
        self._populate_filters()
        self._update_selection(reset_quantity=True)
        status_key = (
            "supervised_analyzed_local"
            if result.get("scan_mode") == "structured_local"
            else "supervised_analyzed_ai"
        )
        status = t(
            status_key,
            count=len(inventory),
            keep=self._scan_counts.get("keep", 0),
            skip=self._scan_counts.get("skip", 0),
            review=self._scan_counts.get("review", 0),
        )
        token_info = dict(result.get("token_info", {}))
        if token_info.get("requests"):
            status += " " + t(
                "supervised_scan_usage",
                requests=int(token_info.get("requests", 0)),
                input_tokens=int(token_info.get("prompt_tokens", 0)),
                output_tokens=int(token_info.get("completion_tokens", 0)),
                cost=float(token_info.get("total_cost", 0.0)),
            )
        self.lbl_status.setText(status)

    def _on_scan_error(self, error_message):
        self._set_scanning(False)
        self.lbl_status.setText(t("batch_status_error", error=error_message))

    def _show_scan_details(self):
        rows = [
            (index, row) for index, row in enumerate(self._scan_rows)
            if row.get("decision") in {"skip", "review"}
        ]
        if not rows:
            tooltip(t("supervised_no_scan_details"))
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(t("supervised_scan_details_title"))
        dialog.resize(800, 560)
        layout = QVBoxLayout(dialog)
        detail = QListWidget()
        detail.setWordWrap(True)
        for row_index, row in rows:
            item = QListWidgetItem(t(
                "supervised_scan_detail_row",
                decision=t(f"supervised_decision_{row.get('decision', 'review')}"),
                source_id=row.get("source_id", ""),
                surface=row.get("surface") or t("supervised_none"),
                reason=row.get("reason") or t("supervised_none"),
                source=row.get("source_text", ""),
            ))
            item.setData(Qt.ItemDataRole.UserRole, row_index)
            if row.get("decision") == "skip" and row.get("surface"):
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
            detail.addItem(item)
        layout.addWidget(detail)
        actions = QHBoxLayout()
        restore = QPushButton(t("supervised_restore_selected"))
        restore.clicked.connect(lambda: self._restore_scan_rows(detail, dialog))
        actions.addWidget(restore)
        actions.addStretch(1)
        close = QPushButton(t("btn_close"))
        close.clicked.connect(dialog.accept)
        actions.addWidget(close)
        layout.addLayout(actions)
        dialog.exec()

    def _restore_scan_rows(self, detail, dialog):
        restored = 0
        for row_number in range(detail.count()):
            item = detail.item(row_number)
            if item.checkState() != Qt.CheckState.Checked:
                continue
            scan_index = item.data(Qt.ItemDataRole.UserRole)
            if not isinstance(scan_index, int) or not (0 <= scan_index < len(self._scan_rows)):
                continue
            row = self._scan_rows[scan_index]
            if row.get("decision") != "skip" or not row.get("surface"):
                continue
            row["decision"] = "review"
            row["reason"] = t("supervised_restored_reason")
            restored += 1
        if not restored:
            tooltip(t("supervised_restore_empty"))
            return
        self._scan_counts["skip"] = max(
            0, int(self._scan_counts.get("skip", 0)) - restored,
        )
        self._scan_counts["review"] = int(
            self._scan_counts.get("review", 0)
        ) + restored
        self._inventory = inventory_from_scan_rows(
            self._scan_rows,
            self._source_id,
            self.lang,
            grammar=self.grammar,
        )
        self._scan_rows, self._topic_catalog = canonicalize_topics(self._scan_rows)
        self._topic_catalog_ready = True
        self._refresh_topic_catalog_label()
        self._existing_completed_ids = supervised_existing_ids(
            self._inventory, self.existing_words, grammar=self.grammar,
        )
        self._populate_filters()
        self._update_selection(reset_quantity=True)
        self.lbl_status.setText(t("supervised_restored", count=restored))
        dialog.accept()

    def _refresh_topic_catalog_label(self):
        if not self._topic_catalog_ready:
            self.lbl_topic_catalog.setText(t("supervised_topic_catalog_pending"))
            return
        preview = " · ".join(
            f"{topic.get('name', '')} ({int(topic.get('count', 0))})"
            for topic in self._topic_catalog[:12]
        )
        more = max(0, len(self._topic_catalog) - 12)
        self.lbl_topic_catalog.setText(t(
            "supervised_topic_catalog_ready",
            topics=len(self._topic_catalog),
            preview=preview or t("supervised_unclassified"),
            more=(t("supervised_topic_catalog_more", count=more) if more else ""),
        ))

    def _completed_ids(self):
        return (
            self._persisted_completed_ids
            | self._existing_completed_ids
            | self._session_completed_ids
        )

    def _populate_filters(self):
        current_topic = self.cbo_topic.currentData() if self.cbo_topic.count() else ""
        current_level = self.cbo_level.currentData() if self.cbo_level.count() else ""
        current_decision = (
            self.cbo_decision.currentData() if self.cbo_decision.count() else "keep"
        )
        completed = self._completed_ids()
        remaining_items = filter_supervised_inventory(
            self._inventory, completed_ids=completed,
        )
        if current_decision:
            remaining_items = [
                item for item in remaining_items
                if item.get("decision") == current_decision
            ]
        remaining_total = len(remaining_items)
        self._refreshing = True
        try:
            self.cbo_topic.clear()
            self.cbo_level.clear()
            self.cbo_decision.clear()
            self.cbo_topic.addItem(
                f"{t('supervised_all_topics')} ({remaining_total})", "",
            )
            self.cbo_level.addItem(
                f"{t('supervised_all_levels')} ({remaining_total})", "",
            )
            keep_count = sum(
                1 for item in self._inventory
                if item.get("decision") == "keep" and item.get("id") not in completed
            )
            review_count = sum(
                1 for item in self._inventory
                if item.get("decision") == "review" and item.get("id") not in completed
            )
            self.cbo_decision.addItem(
                f"{t('supervised_decision_keep')} ({keep_count})", "keep",
            )
            self.cbo_decision.addItem(
                f"{t('supervised_decision_review')} ({review_count})", "review",
            )
            self.cbo_decision.addItem(
                f"{t('supervised_decision_actionable')} ({keep_count + review_count})", "",
            )
            topics = sorted({str(item.get("topic") or "").strip() for item in self._inventory})
            levels = sorted({str(item.get("level") or "").strip() for item in self._inventory})
            for topic in topics:
                data = topic or _UNCLASSIFIED
                matching = filter_supervised_inventory(
                    self._inventory, topic=data, completed_ids=completed,
                )
                if current_decision:
                    matching = [
                        item for item in matching
                        if item.get("decision") == current_decision
                    ]
                count = len(matching)
                self.cbo_topic.addItem(
                    f"{topic or t('supervised_unclassified')} ({count})",
                    data,
                )
            for level in levels:
                data = level or _UNCLASSIFIED
                matching = filter_supervised_inventory(
                    self._inventory, level=data, completed_ids=completed,
                )
                if current_decision:
                    matching = [
                        item for item in matching
                        if item.get("decision") == current_decision
                    ]
                count = len(matching)
                self.cbo_level.addItem(
                    f"{level or t('supervised_unclassified')} ({count})",
                    data,
                )
            topic_index = self.cbo_topic.findData(current_topic)
            level_index = self.cbo_level.findData(current_level)
            decision_index = self.cbo_decision.findData(current_decision)
            self.cbo_topic.setCurrentIndex(max(0, topic_index))
            self.cbo_level.setCurrentIndex(max(0, level_index))
            self.cbo_decision.setCurrentIndex(max(0, decision_index))
        finally:
            self._refreshing = False

    def _filter_changed(self):
        if not self._refreshing:
            self._update_selection(reset_quantity=True)

    def _decision_changed(self):
        if not self._refreshing:
            self._populate_filters()
            self._update_selection(reset_quantity=True)

    def _filtered_items(self):
        topic = self.cbo_topic.currentData() or ""
        level = self.cbo_level.currentData() or ""
        decision = self.cbo_decision.currentData()
        items = filter_supervised_inventory(
            self._inventory,
            topic=topic,
            level=level,
            completed_ids=self._completed_ids(),
        )
        if decision:
            items = [item for item in items if item.get("decision") == decision]
        return items

    def _update_selection(self, *, reset_quantity=False):
        available = self._filtered_items() if self._inventory else []
        total = len(self._inventory)
        completed = len({item["id"] for item in self._inventory} & self._completed_ids())
        remaining = max(0, total - completed)
        selected_remaining = len(available)
        unknown_topics = sum(1 for item in self._inventory if not item.get("topic"))
        unknown_levels = sum(1 for item in self._inventory if not item.get("level"))
        self.lbl_inventory.setText(t(
            "supervised_inventory_summary_ai" if self._scan_counts else "supervised_inventory_summary",
            total=total,
            completed=completed,
            remaining=remaining,
            filtered=selected_remaining,
            unknown_topics=unknown_topics,
            unknown_levels=unknown_levels,
            source_rows=self._scan_counts.get("source_rows", 0),
            keep=self._scan_counts.get("keep", 0),
            skip=self._scan_counts.get("skip", 0),
            review=self._scan_counts.get("review", 0),
        ))

        recommended = recommended_supervised_run_size(
            selected_remaining,
            self.lang,
            grammar=self.grammar,
            max_output_tokens=get_api_config().get("max_tokens", 8192),
        )
        self.spin_quantity.blockSignals(True)
        self.spin_quantity.setRange(0 if not selected_remaining else 1, selected_remaining)
        if reset_quantity or self.spin_quantity.value() > selected_remaining:
            self.spin_quantity.setValue(recommended)
        self.spin_quantity.blockSignals(False)
        self.lbl_recommended.setText(t(
            "supervised_recommended",
            count=recommended,
            api_size=recommended_quality_v2_batch_size(
                self.lang,
                grammar=self.grammar,
                max_output_tokens=get_api_config().get("max_tokens", 8192),
            ),
        ) if recommended else t("supervised_recommended_empty"))
        self.btn_process.setEnabled(
            self._topic_catalog_ready
            and bool(available)
            and self._batch_thread is None
            and self._scan_thread is None
        )
        self._quantity_changed()

    def _quantity_changed(self):
        available = self._filtered_items() if self._inventory else []
        count = min(len(available), self.spin_quantity.value())
        selected = available[:count]
        preview_lines = []
        for item in selected[:12]:
            metadata = " · ".join((
                str(item.get("topic") or t("supervised_unclassified")),
                str(item.get("level") or t("supervised_unclassified")),
            ))
            preview_lines.append(f"• {item['front']} — {metadata}")
        if len(selected) > 12:
            preview_lines.append(t("supervised_preview_more", count=len(selected) - 12))
        self.txt_preview.setPlainText("\n".join(preview_lines))

        if not count:
            self.lbl_estimate.setText(t("supervised_estimate_empty"))
            return
        request_size = recommended_quality_v2_batch_size(
            self.lang,
            grammar=self.grammar,
            max_output_tokens=get_api_config().get("max_tokens", 8192),
        )
        estimate = estimate_batch_cost(
            count, self.lang, request_size, grammar=self.grammar,
        )
        seconds = estimate["estimated_time_seconds"]
        if self._is_openrouter and self.chk_slow_mode.isChecked():
            seconds = int(estimate["estimated_batches"] * 10.2)
        self.lbl_estimate.setText(t(
            "supervised_estimate",
            count=count,
            batches=estimate["estimated_batches"],
            cost=estimate["estimated_cost_usd"],
            seconds=seconds,
        ))

    def _start_processing(self):
        if not self._inventory:
            self._analyze_inventory()
            if not self._inventory:
                return
        available = self._filtered_items()
        count = min(len(available), self.spin_quantity.value())
        if count <= 0:
            tooltip(t("supervised_nothing_selected"))
            return
        self._active_items = available[:count]
        raw_text = json.dumps(
            [
                {
                    "front": item["front"],
                    "meaning": item.get("meaning", ""),
                    "level": item.get("level", ""),
                    "topic": item.get("topic", ""),
                }
                for item in self._active_items
            ],
            ensure_ascii=False,
        )
        from workers.batch_workers import BatchProcessThread

        self.slow_mode = bool(
            self._is_openrouter and self.chk_slow_mode.isChecked()
        )
        self._batch_thread = BatchProcessThread(
            raw_text=raw_text,
            lang=self.lang,
            custom_instruction=self.txt_instruction.toPlainText().strip(),
            existing_words=self.existing_words,
            batch_size=recommended_quality_v2_batch_size(
                self.lang,
                grammar=self.grammar,
                max_output_tokens=get_api_config().get("max_tokens", 8192),
            ),
            grammar=self.grammar,
            slow_mode=self.slow_mode,
        )
        self._batch_thread.progress.connect(self._on_progress)
        self._batch_thread.finished.connect(self._on_batch_finished)
        self._batch_thread.error.connect(self._on_error)
        self._set_processing(True)
        self._batch_thread.start()

    def _on_progress(self, message):
        self.lbl_status.setText(message)
        QApplication.processEvents()

    def _on_batch_finished(self, vocab_list):
        report = dict(getattr(self._batch_thread, "last_report", {}) or {})
        vocab_list = apply_supervised_metadata(
            vocab_list, self._active_items, self.lang, grammar=self.grammar,
        )
        produced_ids = supervised_result_ids(
            self._active_items, vocab_list, grammar=self.grammar,
        )
        self._session_completed_ids.update(produced_ids)
        for item in vocab_list:
            if item not in self.result_vocab:
                self.result_vocab.append(item)
        self._last_report = {
            "requested": self._last_report.get("requested", 0) + report.get("requested", 0),
            "valid": len(self.result_vocab),
            "missing": self._last_report.get("missing", 0) + report.get("missing", 0),
            "retries": self._last_report.get("retries", 0) + report.get("retries", 0),
            "complete": not report.get("missing"),
        }
        self._set_processing(False)
        self.btn_use_results.setText(t("supervised_use_results", count=len(self.result_vocab)))
        self.btn_use_results.setVisible(bool(self.result_vocab))
        self._populate_filters()
        self._update_selection(reset_quantity=True)
        self.lbl_status.setText(t(
            "supervised_run_done",
            produced=len(produced_ids),
            remaining=len(self._filtered_items()),
        ))

    def _on_error(self, error_message):
        self._set_processing(False)
        self.lbl_status.setText(t("batch_status_error", error=error_message))

    def _set_processing(self, running):
        self.txt_input.setEnabled(not running)
        self.btn_take_workshop.setEnabled(not running and bool(
            self._workshop_text.strip() or self._workshop_paths
        ))
        self.btn_open_file.setEnabled(not running)
        self.btn_analyze.setEnabled(not running)
        self.btn_scan_details.setEnabled(not running and bool(self._scan_rows))
        self.cbo_topic.setEnabled(not running)
        self.cbo_level.setEnabled(not running)
        self.cbo_decision.setEnabled(not running)
        self.spin_quantity.setEnabled(not running)
        self.txt_instruction.setEnabled(not running)
        self.chk_turbo_scan.setEnabled(not running)
        if self._is_openrouter:
            self.chk_slow_mode.setEnabled(not running)
        self.btn_process.setVisible(not running)
        self.btn_stop.setVisible(running)
        self.btn_close.setEnabled(not running)
        self.progress_bar.setVisible(running)
        if running:
            self.progress_bar.setRange(0, 0)
            self.btn_process.setEnabled(False)
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self._batch_thread = None

    def _set_scanning(self, running):
        self.txt_input.setEnabled(not running)
        self.btn_take_workshop.setEnabled(not running and bool(
            self._workshop_text.strip() or self._workshop_paths
        ))
        self.btn_open_file.setEnabled(not running)
        self.btn_analyze.setEnabled(not running)
        self.btn_scan_details.setEnabled(not running and bool(self._scan_rows))
        self.cbo_topic.setEnabled(not running)
        self.cbo_level.setEnabled(not running)
        self.cbo_decision.setEnabled(not running)
        self.spin_quantity.setEnabled(not running)
        self.txt_instruction.setEnabled(not running)
        self.chk_turbo_scan.setEnabled(not running)
        if self._is_openrouter:
            self.chk_slow_mode.setEnabled(not running)
        self.btn_process.setVisible(not running)
        self.btn_stop.setVisible(running)
        self.btn_close.setEnabled(not running)
        self.progress_bar.setVisible(running)
        if running:
            self.progress_bar.setRange(0, 0)
            self.btn_process.setEnabled(False)
            self.lbl_status.setText(t("inventory_ai_starting"))
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self._scan_thread = None

    def _stop_processing(self):
        scan_worker = self._scan_thread
        if scan_worker and scan_worker.isRunning():
            scan_worker.stop()
            self._set_scanning(False)
            if scan_worker.isRunning():
                self._scan_thread = scan_worker
                self.btn_process.setEnabled(False)
                QTimer.singleShot(100, self._release_stopped_thread)
            self.lbl_status.setText(t("batch_status_stopped"))
            return
        worker = self._batch_thread
        if worker and worker.isRunning():
            worker.stop()
        self._set_processing(False)
        if worker and worker.isRunning():
            self._batch_thread = worker
            self.btn_process.setEnabled(False)
            QTimer.singleShot(100, self._release_stopped_thread)
        self.lbl_status.setText(t("batch_status_stopped"))

    def _release_stopped_thread(self):
        scan_worker = self._scan_thread
        if scan_worker is not None:
            if scan_worker.isRunning():
                QTimer.singleShot(100, self._release_stopped_thread)
                return
            self._scan_thread = None
            self._update_selection(reset_quantity=False)
            return
        worker = self._batch_thread
        if worker is None:
            return
        if worker.isRunning():
            QTimer.singleShot(100, self._release_stopped_thread)
            return
        self._batch_thread = None
        self._update_selection(reset_quantity=False)

    def _accept_results(self):
        if not self.result_vocab:
            return
        save_supervised_progress(self._source_id, self._session_completed_ids)
        self.accept()

    def get_result_vocab(self):
        return list(self.result_vocab)

    def get_reliability_report(self):
        return dict(self._last_report)
