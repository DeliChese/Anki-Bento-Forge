"""
AI Preview Dialog — Xem trước, chỉnh sửa, xóa, tái tạo thẻ từ AI extract.
"""

import json

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, Qt,
)
from aqt.utils import showInfo, tooltip

from utils.ai_extractor import extract_vocabulary_with_ai, extract_vocabulary_long_text
from utils.knowledge_extractor import extract_knowledge_long_text, extract_knowledge_with_ai
from utils.knowledge_schema import KnowledgeSchemaError, parse_knowledge_cards
from utils.import_quality import evaluate_card_candidate
from utils.ai_output_validation import validate_ai_cards
from utils.logger import get_logger
from utils.i18n import t

logger = get_logger()


def show_ai_preview_dialog(parent, vocab_list, lang, ai_text_input, ai_instruction,
                           lbl_ai_status, get_existing_words_fn,
                           on_finalize_callback, grammar=False, learning_mode="language"):
    """
    Mở dialog xem trước & chỉnh sửa thẻ sau AI extract (từ vựng HOẶC ngữ pháp).

    Args:
        parent: Parent widget (AnkiSmartFactory)
        vocab_list: Mutable list các dict (từ vựng hoặc ngữ pháp)
        lang: "japanese" hoặc "chinese"
        ai_text_input: QPlainTextEdit chứa text gốc
        ai_instruction: QLineEdit chứa custom instruction
        lbl_ai_status: QLabel hiển thị trạng thái
        get_existing_words_fn: Hàm lấy danh sách từ hiện có
        on_finalize_callback: Callback khi user chấp nhận (nhận final_list)
        grammar: True nếu đang ở chế độ Ngữ pháp
    """
    item_label = (
        t("item_label_knowledge") if learning_mode == "knowledge"
        else (t("item_label_grammar") if grammar else t("item_label_vocab"))
    )
    dlg = QDialog(parent)
    dlg.setWindowTitle(t("dlg_preview_edit", count=len(vocab_list), item=item_label))
    dlg.setMinimumSize(900, 650)
    dlg.resize(1000, 750)
    dlg.setWindowFlags(
        dlg.windowFlags()
        | Qt.WindowType.WindowMinMaxButtonsHint
    )

    vl = QVBoxLayout(dlg)

    # Header
    header = QHBoxLayout()
    header.addWidget(QLabel(
        f"<h3>{t('preview_header_html', count=len(vocab_list), item=item_label)}</h3>"
    ))
    header.addStretch()

    btn_accept_all = QPushButton(t("btn_accept_all"))
    btn_accept_all.setStyleSheet(
        "padding:10px 20px;background:#27ae60;color:white;"
        "font-weight:bold;border-radius:8px;font-size:13px;"
    )
    btn_accept_all.clicked.connect(lambda: (
        _finalize_and_close(
            dlg, table, columns, vocab_list, on_finalize_callback,
            lang=lang, grammar=grammar,
        )
    ))
    header.addWidget(btn_accept_all)
    vl.addLayout(header)

    vl.addWidget(QLabel(t("preview_hint")))

    # Table
    table = QTableWidget()
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
    table.setAlternatingRowColors(True)

    # Xác định cột dựa trên chế độ (ngữ pháp) + ngôn ngữ
    if learning_mode == "knowledge":
        columns = ["type", "question", "answer", "explanation", "source", "tags", "cloze_text"]
    elif grammar:
        if lang == "chinese":
            columns = ["pattern", "pinyin", "meaning", "hsk_level", "topic", "usage",
                       "explanation", "example", "example_pinyin", "example_vn",
                       "example_2", "example_2_pinyin", "example_2_vn",
                       "example_3", "example_3_pinyin", "example_3_vn",
                       "example_4", "example_4_pinyin", "example_4_vn"]
        elif lang == "korean":
            columns = ["pattern", "romanization", "meaning", "topik_level", "topic", "usage",
                       "explanation", "example", "example_romanization", "example_vn",
                       "example_2", "example_2_romanization", "example_2_vn",
                       "example_3", "example_3_romanization", "example_3_vn",
                       "example_4", "example_4_romanization", "example_4_vn"]
        elif lang == "english":
            columns = ["pattern", "pronunciation", "meaning", "cefr_level", "topic", "usage",
                       "explanation", "example", "example_vn", "example_2", "example_2_vn",
                       "example_3", "example_3_vn", "example_4", "example_4_vn"]
        else:
            columns = ["pattern", "reading", "meaning", "jlptlevel", "topic", "usage",
                       "explanation", "example", "example_vn", "example_2", "example_2_vn",
                       "example_3", "example_3_vn", "example_4", "example_4_vn"]
    elif lang == "chinese":
        columns = ["simplified", "traditional", "pinyin", "meaning",
                   "usage_pattern", "usage_note", "collocation", "sino_vietnamese",
                   "hsk_level", "topic", "example", "example_pinyin", "example_vn",
                   "example_2", "example_2_pinyin", "example_2_vn",
                   "example_3", "example_3_pinyin", "example_3_vn",
                   "example_4", "example_4_pinyin", "example_4_vn"]
    elif lang == "korean":
        columns = ["front", "romanization", "meaning",
                   "usage_pattern", "usage_note", "collocation", "sino_vietnamese",
                   "topik_level", "topic", "example", "example_romanization", "example_vn",
                   "example_2", "example_2_romanization", "example_2_vn",
                   "example_3", "example_3_romanization", "example_3_vn",
                   "example_4", "example_4_romanization", "example_4_vn"]
    elif lang == "english":
        columns = ["front", "pronunciation", "meaning",
                   "usage_pattern", "usage_note", "collocation", "cefr_level", "topic",
                   "example", "example_vn", "example_2", "example_2_vn",
                   "example_3", "example_3_vn", "example_4", "example_4_vn"]
    else:
        columns = ["front", "furigana", "meaning",
                   "usage_pattern", "usage_note", "collocation", "sino-vietnamese",
                   "jlptlevel", "topic", "example", "example_vn", "example_2", "example_2_vn",
                   "example_3", "example_3_vn", "example_4", "example_4_vn"]

    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.horizontalHeader().setStretchLastSection(True)

    # Đổ dữ liệu
    table.setRowCount(len(vocab_list))
    for row, item in enumerate(vocab_list):
        for col, key in enumerate(columns):
            value = item.get(key, "")
            val = ", ".join(value) if key == "tags" and isinstance(value, list) else str(value)
            table_item = QTableWidgetItem(val)
            table_item.setFlags(table_item.flags() | Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, col, table_item)

    table.resizeColumnsToContents()
    vl.addWidget(table)

    quality_summary = QLabel()
    quality_summary.setWordWrap(True)
    vl.addWidget(quality_summary)
    existing_terms = ()
    if learning_mode == "language" and not grammar:
        try:
            existing_terms = tuple(get_existing_words_fn() or ())
        except Exception as error:
            logger.warning("Could not load same-deck terms for Confusion Guard: %s", error)

    def refresh_quality_summary(*_args):
        current = _get_current_vocab_from_table(table, columns, learning_mode=learning_mode)
        if learning_mode == "knowledge":
            _update_knowledge_validation(quality_summary, current)
        else:
            _update_quality_summary(
                quality_summary, table, current, lang=lang, grammar=grammar,
                existing_terms=existing_terms,
            )

    refresh_quality_summary()
    table.itemChanged.connect(refresh_quality_summary)
    table.model().rowsRemoved.connect(refresh_quality_summary)
    table.model().modelReset.connect(refresh_quality_summary)

    # Action buttons
    action_bar = QHBoxLayout()

    btn_select_all = QPushButton(t("btn_select_all_check"))
    btn_select_all.clicked.connect(lambda: table.selectAll())
    action_bar.addWidget(btn_select_all)

    btn_edit_selected = QPushButton(t("btn_edit_selected"))
    btn_edit_selected.setStyleSheet("padding:6px 12px;background:#3498db;color:white;font-weight:bold;border-radius:6px;")
    btn_edit_selected.clicked.connect(lambda: _edit_selected_card(table, columns, vocab_list))
    action_bar.addWidget(btn_edit_selected)

    btn_delete = QPushButton(t("btn_delete_selected"))
    btn_delete.setStyleSheet("padding:6px 12px;background:#e74c3c;color:white;font-weight:bold;border-radius:6px;")
    btn_delete.clicked.connect(lambda: _delete_selected(table, vocab_list, dlg))
    action_bar.addWidget(btn_delete)

    btn_regenerate = QPushButton(t("btn_regenerate"))
    btn_regenerate.setStyleSheet("padding:6px 12px;background:#e67e22;color:white;font-weight:bold;border-radius:6px;")
    btn_regenerate.clicked.connect(lambda: _regenerate_selected(
        table, columns, vocab_list, lang, ai_text_input, ai_instruction,
        get_existing_words_fn, lbl_ai_status, parent, grammar, learning_mode
    ))
    action_bar.addWidget(btn_regenerate)

    btn_regenerate_all = QPushButton(t("btn_regenerate_all"))
    btn_regenerate_all.setStyleSheet("padding:6px 12px;background:#8e44ad;color:white;font-weight:bold;border-radius:6px;")
    btn_regenerate_all.clicked.connect(lambda: _regenerate_all(
        table, columns, vocab_list, lang, ai_text_input, ai_instruction,
        get_existing_words_fn, lbl_ai_status, parent, dlg, grammar, learning_mode
    ))
    action_bar.addWidget(btn_regenerate_all)

    action_bar.addStretch()
    vl.addLayout(action_bar)

    # Bottom buttons
    bottom_bar = QHBoxLayout()

    btn_cancel = QPushButton(t("btn_cancel_modal"))
    btn_cancel.setStyleSheet("padding:10px 20px;background:#95a5a6;color:white;font-weight:bold;border-radius:8px;")
    btn_cancel.clicked.connect(dlg.reject)
    bottom_bar.addWidget(btn_cancel)

    bottom_bar.addStretch()

    btn_accept = QPushButton(t("btn_accept_pour"))
    btn_accept.setStyleSheet(
        "padding:12px 30px;background:#27ae60;color:white;"
        "font-weight:bold;border-radius:10px;font-size:14px;"
    )
    btn_accept.clicked.connect(lambda: (
        _finalize_and_close(
            dlg, table, columns, vocab_list, on_finalize_callback,
            lang=lang, grammar=grammar,
        )
    ))
    bottom_bar.addWidget(btn_accept)

    vl.addLayout(bottom_bar)
    dlg.exec()


# ═══════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════

def _get_current_vocab_from_table(table, columns, learning_mode="language"):
    """Đọc dữ liệu hiện tại từ bảng preview."""
    result = []
    for row in range(table.rowCount()):
        item_data = {}
        for col, key in enumerate(columns):
            table_item = table.item(row, col)
            val = table_item.text().strip() if table_item else ""
            item_data[key] = (
                [tag.strip() for tag in val.split(",") if tag.strip()]
                if learning_mode == "knowledge" and key == "tags" else val
            )
        # Ngữ pháp lọc theo pattern; từ vựng lọc theo front/simplified
        result.append(item_data)
    return result


def _update_knowledge_validation(label, cards):
    try:
        parse_knowledge_cards(json.dumps(cards, ensure_ascii=False))
    except KnowledgeSchemaError as error:
        label.setText(t("knowledge_schema_error", error=error))
        label.setStyleSheet(
            "background:#f8d7da;border:1px solid #dc3545;border-radius:6px;"
            "padding:7px;color:#721c24;"
        )
    else:
        label.setText(t("knowledge_preview_valid", count=len(cards)))
        label.setStyleSheet(
            "background:#d4edda;border:1px solid #28a745;border-radius:6px;"
            "padding:7px;color:#155724;"
        )


def _update_quality_summary(
    label, table, vocab_list, *, lang, grammar, existing_terms=(),
):
    """Show deterministic, advisory quality feedback without blocking import."""
    results = [
        evaluate_card_candidate(
            item, lang=lang, grammar=grammar, existing_terms=existing_terms,
        )
        for item in vocab_list
    ]
    _set_quality_tooltips(table, results)
    if not results:
        label.clear()
        return

    average = round(sum(result["score"] for result in results) / len(results))
    flagged = [result for result in results if result["has_warnings"]]
    if flagged:
        issues = sum(len(result["issues"]) for result in flagged)
        label.setText(t(
            "preview_quality_warning",
            flagged=len(flagged), total=len(results), issues=issues, score=average,
        ))
        label.setStyleSheet(
            "background:#fef3cd;border:1px solid #d39e00;border-radius:6px;"
            "padding:7px;color:#6c5100;"
        )
    else:
        label.setText(t("preview_quality_complete", total=len(results), score=average))
        label.setStyleSheet(
            "background:#d4edda;border:1px solid #28a745;border-radius:6px;"
            "padding:7px;color:#155724;"
        )


def _set_quality_tooltips(table, results):
    """Attach translated, row-level advisory details to editable preview cells."""
    for row, result in enumerate(results):
        messages = []
        for issue in result["issues"]:
            if issue == "confusion_candidate":
                messages.append(t(
                    "preview_quality_issue_confusion_candidate",
                    candidates=", ".join(result.get("confusion_candidates") or ()),
                ))
            else:
                messages.append(t(f"preview_quality_issue_{issue}"))
        issue_text = "\n".join(messages)
        for col in range(table.columnCount()):
            cell = table.item(row, col)
            if cell is not None:
                cell.setToolTip(issue_text)


def _delete_selected(table, vocab_list, dlg):
    """Xóa các thẻ được chọn khỏi bảng."""
    rows = set()
    for item in table.selectedItems():
        rows.add(item.row())

    if not rows:
        tooltip(t("tooltip_select_to_delete"))
        return

    for row in sorted(rows, reverse=True):
        table.removeRow(row)
        if row < len(vocab_list):
            vocab_list.pop(row)

    table.clearSelection()
    dlg.setWindowTitle(t("dlg_preview_edit", count=len(vocab_list), item=t("item_label_vocab")))
    tooltip(t("tooltip_deleted", count=len(rows)))


def _edit_selected_card(table, columns, vocab_list):
    """Mở dialog sửa chi tiết cho thẻ được chọn."""
    selected_rows = set()
    for item in table.selectedItems():
        selected_rows.add(item.row())

    if not selected_rows:
        tooltip(t("tooltip_select_to_edit"))
        return

    row = min(selected_rows)
    edit_dlg = QDialog(table.window())
    edit_dlg.setWindowTitle(t("edit_dlg_title", row=row + 1))
    edit_dlg.setMinimumWidth(600)
    layout = QVBoxLayout(edit_dlg)

    form = QFormLayout()
    editors = {}
    for col, key in enumerate(columns):
        table_item = table.item(row, col)
        val = table_item.text() if table_item else ""
        edit = QLineEdit(val)
        edit.setMinimumHeight(28)
        form.addRow(QLabel(f"<b>{key}:</b>"), edit)
        editors[key] = edit

    layout.addLayout(form)

    btn_bar = QHBoxLayout()
    btn_cancel2 = QPushButton(t("btn_cancel_short"))
    btn_cancel2.clicked.connect(edit_dlg.reject)
    btn_bar.addWidget(btn_cancel2)
    btn_bar.addStretch()
    btn_save = QPushButton(t("btn_save"))
    btn_save.setStyleSheet("padding:8px 20px;background:#27ae60;color:white;font-weight:bold;border-radius:6px;")
    btn_save.clicked.connect(edit_dlg.accept)
    btn_bar.addWidget(btn_save)
    layout.addLayout(btn_bar)

    if edit_dlg.exec() == QDialog.DialogCode.Accepted:
        for col, key in enumerate(columns):
            new_val = editors[key].text().strip()
            table.item(row, col).setText(new_val)
            if row < len(vocab_list):
                vocab_list[row][key] = new_val
        tooltip(t("tooltip_updated_card", row=row + 1))


def _regenerate_selected(table, columns, vocab_list, lang, ai_text_input,
                         ai_instruction, get_existing_words_fn, lbl_ai_status, parent,
                         grammar=False, learning_mode="language"):
    """Tái tạo các thẻ được chọn bằng AI (hỗ trợ cả từ vựng & ngữ pháp)."""
    selected_rows = set()
    for item in table.selectedItems():
        selected_rows.add(item.row())

    if not selected_rows:
        tooltip(t("tooltip_select_to_regen"))
        return

    text = ai_text_input.toPlainText().strip()
    if not text:
        tooltip(t("tooltip_no_source_text"))
        return

    custom_instr = ai_instruction.text().strip()
    if learning_mode == "knowledge":
        regen_instr = t("regen_instr_knowledge")
    elif grammar:
        regen_instr = t("regen_instr_grammar")
    else:
        regen_instr = t("regen_instr_vocab")
    for row in sorted(selected_rows):
        if row < len(vocab_list):
            word = (vocab_list[row].get("pattern")
                    or vocab_list[row].get("question")
                    or vocab_list[row].get("cloze_text")
                    or vocab_list[row].get("front")
                    or vocab_list[row].get("simplified")
                    or f"#{row+1}")
            regen_instr += f"- {word}\n"
    if custom_instr:
        regen_instr = custom_instr + "\n" + regen_instr

    existing_words = get_existing_words_fn()

    try:
        if learning_mode == "knowledge":
            vocab_list_new = extract_knowledge_with_ai(
                text, regen_instr,
                existing_keys=existing_words,
                progress_callback=lambda m: lbl_ai_status.setText(m),
                force_refresh=True,
            )
        elif grammar:
            from utils.ai_extractor import extract_grammar_with_ai
            vocab_list_new = extract_grammar_with_ai(
                text, lang, regen_instr,
                existing_patterns=existing_words,
                progress_callback=lambda m: lbl_ai_status.setText(m),
                force_refresh=True,
            )
        else:
            vocab_list_new = extract_vocabulary_with_ai(
                text, lang, regen_instr,
                existing_words=existing_words,
                progress_callback=lambda m: lbl_ai_status.setText(m),
                force_refresh=True,
            )

        if vocab_list_new:
            new_idx = 0
            for row in sorted(selected_rows):
                if new_idx < len(vocab_list_new):
                    if row < len(vocab_list):
                        vocab_list[row] = vocab_list_new[new_idx]
                    if row < table.rowCount():
                        for col, key in enumerate(columns):
                            value = vocab_list_new[new_idx].get(key, "")
                            val = ", ".join(value) if key == "tags" and isinstance(value, list) else str(value)
                            table_item = table.item(row, col)
                            if table_item:
                                table_item.setText(val)
                    new_idx += 1

            lbl_ai_status.setText(t("status_regen_done", count=len(selected_rows)))
            lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")
            tooltip(t("tooltip_regen_done", count=new_idx))
        else:
            tooltip(t("tooltip_regen_fail"))
    except Exception as e:
        tooltip(t("tooltip_regen_error", error=e))


def _regenerate_all(table, columns, vocab_list, lang, ai_text_input,
                    ai_instruction, get_existing_words_fn, lbl_ai_status, parent, dlg,
                    grammar=False, learning_mode="language"):
    """Tái tạo toàn bộ từ đầu (hỗ trợ cả từ vựng & ngữ pháp)."""
    from aqt.qt import QMessageBox
    item_label = (
        t("item_label_knowledge") if learning_mode == "knowledge" else
        (t("item_label_grammar_lower") if grammar else t("item_label_vocab_lower"))
    )
    reply = QMessageBox.question(
        parent,
        t("regen_all_confirm_title"),
        t("regen_all_confirm_msg", item=item_label),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    if reply != QMessageBox.StandardButton.Yes:
        return

    text = ai_text_input.toPlainText().strip()
    if not text:
        tooltip(t("tooltip_no_source_text2"))
        return

    custom_instr = ai_instruction.text().strip()
    existing_words = get_existing_words_fn()

    parent.setEnabled(False)
    from aqt.qt import QApplication
    QApplication.processEvents()

    try:
        if learning_mode == "knowledge":
            vocab_list_new = extract_knowledge_long_text(
                text, custom_instr,
                existing_keys=existing_words,
                progress_callback=lambda m: lbl_ai_status.setText(m),
                force_refresh=True,
            )
        elif grammar:
            from utils.ai_extractor import extract_grammar_long_text
            vocab_list_new = extract_grammar_long_text(
                text, lang, custom_instr,
                existing_patterns=existing_words,
                progress_callback=lambda m: lbl_ai_status.setText(m),
                force_refresh=True,
            )
        else:
            vocab_list_new = extract_vocabulary_long_text(
                text, lang, custom_instr,
                existing_words=existing_words,
                progress_callback=lambda m: lbl_ai_status.setText(m),
                force_refresh=True,
            )

        if vocab_list_new:
            vocab_list.clear()
            vocab_list.extend(vocab_list_new)

            table.setRowCount(len(vocab_list_new))
            for row, item in enumerate(vocab_list_new):
                for col, key in enumerate(columns):
                    value = item.get(key, "")
                    val = ", ".join(value) if key == "tags" and isinstance(value, list) else str(value)
                    table_item = QTableWidgetItem(val)
                    table_item.setFlags(table_item.flags() | Qt.ItemFlag.ItemIsEditable)
                    table.setItem(row, col, table_item)
            table.resizeColumnsToContents()

            dlg.setWindowTitle(t("dlg_preview_edit", count=len(vocab_list_new), item=item_label))
            lbl_ai_status.setText(t("status_regen_all", count=len(vocab_list_new), item=item_label))
            lbl_ai_status.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")
            tooltip(t("tooltip_regen_all", count=len(vocab_list_new), item=item_label))
        else:
            tooltip(t("tooltip_regen_no_result"))
    except Exception as e:
        tooltip(t("tooltip_regen_all_error", error=e))
    finally:
        parent.setEnabled(True)


def _finalize_and_close(
    dlg, table, columns, vocab_list, on_finalize_callback, *, lang, grammar,
):
    """Lấy dữ liệu cuối cùng từ bảng và gọi callback."""
    learning_mode = "knowledge" if "cloze_text" in columns and "question" in columns else "language"
    final_list = _get_current_vocab_from_table(table, columns, learning_mode=learning_mode)

    if learning_mode == "knowledge":
        try:
            final_list = parse_knowledge_cards(json.dumps(final_list, ensure_ascii=False))
        except KnowledgeSchemaError as error:
            showInfo(t("knowledge_schema_error", error=error))
            return
    else:
        validation = validate_ai_cards(
            final_list, lang=lang, kind="grammar" if grammar else "vocab",
            require_example=True,
        )
        if validation.invalid or len(validation.valid_cards) != len(final_list):
            categories = ", ".join(sorted({issue.category for issue in validation.invalid}))
            showInfo(t(
                "factory_validation_blocked",
                count=len(validation.invalid), categories=categories,
            ))
            return
        final_list = [dict(card) for card in validation.valid_cards]

    vocab_list.clear()
    vocab_list.extend(final_list)

    if not final_list:
        msg = (t("tooltip_no_grammar_after") if "pattern" in columns else t("tooltip_no_vocab_after"))
        tooltip(msg)
        return

    on_finalize_callback(final_list)
    dlg.accept()
