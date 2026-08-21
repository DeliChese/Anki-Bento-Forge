"""
Overview Mode — đồng bộ chế độ học (qa/vn/wb/pron/lg) từ thẻ với Anki.

- Đăng ký public hook `webview_did_receive_js_message` → xử lý `ai_factory_set_mode:xxx`
  (lưu mode vào mw.col.conf) để card đọc mode qua reviewer hook.

Không patch `Overview._table`: đây là private API không có cam kết tương thích.
"""

import json

# Import an toàn (không import aqt top-level cứng — test chạy không cần Anki)
try:
    from aqt import gui_hooks
except Exception:
    gui_hooks = None

from utils.logger import get_logger

logger = get_logger()
_REGISTERED_HOOKS = set()

# Key lưu chế độ học trong mw.col.conf
CONF_KEY = "ai_factory_study_mode"
CONF_DECK_MODES_KEY = "ai_factory_study_mode_by_deck"
CONF_SRS_LAYOUT_KEY = "ai_factory_srs_layout"
CONF_DECK_SRS_LAYOUTS_KEY = "ai_factory_srs_layout_by_deck"
# Key lưu cấu hình lựa chọn ngôn ngữ hiện tại (dùng để hiển thị label đúng)
CONF_LANG_KEY = "ai_factory_active_lang"

# Các chế độ học (khớp với _COMBO_MODE_JS trong mode/shared.py)
MODES = ("qa", "vn", "wb", "pron", "lg")
SRS_LAYOUTS = ("combo", "independent")


def _deck_value(conf, mapping_key, deck_id):
    if deck_id is None:
        return None
    mapping = conf.get(mapping_key, {})
    if not isinstance(mapping, dict):
        return None
    return mapping.get(str(deck_id))


def get_study_mode(deck_id=None):
    """Read a stable default direction for one deck, with legacy fallback."""
    try:
        from aqt import mw
        mode = _deck_value(mw.col.conf, CONF_DECK_MODES_KEY, deck_id)
        if mode is None:
            mode = mw.col.conf.get(CONF_KEY, "qa")
        if mode not in MODES:
            mode = "qa"
        return mode
    except Exception:
        return "qa"


def set_study_mode(mode, deck_id=None):
    """Persist a mode globally and, when known, for the selected deck."""
    if mode not in MODES:
        mode = "qa"
    try:
        from aqt import mw
        if deck_id is None:
            mw.col.conf[CONF_KEY] = mode
        else:
            mapping = mw.col.conf.get(CONF_DECK_MODES_KEY, {})
            mapping = dict(mapping) if isinstance(mapping, dict) else {}
            mapping[str(deck_id)] = mode
            mw.col.conf[CONF_DECK_MODES_KEY] = mapping
        mw.col.setMod()
        return True
    except Exception as e:
        logger.warning("Không lưu được study mode: %s", e)
        return False


def get_srs_layout(deck_id=None):
    """Return combo by default so upgrades never create surprise cards."""
    try:
        from aqt import mw
        layout = _deck_value(mw.col.conf, CONF_DECK_SRS_LAYOUTS_KEY, deck_id)
        if layout is None:
            layout = mw.col.conf.get(CONF_SRS_LAYOUT_KEY, "combo")
        return layout if layout in SRS_LAYOUTS else "combo"
    except Exception:
        return "combo"


def set_srs_layout(layout, deck_id=None):
    """Persist creation policy; existing notes are intentionally untouched."""
    if layout not in SRS_LAYOUTS:
        layout = "combo"
    try:
        from aqt import mw
        if deck_id is None:
            mw.col.conf[CONF_SRS_LAYOUT_KEY] = layout
        else:
            mapping = mw.col.conf.get(CONF_DECK_SRS_LAYOUTS_KEY, {})
            mapping = dict(mapping) if isinstance(mapping, dict) else {}
            mapping[str(deck_id)] = layout
            mw.col.conf[CONF_DECK_SRS_LAYOUTS_KEY] = mapping
        mw.col.setMod()
        return True
    except Exception as exc:
        logger.warning("Không lưu được SRS layout: %s", exc)
        return False


def _context_deck_id(context):
    try:
        card = getattr(context, "card", None)
        if card is None:
            card = getattr(getattr(context, "reviewer", None), "card", None)
        return getattr(card, "did", None)
    except Exception:
        return None


def _on_js_message(handled, message, context):
    """Xử lý pycmd từ webview:
       - ai_factory_set_mode:xxx     → đổi chế độ học (từ combo-mode-bar trong thẻ)
       - ai_grammar_sentence:{json}  → AI sinh câu luyện dịch ngữ pháp + đẩy vào card
    """
    try:
        if message and message.startswith("ai_factory_set_mode:"):
            mode = message.split(":", 1)[1].strip()
            set_study_mode(mode, _context_deck_id(context))
            return (True, None)
        if message and message.startswith("ai_grammar_sentence:"):
            return _handle_grammar_sentence(message, context)
        if message == "bento_forge_ai:open":
            from hooks.reviewer import open_companion_from_reviewer
            open_companion_from_reviewer(context)
            return (True, None)
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
        from utils.language_identity import normalize_language
        lang = normalize_language(data.get("lang"))
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
    hook_name = "webview_did_receive_js_message"
    if hook_name in _REGISTERED_HOOKS:
        return True
    hook = getattr(gui_hooks, hook_name, None) if gui_hooks is not None else None
    append = getattr(hook, "append", None)
    if not callable(append):
        logger.warning(
            "HOOK_OVERVIEW_UNAVAILABLE: Anki does not expose gui_hooks.%s; mode sync disabled.",
            hook_name,
        )
        return False
    try:
        append(_on_js_message)
        _REGISTERED_HOOKS.add(hook_name)
        return True
    except Exception as exc:
        logger.warning("HOOK_OVERVIEW_REGISTER_FAILED: %s", exc)
        return False
