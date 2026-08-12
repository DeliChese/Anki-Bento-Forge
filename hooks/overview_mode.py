"""
Overview Mode Selector — chèn bộ chọn chế độ học (qa/vn/wb/pron/lg) vào
màn hình overview của Anki (tương thích Onigiri "Study now").

- Patch Overview._table (wrap, KHÔNG ghi đè) → chèn selector cạnh nút Study now.
- Đăng ký webview_did_receive_js_message → xử lý `ai_factory_set_mode:xxx`
  (lưu mode vào mw.col.conf) để card đọc mode qua reviewer hook.
"""

import json

# Import an toàn (không import aqt top-level cứng — test chạy không cần Anki)
try:
    from aqt import gui_hooks
except Exception:
    gui_hooks = None

from utils.logger import get_logger
from utils.i18n import t, study_mode_labels

logger = get_logger()

# Key lưu chế độ học trong mw.col.conf
CONF_KEY = "ai_factory_study_mode"
# Key lưu cấu hình lựa chọn ngôn ngữ hiện tại (dùng để hiển thị label đúng)
CONF_LANG_KEY = "ai_factory_active_lang"

# Các chế độ học (khớp với _COMBO_MODE_JS trong mode/shared.py)
MODES = ("qa", "vn", "wb", "pron", "lg")


def get_study_mode():
    """Đọc mode hiện tại từ mw.col.conf."""
    try:
        from aqt import mw
        mode = mw.col.conf.get(CONF_KEY, "qa")
        if mode not in MODES:
            mode = "qa"
        return mode
    except Exception:
        return "qa"


def set_study_mode(mode):
    """Lưu mode vào mw.col.conf (persist giữa các phiên học)."""
    if mode not in MODES:
        mode = "qa"
    try:
        from aqt import mw
        mw.col.conf[CONF_KEY] = mode
        mw.col.setMod()
        return True
    except Exception as e:
        logger.warning("Không lưu được study mode: %s", e)
        return False


def _build_selector_html():
    """Tạo HTML selector chọn chế độ học + nút Study now."""
    try:
        from aqt import mw
        lang = mw.col.conf.get(CONF_LANG_KEY, "japanese")
    except Exception:
        lang = "japanese"
    # Nhãn theo ngôn ngữ học + ngôn ngữ UI (vi: "Nhật→Việt" / en: "Japanese→English")
    labels = study_mode_labels(lang)
    current = get_study_mode()
    opts = "".join(
        f'<option value="{k}"{" selected" if k == current else ""}>{labels[k]}</option>'
        for k in MODES
    )
    return (
        '<div class="ai-factory-mode-selector" style="'
        'display:flex;align-items:center;justify-content:center;gap:10px;'
        'flex-wrap:wrap;padding:8px 12px;margin:0 auto 8px;max-width:520px;'
        'background:rgba(128,128,128,.08);border-radius:14px;">'
        f'<span style="font-size:12px;font-weight:700;opacity:.75;">{t("overview_mode_label")}</span>'
        '<select id="ai-factory-mode" onchange="pycmd(\'ai_factory_set_mode:\'+this.value)"'
        ' style="padding:6px 10px;border-radius:10px;border:1px solid #888;background:transparent;font-size:13px;">'
        f'{opts}'
        '</select>'
        '<button id="ai-factory-study" onclick="pycmd(\'study\'); return false;"'
        ' style="padding:7px 16px;border-radius:12px;border:none;'
        'background:linear-gradient(135deg,#4fa3d1,#2980b9);color:#fff;'
        'font-weight:700;font-size:13px;cursor:pointer;">▶ Study now</button>'
        '</div>'
    )


def _inject_selector(html):
    """Chèn selector vào HTML overview — trước nút Study now (nếu có)."""
    selector = _build_selector_html()
    # Ưu tiên chèn ngay trước button id="study" (cả Onigiri lẫn Anki gốc đều có)
    marker = '<button id="study"'
    if marker in html:
        idx = html.index(marker)
        return html[:idx] + selector + html[idx:]
    # Fallback: chèn trước nút học (Anki cũ dùng class add-button)
    marker2 = 'id="study"'
    if marker2 in html:
        idx = html.index(marker2)
        return html[:idx] + selector + html[idx:]
    return selector + html


def _patch_overview():
    """Wrap Overview._table để chèn selector chọn mode (không ghi đè bản Onigiri)."""
    try:
        from aqt.overview import Overview

        # Tránh patch trùng (nếu profile load lại)
        if getattr(Overview, "_ai_factory_mode_patched", False):
            return
        _orig_table = Overview._table

        def _wrapped_table(self):
            try:
                html = _orig_table(self)
            except Exception as e:
                logger.warning("Overview._table lỗi: %s", e)
                html = ""
            return _inject_selector(html)

        Overview._table = _wrapped_table
        Overview._ai_factory_mode_patched = True
        logger.info("Đã chèn selector chế độ học vào Overview (tương thích Onigiri).")
    except Exception as e:
        logger.warning("Không patch được Overview: %s", e)


def _on_js_message(handled, message, context):
    """Xử lý pycmd từ webview:
       - ai_factory_set_mode:xxx     → đổi chế độ học (từ combo-mode-bar trong thẻ)
       - ai_grammar_sentence:{json}  → AI sinh câu luyện dịch ngữ pháp + đẩy vào card
    """
    try:
        if message and message.startswith("ai_factory_set_mode:"):
            mode = message.split(":", 1)[1].strip()
            set_study_mode(mode)
            return (True, None)
        if message and message.startswith("ai_grammar_sentence:"):
            return _handle_grammar_sentence(message, context)
    except Exception as e:
        logger.warning("Lỗi xử lý webview message: %s", e)
    return handled


def _handle_grammar_sentence(message, context):
    """Sinh câu luyện dịch ngữ pháp bằng AI, đẩy kết quả vào JS của card.

    Card gửi: pycmd('ai_grammar_sentence:' + JSON{pattern, meaning, lang}).
    Python gọi AI → gọi context.web.eval("window._aiGrammarResult({...})")
    để card hiển thị (streaming) + tự chấm điểm bản dịch của người học.
    """
    try:
        import json as _json
        raw = message.split(":", 1)[1] if ":" in message else "{}"
        data = _json.loads(raw or "{}")
        pattern = str(data.get("pattern") or "")
        meaning = str(data.get("meaning") or "")
        lang = str(data.get("lang") or "japanese")
        from utils.grammar_ai import generate_grammar_sentence
        result = generate_grammar_sentence(pattern, meaning, lang)
        js = (
            "if (window._aiGrammarResult) {"
            f"window._aiGrammarResult({_json.dumps(result, ensure_ascii=False)});"
            "}"
        )
        try:
            context.web.eval(js)
        except Exception:
            pass
        return (True, None)
    except Exception as e:
        logger.warning("Lỗi xử lý ai_grammar_sentence: %s", e)
        return (True, None)


def register_overview_hooks():
    """Đăng ký webview message handler cho chế độ học.

    ❌ KHÔNG còn patch Overview._table để chèn selector + nút "Study now" nữa.
       Lý do (fix luồng học):
         - Tránh TRÙNG nút "Study now" (selector chèn thêm 1 nút cạnh nút gốc của Anki).
         - Thống nhất CHỈ MỘT nguồn điều khiển chế độ học: thanh `combo-mode-bar`
           NGAY TRONG THẺ (5 mode: qa/vn/wb/pron/lg) thay vì 2 tầng (overview + card).
       Vẫn giữ `_on_js_message` để thẻ có thể gọi `ai_factory_set_mode:xxx`
       (đồng bộ mode từ combo-mode-bar xuống mw.col.conf).
    """
    if gui_hooks is None:
        return
    try:
        gui_hooks.webview_did_receive_js_message.append(_on_js_message)
    except Exception as e:
        logger.warning("Không đăng ký được overview hooks: %s", e)
