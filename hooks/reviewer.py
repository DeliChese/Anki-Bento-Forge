"""
Hooks package — Reviewer hooks for AnkiTool.
"""

try:
    from aqt import gui_hooks
except Exception:
    gui_hooks = None

from audio.engine import detect_lang_from_model, get_default_speed
from mode import _SPEED_CTRL_JS, _LG_JS_BODY
from utils.logger import get_logger, log_event

logger = get_logger()
_REGISTERED_HOOKS = set()

# Import an toàn module overview_mode (tránh circular import ở mức module load)
try:
    from hooks.overview_mode import get_study_mode
except Exception:
    def get_study_mode():
        return "qa"


def _on_reviewer_question(reviewer):
    """Inject Letter Gap JS khi hiện mặt trước thẻ + sync mode combo."""
    try:
        card = reviewer.card
        if card is None:
            return
        q = card.q() or ""
        # Card combo (1 từ = 1 card, 5 chế độ): đồng bộ mode từ config
        if 'id="combo-mode-bar"' in q and 'data-srs-layout="combo"' in q:
            mode = get_study_mode(getattr(card, "did", None))
            js = (
                f"window._aiFactoryMode='{mode}';"
                f"window.dispatchEvent(new CustomEvent('ai-factory-mode',{{detail:'{mode}'}}));"
            )
            try:
                reviewer.web.eval(js)
            except Exception:
                pass
        # Letter Gap (cả card combo lẫn card cũ đều có lg-display)
        if 'id="lg-display"' in q:
            reviewer.web.eval(_LG_JS_BODY)
    except Exception:
        pass


def _on_reviewer_answer(reviewer):
    """Inject Speed Control JS khi hiện mặt sau thẻ."""
    # Bước 1: Xác định tốc độ mặc định
    default_spd = 1.0
    try:
        card = reviewer.card
        if card is not None:
            note = card.note()
            if note is not None:
                model = note.model()
                if model is not None:
                    lang = detect_lang_from_model(model['name'])
                    if lang:
                        default_spd = get_default_speed(lang)
    except Exception:
        pass

    # Bước 2: Inject JS tốc độ
    try:
        reviewer.web.eval(f"window._ankiDefaultSpeed={default_spd};" + _SPEED_CTRL_JS)
    except Exception:
        pass


def _register_gui_hook(name, callback):
    """Register one public Anki hook without assuming other hooks exist."""
    if name in _REGISTERED_HOOKS:
        return True
    hook = getattr(gui_hooks, name, None) if gui_hooks is not None else None
    append = getattr(hook, "append", None)
    if not callable(append):
        logger.warning(
            "HOOK_REVIEWER_UNAVAILABLE: Anki does not expose gui_hooks.%s; feature disabled.",
            name,
        )
        return False
    try:
        append(callback)
        _REGISTERED_HOOKS.add(name)
        return True
    except Exception as exc:
        log_event(
            "HOOK_REVIEWER_REGISTER_FAILED",
            "disable_reviewer_hook",
            hook=name,
            error=exc.__class__.__name__,
        )
        return False


def register_hooks():
    """Register available reviewer hooks, gracefully disabling missing features."""
    question_registered = _register_gui_hook(
        "reviewer_did_show_question", _on_reviewer_question
    )
    answer_registered = _register_gui_hook(
        "reviewer_did_show_answer", _on_reviewer_answer
    )
    return question_registered or answer_registered
