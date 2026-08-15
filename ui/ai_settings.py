"""
AI Settings Dialog — Cấu hình API Key, Provider & Model cho AI.

- Dropdown nhà cung cấp (Preset AI): DeepSeek, OpenAI, Google Gemini, Anthropic Claude,
  OpenRouter, Ollama, LM Studio + "Tùy chỉnh".
- Model luôn hiển thị ĐÚNG theo provider được chọn (không trộn chung).
- Hiệu ứng hover: viền phát sáng chạy xung quanh trong 5 giây theo màu đặc trưng
  từng nhà cung cấp (QConicalGradient sweep trên QComboBox).
- Bố cục NGANG 2 cột (Provider/Connection + Generation/Session) — kéo phân cách
  bằng QSplitter, dialog kéo thay đổi kích thước tùy ý.
"""

import json
import socket
import time
import urllib.request
import urllib.error

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QCheckBox, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QGroupBox, QTimer, QWidget, Qt,
)
from aqt.utils import showInfo, tooltip

# QSplitter có thể không có trong aqt.qt của một số version Anki → fallback
# (pattern tương tự ui/theme.py). Test suite mock aqt.qt không export QSplitter,
# PyQt6/PyQt5 cũng không có sẵn → fallback cuối MagicMock (chỉ để import được).
try:
    from aqt.qt import QSplitter
except ImportError:
    try:
        from PyQt6.QtWidgets import QSplitter
    except ImportError:
        try:
            from PyQt5.QtWidgets import QSplitter
        except ImportError:
            from unittest.mock import MagicMock as _QSplitterMock
            QSplitter = _QSplitterMock

# ── Lớp vẽ (painting) — trong RPM thật Anki luôn có; test suite mock `aqt.qt`
#    không export chúng. Khi thiếu → fallback MagicMock (paint chỉ chạy runtime thật).
try:
    from aqt.qt import (
        QPainter, QPainterPath, QConicalGradient,
        QPen, QBrush, QColor, QRectF, QStyledItemDelegate, QStyle,
    )
except ImportError:
    from unittest.mock import MagicMock as _MagicMock
    QPainter = _MagicMock
    QPainterPath = _MagicMock
    QConicalGradient = _MagicMock
    QPen = _MagicMock
    QBrush = _MagicMock
    QColor = _MagicMock
    QRectF = _MagicMock
    QStyledItemDelegate = object
    QStyle = _MagicMock

from utils.ai_extractor import (
    clear_cache,
    clear_import_history,
    get_api_config,
    get_api_key_storage_status,
    save_api_config,
)
from utils.ai_providers import AI_PROVIDERS, detect_provider, get_provider
from utils.i18n import t
from ui.prompt_editor import show_prompt_editor_dialog


# ── Enum cả Qt5 (PyQt5/PySide2) lẫn Qt6 (PyQt6/PySide6) ──────────────
def _qstyle_flag(flag_name, enum_attr="StateFlag"):
    """Lấy cờ QStyle (State_Selected / State_MouseOver) tương thích Qt5/Qt6."""
    enum = getattr(QStyle, enum_attr, None)
    if enum is not None:
        val = getattr(enum, flag_name, None)
        if val is not None:
            return val
    return getattr(QStyle, f"State_{flag_name}", None)


_STATE_SELECTED = _qstyle_flag("Selected")
_STATE_MOUSE_OVER = _qstyle_flag("MouseOver")


class _ProviderItemDelegate(QStyledItemDelegate):
    """Vẽ item provider đẹp: chấm màu đặc trưng + hover/selected sáng."""

    _RADIUS = 10.0
    _CHIP = 18.0

    def paint(self, painter, option, index):
        painter.save()
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            provider = index.data(int(Qt.ItemDataRole.UserRole)) or {}
            color = QColor(provider.get("color", "#8a94a6"))
            rect = QRectF(option.rect).adjusted(3.0, 3.0, -3.0, -3.0)

            selected = bool(option.state & _STATE_SELECTED) if _STATE_SELECTED is not None else False
            hovered = bool(option.state & _STATE_MOUSE_OVER) if _STATE_MOUSE_OVER is not None else False

            path = QPainterPath()
            path.addRoundedRect(rect, self._RADIUS, self._RADIUS)

            # Nền selected / hover
            if selected:
                bg = QColor(color)
                bg.setAlpha(92)
                painter.setPen(QPen(color, 1.5))
                painter.setBrush(bg)
                painter.drawPath(path)
            elif hovered:
                bg = QColor(color)
                bg.setAlpha(38)
                painter.setPen(QPen(color, 1.0))
                painter.setBrush(bg)
                painter.drawPath(path)

            # Chấm tròn màu đặc trưng
            cy = rect.center().y()
            chip_rect = QRectF(rect.left() + 6, cy - self._CHIP / 2, self._CHIP, self._CHIP)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(color))
            painter.drawEllipse(chip_rect)

            # Vẽ chấm nhấp nháy bên trong
            painter.setBrush(QColor(255, 255, 255, 190))
            painter.drawEllipse(
                QRectF(rect.left() + 6 + 5, cy - 4, 8, 8)
            )

            # Tên
            text = index.data(int(Qt.ItemDataRole.DisplayRole)) or ""
            text_rect = QRectF(rect.left() + 34, rect.top(), rect.width() - 40, rect.height())

            if selected:
                text_color = QColor(255, 255, 255)
            else:
                text_color = option.palette.color(option.palette.ColorRole.Text)
            painter.setPen(text_color)
            font = option.font
            if selected:
                font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                text_rect,
                int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                text,
            )
        finally:
            painter.restore()

    def sizeHint(self, option, index):
        base = super().sizeHint(option, index)
        base.setHeight(max(base.height(), 40))
        return base


try:
    class _GlowProviderCombo(QComboBox):
        """QComboBox có viền phát sáng chạy quanh 5 giây theo màu provider."""

        _GLOW_MS = 5000

        def __init__(self, parent=None):
            super().__init__(parent)
            self._glow_running = False
            self._phase = 0.0
            self._stop_at = 0.0
            self._color = "#8A94A6"
            self._timer = None
            self.setMouseTracking(True)

        # ── public ──
        def set_glow_color(self, color):
            self._color = color or "#8d94a6"

        def start_glow(self, ms=None):
            """Bật animation viền chạy quanh (≈60fps) trong *ms*."""
            self._phase = 0.0
            self._glow_running = True
            self._stop_at = time.monotonic() + (ms or self._GLOW_MS) / 1000.0
            if self._timer is None:
                self._timer = QTimer(self)
                self._timer.setInterval(16)
                self._timer.timeout.connect(self._on_tick)
            self._timer.start()
            self.update()

        def glow_color(self):
            return self._color

        # ── events ──
        def enterEvent(self, event):
            self.start_glow()
            super().enterEvent(event)

        def focusInEvent(self, event):
            self.start_glow(self._GLOW_MS // 3)
            super().focusInEvent(event)

        def showPopup(self):
            self.start_glow()
            super().showPopup()
            try:
                view = self.view()
                view.setMouseTracking(True)
                view.setWindowOpacity(1.0)
            except Exception:
                pass

        def hidePopup(self):
            super().hidePopup()

        def _on_tick(self):
            if not self._glow_running:
                self._timer.stop()
                self._glow_running = False
                return
            if time.monotonic() >= self._stop_at:
                self._glow_running = False
                try:
                    self._timer.stop()
                except Exception:
                    pass
                self.update()
                return
            # 1 vòng 360° trong 5 giây => ~1.15°/16ms
            self._phase = (self._phase + 1.15) % 360.0
            self.update()

        def paintEvent(self, event):
            super().paintEvent(event)
            if not self._glow_running:
                return
            painter = QPainter(self)
            try:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                rect = QRectF(self.rect()).adjusted(3.0, 3.0, -3.0, -3.0)
                radius = max(8.0, min(14.0, rect.height() / 2 - 4))
                path = QPainterPath()
                path.addRoundedRect(rect, radius, radius)

                color = QColor(self._color)
                # Lớp glow mềm bên ngoài
                painter.setPen(QPen(color, 2.0))
                painter.setOpacity(0.18)
                painter.drawPath(path)

                painter.setPen(QPen(color, 5.0))
                painter.setOpacity(0.30)
                painter.drawPath(path)

                # Vệt sáng chạy quanh viền — conical gradient quay
                grad = QConicalGradient(rect.center(), self._phase)
                grad.setColorAt(0.00, QColor(0, 0, 0, 0))
                grad.setColorAt(0.82, QColor(0, 0, 0, 0))
                grad.setColorAt(0.90, QColor(color.red(), color.green(), color.blue(), 0))
                grad.setColorAt(0.93, color)
                grad.setColorAt(0.96, QColor(color.red(), color.green(), color.blue(), 0))
                grad.setColorAt(1.00, QColor(0, 0, 0, 0))

                pen = QPen(QBrush(grad), 4.0)
                try:
                    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                except Exception:
                    pass
                painter.setOpacity(1.0)
                painter.setPen(pen)
                painter.drawPath(path)
            finally:
                painter.end()
except TypeError:
    # Test suite mock aqt.qt.QComboBox = lambda → không subclass được.
    # Khi đó dùng luôn mock để module import được (paint chỉ chạy runtime thật).
    _GlowProviderCombo = QComboBox


# ═══════════════════════════════════════════════════════════
#  DIALOG
# ═══════════════════════════════════════════════════════════

def show_ai_settings_dialog(parent):
    """Mở dialog cấu hình API Key & Provider.
    Trả về True nếu người dùng đã lưu."""
    cfg = get_api_config()

    dlg = QDialog(parent)
    dlg.setWindowTitle(t("dlg_ai_settings"))
    dlg.setMinimumSize(780, 520)
    dlg.resize(980, 600)
    dlg.setSizeGripEnabled(True)

    root = QVBoxLayout(dlg)
    root.setContentsMargins(14, 12, 14, 12)
    root.setSpacing(10)

    root.addWidget(QLabel(
        f"<h3>{t('ai_set_header_title')}</h3>"
        f"<p style='color:#777;'>{t('ai_set_header_sub')}</p>"
        f"<p style='color:#e67e22;'><b>{t('ai_set_header_tip')}</b></p>"
    ))

    # ═══ Splitter hai cột — kéo phân cách tùy ý ═══
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.setChildrenCollapsible(False)
    splitter.setHandleWidth(6)

    # ─────────────────────────────────────────────────────
    #  CỘT TRÁI: Provider (Preset) + Connection
    # ─────────────────────────────────────────────────────
    left_panel = QWidget()
    lv = QVBoxLayout(left_panel)
    lv.setContentsMargins(0, 0, 0, 0)
    lv.setSpacing(8)

    # ── Provider (Preset AI) ──
    provider_grp = QGroupBox(t("ai_set_preset_grp"))
    pv = QVBoxLayout(provider_grp)
    pv.setSpacing(6)

    pv.addWidget(QLabel(f"<b>{t('ai_set_provider_label')}</b>"))
    cbo_provider = _GlowProviderCombo(dlg)
    cbo_provider.setItemDelegate(_ProviderItemDelegate(cbo_provider))
    cbo_provider.setToolTip(t("ai_set_provider_tip"))

    for prow in AI_PROVIDERS:
        cbo_provider.addItem(f"  {prow['name']}", prow["id"])
        cbo_provider.setItemData(
            cbo_provider.count() - 1, dict(prow), int(Qt.ItemDataRole.UserRole)
        )
    # Custom
    cbo_provider.addItem(f"  {t('ai_set_provider_custom')}", "__custom__")
    cbo_provider.setItemData(
        cbo_provider.count() - 1,
        {"id": "__custom__", "name": "Custom", "color": "#8d94a6", "models": []},
        Qt.ItemDataRole.UserRole,
    )
    cbo_provider.setMinimumHeight(40)
    pv.addWidget(cbo_provider)

    lbl_provider_note = QLabel("")
    lbl_provider_note.setWordWrap(True)
    lbl_provider_note.setStyleSheet(
        "color:#8fd0ff; font-size:11px; padding:4px 6px;"
        "border-left:3px solid rgba(255,255,255,0.25); background:rgba(255,255,255,0.04);"
    )
    pv.addWidget(lbl_provider_note)
    pv.addWidget(QLabel(f"<i style='color:#555;'>{t('ai_set_glow_tip')}</i>"))

    lv.addWidget(provider_grp)

    # ── Connection (API Key / Base URL / Model) ──
    conn_grp = QGroupBox(t("ai_set_conn_grp"))
    cf = QFormLayout(conn_grp)
    cf.setSpacing(8)

    txt_key = QLineEdit()
    txt_key.setEchoMode(QLineEdit.EchoMode.Password)
    txt_key.setPlaceholderText(t("ai_set_api_key_placeholder"))
    txt_key.setText(cfg.get("api_key", ""))
    txt_key.setMinimumHeight(32)
    cf.addRow(QLabel(f"<b>{t('ai_set_api_key_label')}</b>"), txt_key)

    chk_show = QCheckBox(t("ai_set_show_key"))
    chk_show.toggled.connect(lambda checked: (
        txt_key.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
    ))
    cf.addRow("", chk_show)

    secret_store = get_api_key_storage_status()
    secret_store_key = (
        "ai_set_secret_store_ready"
        if secret_store["available"]
        else "ai_set_secret_store_unavailable"
    )
    secret_store_text = t(secret_store_key, command=secret_store["install_command"])
    secret_store_note = QLabel(secret_store_text)
    secret_store_note.setWordWrap(True)
    secret_store_note.setStyleSheet(
        "color:#267a3d;" if secret_store["available"] else "color:#c0392b;"
    )
    cf.addRow("", secret_store_note)

    txt_base = QLineEdit()
    txt_base.setPlaceholderText(t("ai_set_base_placeholder"))
    txt_base.setText(cfg.get("api_base", "https://api.openai.com/v1"))
    txt_base.setMinimumHeight(32)
    cf.addRow(QLabel(f"<b>{t('ai_set_base_label')}</b>"), txt_base)

    cbo_model = QComboBox()
    cbo_model.setEditable(True)
    cbo_model.setMinimumHeight(32)
    cf.addRow(QLabel(f"<b>{t('ai_set_model_label')}</b>"), cbo_model)

    lv.addWidget(conn_grp)
    lv.addStretch(1)

    # ─────────────────────────────────────────────────────
    #  CỘT PHẢI: Generation + Session policy + Cache
    # ─────────────────────────────────────────────────────
    right_panel = QWidget()
    rv = QVBoxLayout(right_panel)
    rv.setContentsMargins(0, 0, 0, 0)
    rv.setSpacing(8)

    # ── Generation (Temperature / Effort / Chunk) ──
    gen_grp = QGroupBox(t("ai_set_gen_grp"))
    gf = QFormLayout(gen_grp)
    gf.setSpacing(8)

    spin_temp = QDoubleSpinBox()
    spin_temp.setRange(0.0, 2.0)
    spin_temp.setSingleStep(0.1)
    spin_temp.setValue(cfg.get("temperature", 0.3))
    gf.addRow(QLabel(f"<b>{t('ai_set_temp_label')}</b>"), spin_temp)

    cbo_effort = QComboBox()
    effort_options = [
        (t("ai_set_effort_auto"), ""),
        (t("ai_set_effort_low"), "low"),
        (t("ai_set_effort_medium"), "medium"),
        (t("ai_set_effort_high"), "high"),
    ]
    for label, val in effort_options:
        cbo_effort.addItem(label, val)
    idx_effort = cbo_effort.findData(cfg.get("reasoning_effort", ""))
    if idx_effort >= 0:
        cbo_effort.setCurrentIndex(idx_effort)
    cbo_effort.setToolTip(t("ai_set_effort_tip"))
    gf.addRow(QLabel(f"<b>{t('ai_set_effort_label')}</b>"), cbo_effort)

    spin_chunk = QSpinBox()
    spin_chunk.setRange(3000, 15000)
    spin_chunk.setSingleStep(1000)
    spin_chunk.setValue(cfg.get("chunk_size", 8000))
    spin_chunk.setToolTip(t("ai_set_chunk_tip"))
    gf.addRow(QLabel(f"<b>{t('ai_set_chunk_label')}</b>"), spin_chunk)

    rv.addWidget(gen_grp)

    # ── Session policy ──
    sess_grp = QGroupBox(t("ai_set_session_grp"))
    sf = QFormLayout(sess_grp)
    sf.setSpacing(8)

    spin_session_input = QSpinBox()
    spin_session_input.setRange(1_000, 500_000)
    spin_session_input.setSingleStep(5_000)
    spin_session_input.setValue(cfg.get("session_max_input_chars", 90_000))
    spin_session_input.setToolTip(t("ai_set_session_input_tip"))
    sf.addRow(QLabel(f"<b>{t('ai_set_session_input_label')}</b>"), spin_session_input)

    spin_session_tokens = QSpinBox()
    spin_session_tokens.setRange(1_000, 1_000_000)
    spin_session_tokens.setSingleStep(10_000)
    spin_session_tokens.setValue(cfg.get("session_max_tokens", 120_000))
    spin_session_tokens.setToolTip(t("ai_set_session_tokens_tip"))
    sf.addRow(QLabel(f"<b>{t('ai_set_session_tokens_label')}</b>"), spin_session_tokens)

    spin_session_cost = QDoubleSpinBox()
    spin_session_cost.setRange(0.0, 1000.0)
    spin_session_cost.setDecimals(2)
    spin_session_cost.setSingleStep(0.5)
    spin_session_cost.setValue(cfg.get("session_max_cost_usd", 2.0))
    spin_session_cost.setToolTip(t("ai_set_session_cost_tip"))
    sf.addRow(QLabel(f"<b>{t('ai_set_session_cost_label')}</b>"), spin_session_cost)

    rv.addWidget(sess_grp)

    # ── Cache management ──
    cache_grp = QGroupBox(t("ai_set_cache_grp"))
    cache_bar = QHBoxLayout(cache_grp)

    btn_clear_cache = QPushButton(t("btn_clear_ai_cache"))
    btn_clear_cache.setStyleSheet(
        "padding:6px 12px;background:#e74c3c;color:white;font-weight:bold;border-radius:6px;"
    )
    btn_clear_cache.clicked.connect(lambda: (
        clear_cache(), tooltip(t("tooltip_cache_cleared"))
    ))
    cache_bar.addWidget(btn_clear_cache)

    btn_clear_history = QPushButton(t("btn_clear_history"))
    btn_clear_history.setStyleSheet(
        "padding:6px 12px;background:#e67e22;color:white;font-weight:bold;border-radius:6px;"
    )
    btn_clear_history.clicked.connect(lambda: (
        tooltip(
            t("tooltip_history_cleared")
            if clear_import_history()
            else t("tooltip_history_clear_fail")
        )
    ))
    cache_bar.addWidget(btn_clear_history)
    cache_bar.addStretch()

    rv.addWidget(cache_grp)
    rv.addStretch(1)

    splitter.addWidget(left_panel)
    splitter.addWidget(right_panel)
    splitter.setSizes([540, 400])
    root.addWidget(splitter, 1)

    # ── Hàm cập nhật UI theo provider ──
    def _provider_id_from_data(data):
        """Chuẩn hóa dữ liệu item combo → provider id (string).

        itemData()/currentData() mặc định trả về UserRole — là *dict* provider
        (delegate cần dict để vẽ màu). Nếu là dict thì lấy "id"; nếu là string
        (id) thì dùng luôn.
        """
        if isinstance(data, dict):
            return data.get("id", "")
        return data or ""

    def _apply_provider(provider_id, keep_current_model=False):
        current_model = cbo_model.currentText().strip()
        prow = get_provider(provider_id) if provider_id != "__custom__" else None

        cbo_provider.set_glow_color((prow or {}).get("color", "#8d9aae"))

        if prow:
            txt_base.setText((prow["base"]).rstrip("/"))
            txt_key.setPlaceholderText(prow.get("key_hint", ""))
            note_text = f"<b>{prow['name']}</b> — {prow.get('note', '')}"
            lbl_provider_note.setText(note_text)
        else:
            txt_key.setPlaceholderText(t("ai_set_api_key_placeholder"))
            lbl_provider_note.setText(t("ai_set_provider_custom_note"))

        # Model combo: chỉ model của provider
        cbo_model.blockSignals(True)
        cbo_model.clear()
        if prow:
            models = prow["models"]
            default_model = prow.get("default", models[0] if models else "")
            cbo_model.addItems(list(models))
            if current_model and current_model in models:
                cbo_model.setCurrentText(current_model)
            else:
                cbo_model.setCurrentText(default_model)
        cbo_model.blockSignals(False)

        if prow:
            # Effort mặc định: chỉ có ý nghĩa với model OpenAI o-series → để auto
            pass

    # ── Gắn sự kiện ──
    def _on_provider_changed(index):
        provider_id = _provider_id_from_data(cbo_provider.itemData(index))
        if provider_id:
            _apply_provider(provider_id, keep_current_model=True)
            # glow ngay khi người dùng chọn (5 giây)
            cbo_provider.start_glow(3500)

    cbo_provider.currentIndexChanged.connect(_on_provider_changed)

    def _find_provider_index(provider_id):
        """Tìm index item combo theo provider id.

        Không dùng findData() vì UserRole là dict (delegate cần vẽ màu) — so sánh
        string với dict luôn thất bại.
        """
        for i in range(cbo_provider.count()):
            data = cbo_provider.itemData(i)
            if isinstance(data, dict):
                if data.get("id") == provider_id:
                    return i
            elif data == provider_id:
                return i
        return -1

    # ── Chọn provider ban đầu ──
    saved_provider = cfg.get("provider", "")
    detected = saved_provider or detect_provider(cfg.get("api_base", ""), cfg.get("model", ""))
    provider_ids = [p["id"] for p in AI_PROVIDERS]
    target_id = detected if detected in provider_ids else "__custom__"
    idx = _find_provider_index(target_id)
    if idx < 0:
        idx = _find_provider_index("__custom__")
    cbo_provider.setCurrentIndex(idx)
    _apply_provider(target_id, keep_current_model=True)
    # Giữ model người dùng đang cấu hình (nếu nó có trong list provider)
    if cfg.get("model") and target_id != "__custom__":
        prow = get_provider(target_id)
        if prow and cfg["model"] in prow["models"]:
            cbo_model.setCurrentText(cfg["model"])

    # ── Thanh nút dưới cùng ──
    btn_layout = QHBoxLayout()
    btn_test = QPushButton(t("btn_test_connection"))
    btn_test.setStyleSheet(
        "padding:8px 16px;background:#3498db;color:white;font-weight:bold;border-radius:6px;"
    )
    btn_test.clicked.connect(lambda: _test_ai_connection(
        txt_key.text().strip(),
        txt_base.text().strip(),
        cbo_model.currentText().strip(),
        dlg,
    ))
    btn_layout.addWidget(btn_test)

    btn_edit_prompts = QPushButton(t("btn_edit_prompts"))
    btn_edit_prompts.setStyleSheet(
        "padding:8px 16px;background:#8e44ad;color:white;font-weight:bold;border-radius:6px;"
    )
    btn_edit_prompts.setToolTip(t("btn_edit_prompts_tip"))
    btn_edit_prompts.clicked.connect(lambda: show_prompt_editor_dialog(dlg))
    btn_layout.addWidget(btn_edit_prompts)

    btn_layout.addStretch()

    btn_cancel = QPushButton(t("btn_cancel_short"))
    btn_cancel.clicked.connect(dlg.reject)
    btn_layout.addWidget(btn_cancel)

    btn_save = QPushButton(t("btn_save"))
    btn_save.setStyleSheet(
        "padding:8px 20px;background:#27ae60;color:white;font-weight:bold;border-radius:6px;"
    )

    def save_settings():
        saved = save_api_config(
            txt_key.text().strip(),
            txt_base.text().strip(),
            cbo_model.currentText().strip(),
            spin_temp.value(),
            45000,                          # max_chars (mặc định 45k)
            spin_chunk.value(),             # chunk_size
            cbo_effort.currentData() or "",
            spin_session_input.value(),
            spin_session_tokens.value(),
            spin_session_cost.value(),
            _provider_id_from_data(cbo_provider.currentData()),
        )
        dlg.accept()
        tooltip(t("tooltip_saved_config") if saved else t("ai_set_secret_store_save_failed"))

    btn_save.clicked.connect(save_settings)
    btn_layout.addWidget(btn_save)
    root.addLayout(btn_layout)

    # Glow ngay khi mở dialog (hiệu ứng chào)
    cbo_provider.start_glow(2500)

    dlg.exec()


def _test_ai_connection(api_key, api_base, model, parent_dlg):
    """Test kết nối đến AI API"""
    if not api_base:
        tooltip("⚠️ Vui lòng nhập API Base URL.")
        return

    try:
        url = api_base.rstrip("/") + "/chat/completions"
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": "Say 'OK' in Vietnamese."}],
            "max_tokens": 10,
        }).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

        parent_dlg.setEnabled(False)
        from aqt.qt import QApplication
        QApplication.processEvents()

        # Timeout rộng rãi hơn cho bài test: nhiều model (nhất là reasoner) cần
        # thời gian suy nghĩ >15s; 15s trước đây gây "The read operation timed out".
        test_timeout = 90
        try:
            with urllib.request.urlopen(req, timeout=test_timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                reply = body.get("choices", [{}])[0].get("message", {}).get("content", "")
                showInfo(t("ai_test_success", model=model, reply=reply))
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")[:300]
            except Exception:
                pass
            showInfo(f"❌ Lỗi HTTP {e.code}: {e.reason}\n\n{err_body}")
        except (socket.timeout, TimeoutError) as e:
            showInfo(t("ai_test_error_timeout", timeout=test_timeout))
        except urllib.error.URLError as e:
            reason = getattr(e, "reason", e)
            showInfo(t("ai_test_error_conn", error=reason))
        except Exception as e:
            showInfo(t("ai_test_error_conn", error=e))
        finally:
            parent_dlg.setEnabled(True)

    except Exception as e:
        showInfo(f"❌ Lỗi: {e}")
