"""Qt browser for privacy-safe per-request AI usage history."""

from datetime import datetime, timedelta

from aqt.qt import (
    QAbstractItemView, QComboBox, QDate, QDateEdit, QDialog, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout,
)
from aqt.utils import askUser

from utils.ai_usage_history import clear_usage_history, get_usage_entries, summarize_usage
from utils.i18n import t


_OPERATIONS = (
    "vocab_extraction", "grammar_extraction", "ai_chat", "batch_vocabulary",
    "batch_grammar", "deck_organization", "unknown",
)


def _operation_label(operation: str) -> str:
    return t(f"usage_operation_{operation}")


class AiUsageHistoryDialog(QDialog):
    """Filter and inspect individual provider-reported AI requests."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = []
        self.setWindowTitle(t("usage_history_title"))
        self.setMinimumSize(900, 560)
        self.resize(1120, 660)
        self._setup_ui()
        self._reload()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        intro = QLabel(f"<h3>{t('usage_history_header')}</h3><p>{t('usage_history_desc')}</p>")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        filters = QHBoxLayout()
        filters.addWidget(QLabel(t("usage_filter_model")))
        self.cbo_model = QComboBox()
        self.cbo_model.currentIndexChanged.connect(self._rebuild)
        filters.addWidget(self.cbo_model)
        filters.addWidget(QLabel(t("usage_filter_operation")))
        self.cbo_operation = QComboBox()
        self.cbo_operation.addItem(t("usage_filter_all"), "")
        for operation in _OPERATIONS:
            self.cbo_operation.addItem(_operation_label(operation), operation)
        self.cbo_operation.currentIndexChanged.connect(self._rebuild)
        filters.addWidget(self.cbo_operation)
        filters.addWidget(QLabel(t("usage_filter_date")))
        self.cbo_date = QComboBox()
        for key in ("all", "today", "7d", "30d", "custom"):
            self.cbo_date.addItem(t(f"usage_date_{key}"), key)
        self.cbo_date.currentIndexChanged.connect(self._rebuild)
        filters.addWidget(self.cbo_date)
        self.date_from = QDateEdit(QDate.currentDate())
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self._rebuild)
        filters.addWidget(self.date_from)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.dateChanged.connect(self._rebuild)
        filters.addWidget(self.date_to)
        layout.addLayout(filters)

        sort_row = QHBoxLayout()
        sort_row.addWidget(QLabel(t("usage_sort_label")))
        self.cbo_sort = QComboBox()
        for key in ("newest", "oldest", "cost_high", "cost_low", "input_high", "input_low", "output_high", "output_low"):
            self.cbo_sort.addItem(t(f"usage_sort_{key}"), key)
        self.cbo_sort.currentIndexChanged.connect(self._rebuild)
        sort_row.addWidget(self.cbo_sort)
        sort_row.addStretch()
        self.lbl_total = QLabel()
        self.lbl_total.setStyleSheet("font-weight:bold;color:#2980b9;")
        sort_row.addWidget(self.lbl_total)
        layout.addLayout(sort_row)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            t("usage_col_model"), t("usage_col_time"), t("usage_col_duration"),
            t("usage_col_operation"), t("usage_col_input"), t("usage_col_output"),
            t("usage_col_cost"),
        ])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        self.btn_clear = QPushButton(t("usage_clear_history"))
        self.btn_clear.clicked.connect(self._clear)
        actions.addWidget(self.btn_clear)
        actions.addStretch()
        btn_close = QPushButton(t("btn_close"))
        btn_close.clicked.connect(self.accept)
        actions.addWidget(btn_close)
        layout.addLayout(actions)

    def _reload(self):
        self._entries = get_usage_entries()
        current_model = self.cbo_model.currentData()
        self.cbo_model.blockSignals(True)
        self.cbo_model.clear()
        self.cbo_model.addItem(t("usage_filter_all"), "")
        for model in sorted({str(item.get("model", "")) for item in self._entries if item.get("model")}):
            self.cbo_model.addItem(model, model)
        index = self.cbo_model.findData(current_model)
        self.cbo_model.setCurrentIndex(max(0, index))
        self.cbo_model.blockSignals(False)
        self._rebuild()

    def _filtered_entries(self):
        model = self.cbo_model.currentData() or ""
        operation = self.cbo_operation.currentData() or ""
        date_mode = self.cbo_date.currentData() or "all"
        today = datetime.now().date()
        start = None
        end = today
        if date_mode == "today":
            start = today
        elif date_mode == "7d":
            start = today - timedelta(days=6)
        elif date_mode == "30d":
            start = today - timedelta(days=29)
        elif date_mode == "custom":
            start = self.date_from.date().toPyDate()
            end = self.date_to.date().toPyDate()
            if start > end:
                start, end = end, start

        visible = []
        for entry in self._entries:
            if model and entry.get("model") != model:
                continue
            if operation and entry.get("operation") != operation:
                continue
            if start:
                try:
                    entry_date = datetime.fromisoformat(str(entry.get("timestamp", ""))).date()
                except ValueError:
                    continue
                if entry_date < start or entry_date > end:
                    continue
            visible.append(entry)
        return visible

    def _rebuild(self):
        entries = self._filtered_entries()
        key = self.cbo_sort.currentData() or "newest"
        sort_rules = {
            "newest": ("timestamp_unix", True), "oldest": ("timestamp_unix", False),
            "cost_high": ("total_cost", True), "cost_low": ("total_cost", False),
            "input_high": ("prompt_tokens", True), "input_low": ("prompt_tokens", False),
            "output_high": ("completion_tokens", True), "output_low": ("completion_tokens", False),
        }
        field, reverse = sort_rules[key]
        entries.sort(key=lambda entry: float(entry.get(field) or 0), reverse=reverse)

        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            values = (
                str(entry.get("model", "")), str(entry.get("timestamp", "")),
                f"{float(entry.get('duration_seconds') or 0):.2f}s",
                _operation_label(str(entry.get("operation", "unknown"))),
                f"{int(entry.get('prompt_tokens') or 0):,}",
                f"{int(entry.get('completion_tokens') or 0):,}",
                f"${float(entry.get('total_cost') or 0):.8f}",
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

        total = summarize_usage(entries)
        self.lbl_total.setText(t(
            "usage_total",
            calls=total["calls"], input_tokens=total["prompt_tokens"],
            output_tokens=total["completion_tokens"], total_cost=total["total_cost"],
        ))

    def _clear(self):
        if askUser(t("usage_clear_confirm"), parent=self):
            clear_usage_history()
            self._reload()
