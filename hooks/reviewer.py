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
from utils.i18n import t

logger = get_logger()
_REGISTERED_HOOKS = set()

_AI_CONTEXT_FIELDS = {
    "front": "front", "simplified": "simplified", "traditional": "traditional",
    "pattern": "pattern", "furigana": "furigana", "pinyin": "pinyin",
    "romanization": "romanization", "meaning": "meaning", "usage": "usage",
    "explanation": "explanation", "usage pattern": "usage_pattern",
    "usage note": "usage_note", "collocation": "collocation", "example": "example",
    "example in vietnamese": "example_vn", "example2": "example2",
    "example2 in vietnamese": "example2_vn", "example3": "example3",
    "example3 in vietnamese": "example3_vn", "example4": "example4",
    "example4 in vietnamese": "example4_vn", "question": "question",
    "answer": "answer", "concept": "concept",
}


def _inject_ai_action(reviewer):
    """Add one subtle opt-in action; it never opens or calls AI automatically."""
    try:
        import json
        label = json.dumps(t("study_reviewer_action"), ensure_ascii=False)
        reviewer.web.eval(f"""
            (() => {{
              if (document.getElementById('bento-forge-ai-action')) return;
              if (!document.getElementById('bento-forge-ai-action-style')) {{
                const style = document.createElement('style');
                style.id = 'bento-forge-ai-action-style';
                style.textContent = `
                  #bento-forge-ai-action {{
                    position: fixed;
                    right: 12px;
                    top: 10px;
                    z-index: 9999;
                    opacity: .74;
                    border: 1px solid rgba(127, 127, 127, .42);
                    border-radius: 10px;
                    padding: 5px 9px;
                    background: rgba(127, 127, 127, .14);
                    color: inherit;
                    box-shadow: 0 1px 4px rgba(0, 0, 0, .16);
                    font: inherit;
                    font-size: 12px;
                    cursor: pointer;
                    backdrop-filter: blur(5px);
                    -webkit-backdrop-filter: blur(5px);
                  }}
                  #bento-forge-ai-action:hover,
                  #bento-forge-ai-action:focus-visible {{
                    opacity: 1;
                    border-color: currentColor;
                    outline: none;
                  }}
                  #bento-forge-ai-action:focus-visible {{
                    box-shadow: 0 0 0 2px rgba(127, 127, 127, .34);
                  }}
                  @media (prefers-color-scheme: dark) {{
                    #bento-forge-ai-action {{
                      background: rgba(255, 255, 255, .10);
                      border-color: rgba(255, 255, 255, .28);
                    }}
                  }}
                `;
                document.head.appendChild(style);
              }}
              const button = document.createElement('button');
              button.id = 'bento-forge-ai-action';
              button.type = 'button';
              button.textContent = {label};
              button.setAttribute('aria-label', {label});
              button.onclick = () => pycmd('bento_forge_ai:open');
              document.body.appendChild(button);
            }})();
        """)
    except Exception:
        pass


def get_current_card_snapshot(reviewer, side=None):
    """Return relevant current-card fields only; never attach review history."""
    try:
        card = getattr(reviewer, "card", None)
        if card is None:
            return None
        note = card.note()
        model = note.model() if note is not None else None
        model_name = str((model or {}).get("name") or "")
        lang_code = detect_lang_from_model(model_name)
        language = {"ja": "japanese", "zh": "chinese", "ko": "korean", "en": "english"}.get(lang_code, "")
        snapshot = {
            "language": language,
            "note_type": model_name,
            "side": side or getattr(reviewer, "_bento_forge_side", "question"),
            "card_id": getattr(card, "id", ""),
            "study_mode": get_study_mode(getattr(card, "did", None)),
        }
        try:
            from aqt import mw
            snapshot["deck"] = mw.col.decks.name(getattr(card, "did", 0))
        except Exception:
            pass
        if note is not None:
            items = note.items() if callable(getattr(note, "items", None)) else []
            for field_name, value in items:
                key = _AI_CONTEXT_FIELDS.get(str(field_name).strip().casefold())
                if key and str(value or "").strip():
                    snapshot[key] = str(value).strip()[:4_000]
        return snapshot
    except Exception as error:
        log_event(
            "AI_CARD_CONTEXT_FAILED", "open_companion_without_card_context",
            error=error.__class__.__name__,
        )
        return None


def _refresh_companion_context(snapshot):
    """Refresh an existing dock without making Reviewer hooks depend on its UI."""
    try:
        from ui.ai_companion import refresh_ai_companion_context

        refresh_ai_companion_context(snapshot)
    except Exception as error:
        logger.debug("AI companion context refresh unavailable: %s", error)


def open_companion_from_reviewer(context):
    reviewer = getattr(context, "reviewer", None) or context
    snapshot = get_current_card_snapshot(reviewer)
    from ui.ai_companion import show_ai_companion
    return show_ai_companion(
        snapshot=snapshot,
        language=str((snapshot or {}).get("language") or ""),
    )

# Import an toàn module overview_mode (tránh circular import ở mức module load)
try:
    from hooks.overview_mode import get_study_mode
except Exception:
    def get_study_mode(_deck_id=None):
        return "qa"


def _on_reviewer_question(reviewer):
    """Inject Letter Gap JS khi hiện mặt trước thẻ + sync mode combo."""
    try:
        reviewer._bento_forge_side = "question"
        card = reviewer.card
        if card is None:
            return
        snapshot = get_current_card_snapshot(reviewer, side="question")
        _refresh_companion_context(snapshot)
        q = card.q() or ""
        _inject_ai_action(reviewer)
        # Card combo (1 từ = 1 card, 5 chế độ): đồng bộ mode từ config
        if 'id="combo-mode-bar"' in q and 'data-srs-layout="combo"' in q:
            mode = str((snapshot or {}).get("study_mode") or "qa")
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
    _inject_ai_action(reviewer)
    # Bước 1: Xác định tốc độ mặc định
    default_spd = 1.0
    try:
        reviewer._bento_forge_side = "answer"
        card = reviewer.card
        if card is not None:
            _refresh_companion_context(get_current_card_snapshot(reviewer, side="answer"))
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
