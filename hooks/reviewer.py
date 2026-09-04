"""
Hooks package — Reviewer hooks for AnkiTool.
"""

import json

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


def _resolve_reviewer(hook_arg):
    """Return the Reviewer for both legacy and current Anki hook signatures."""
    if callable(getattr(getattr(hook_arg, "web", None), "eval", None)):
        return hook_arg
    try:
        from aqt import mw
        reviewer = getattr(mw, "reviewer", None)
        if not callable(getattr(getattr(reviewer, "web", None), "eval", None)):
            return None
        hook_card_id = getattr(hook_arg, "id", None)
        active_card_id = getattr(getattr(reviewer, "card", None), "id", None)
        if isinstance(hook_card_id, int) and isinstance(active_card_id, int):
            if hook_card_id != active_card_id:
                return None
        return reviewer
    except Exception as error:
        logger.debug("Reviewer hook context unavailable: %s", error)
        return None

_AI_CONTEXT_FIELDS = {
    "front": "front", "simplified": "simplified", "traditional": "traditional",
    "word": "front", "vocabulary": "front", "term": "front", "expression": "front",
    "target": "front", "target word": "front", "vocabulary word": "front",
    "expression text": "front",
    "hanzi": "front", "kanji": "front", "hangul": "front",
    "pattern": "pattern", "grammar pattern": "pattern", "structure": "pattern",
    "reading": "reading", "pronunciation": "pronunciation",
    "furigana": "furigana", "pinyin": "pinyin",
    "romanization": "romanization", "meaning": "meaning", "usage": "usage",
    "explanation": "explanation", "usage pattern": "usage_pattern",
    "usage note": "usage_note", "collocation": "collocation", "example": "example",
    "sino-vietnamese": "sino_vietnamese", "jlpt level": "level",
    "hsk level": "level", "topik level": "level", "cefr level": "level",
    "level": "level", "topic": "topic",
    "example pinyin": "example_pinyin",
    "example romanization": "example_romanization",
    "example reading": "example_reading",
    "example pronunciation": "example_pronunciation",
    "example in vietnamese": "example_vn", "example2": "example2",
    "example2 pinyin": "example2_pinyin",
    "example2 romanization": "example2_romanization",
    "example2 reading": "example2_reading",
    "example2 pronunciation": "example2_pronunciation",
    "example2 in vietnamese": "example2_vn", "example3": "example3",
    "example3 pinyin": "example3_pinyin",
    "example3 romanization": "example3_romanization",
    "example3 reading": "example3_reading",
    "example3 pronunciation": "example3_pronunciation",
    "example3 in vietnamese": "example3_vn", "example4": "example4",
    "example4 pinyin": "example4_pinyin",
    "example4 romanization": "example4_romanization",
    "example4 reading": "example4_reading",
    "example4 pronunciation": "example4_pronunciation",
    "example4 in vietnamese": "example4_vn", "question": "question",
    "answer": "answer", "concept": "concept",
}

_TARGET_FIELD_KEYS = (
    "front", "simplified", "pattern", "question", "concept",
    "traditional",
)


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


def _production_drill_payload(snapshot):
    """Build a local-only production drill from explicit Usage Guide fields."""
    if not isinstance(snapshot, dict):
        return None
    target = str(snapshot.get("current_target") or "").strip()
    guides = []
    for key, label_key in (
        ("usage_pattern", "production_drill_pattern"),
        ("collocation", "production_drill_collocation"),
    ):
        value = str(snapshot.get(key) or "").strip()
        if value:
            guides.append({"label": t(label_key), "value": value[:1_000]})
    if not target or not guides:
        return None
    example = str(snapshot.get("example") or "").strip()
    if example:
        guides.append({"label": t("production_drill_example"), "value": example[:1_000]})
    return {
        "target": target[:240],
        "guides": guides,
    }


def _inject_production_drill(reviewer, snapshot):
    """Inject an opt-in, zero-AI sentence-production drill on the question side."""
    payload = _production_drill_payload(snapshot)
    if payload is None:
        return False
    strings = {
        "action": t("production_drill_action"),
        "title": t("production_drill_title"),
        "instruction": t("production_drill_instruction"),
        "placeholder": t("production_drill_placeholder"),
        "reveal": t("production_drill_reveal"),
        "hide": t("production_drill_hide"),
        "clear": t("production_drill_clear"),
        "close": t("production_drill_close"),
    }
    data_json = json.dumps(payload, ensure_ascii=False)
    strings_json = json.dumps(strings, ensure_ascii=False)
    try:
        reviewer.web.eval(f"""
            (() => {{
              if (document.getElementById('bento-production-drill-action')) return;
              const data = {data_json};
              const copy = {strings_json};
              if (!document.getElementById('bento-production-drill-style')) {{
                const style = document.createElement('style');
                style.id = 'bento-production-drill-style';
                style.textContent = `
                  #bento-production-drill-action {{
                    position: fixed; right: 12px; top: 48px; z-index: 9999;
                    border: 1px solid rgba(53,111,164,.46); border-radius: 10px;
                    padding: 5px 9px; background: rgba(53,111,164,.13);
                    color: inherit; font: inherit; font-size: 12px; cursor: pointer;
                  }}
                  #bento-production-drill {{
                    position: fixed; right: 12px; top: 84px; z-index: 10000;
                    width: min(390px, calc(100vw - 24px)); box-sizing: border-box;
                    padding: 14px; border: 1px solid rgba(127,127,127,.42);
                    border-radius: 14px; background: var(--canvas, #fff); color: inherit;
                    box-shadow: 0 10px 34px rgba(0,0,0,.22); font: inherit;
                  }}
                  #bento-production-drill[hidden] {{ display: none; }}
                  #bento-production-drill textarea {{
                    width: 100%; min-height: 92px; box-sizing: border-box; resize: vertical;
                    margin: 10px 0; padding: 9px; border: 1px solid rgba(127,127,127,.45);
                    border-radius: 9px; background: transparent; color: inherit; font: inherit;
                  }}
                  #bento-production-drill-guide {{
                    margin: 8px 0; padding: 9px; border-radius: 9px;
                    background: rgba(53,111,164,.10); white-space: pre-wrap;
                  }}
                  #bento-production-drill-actions {{ display: flex; gap: 7px; flex-wrap: wrap; }}
                  #bento-production-drill button {{
                    border: 1px solid rgba(127,127,127,.42); border-radius: 8px;
                    padding: 5px 9px; background: transparent; color: inherit;
                    font: inherit; cursor: pointer;
                  }}
                  #bento-production-drill-title {{ font-weight: 700; margin-right: 24px; }}
                  #bento-production-drill-target {{ font-weight: 650; color: #356fa4; }}
                  #bento-production-drill-close {{ position: absolute; right: 9px; top: 7px; }}
                  @media (prefers-color-scheme: dark) {{
                    #bento-production-drill {{ background: #252525; }}
                  }}
                `;
                document.head.appendChild(style);
              }}

              const action = document.createElement('button');
              action.id = 'bento-production-drill-action';
              action.type = 'button';
              action.textContent = copy.action;
              action.setAttribute('aria-expanded', 'false');

              const panel = document.createElement('section');
              panel.id = 'bento-production-drill';
              panel.hidden = true;
              panel.setAttribute('aria-label', copy.title);

              const title = document.createElement('div');
              title.id = 'bento-production-drill-title';
              title.textContent = copy.title;
              const close = document.createElement('button');
              close.id = 'bento-production-drill-close';
              close.type = 'button';
              close.textContent = '×';
              close.setAttribute('aria-label', copy.close);
              const instruction = document.createElement('div');
              instruction.textContent = copy.instruction + ' ';
              const target = document.createElement('span');
              target.id = 'bento-production-drill-target';
              target.textContent = data.target;
              instruction.appendChild(target);
              const draft = document.createElement('textarea');
              draft.placeholder = copy.placeholder;
              draft.setAttribute('aria-label', copy.placeholder);
              const guide = document.createElement('div');
              guide.id = 'bento-production-drill-guide';
              guide.hidden = true;
              const guideText = document.createElement('div');
              data.guides.forEach((item, index) => {{
                if (index) guideText.appendChild(document.createElement('br'));
                const label = document.createElement('strong');
                label.textContent = item.label + ': ';
                guideText.appendChild(label);
                guideText.appendChild(document.createTextNode(item.value));
              }});
              guide.appendChild(guideText);
              const actions = document.createElement('div');
              actions.id = 'bento-production-drill-actions';
              const reveal = document.createElement('button');
              reveal.type = 'button';
              reveal.textContent = copy.reveal;
              const clear = document.createElement('button');
              clear.type = 'button';
              clear.textContent = copy.clear;
              actions.append(reveal, clear);
              panel.append(title, close, instruction, draft, guide, actions);
              document.body.append(action, panel);

              const setOpen = (open) => {{
                panel.hidden = !open;
                action.setAttribute('aria-expanded', String(open));
                if (open) draft.focus();
              }};
              action.onclick = () => setOpen(panel.hidden);
              close.onclick = () => setOpen(false);
              reveal.onclick = () => {{
                guide.hidden = !guide.hidden;
                reveal.textContent = guide.hidden ? copy.reveal : copy.hide;
              }};
              clear.onclick = () => {{ draft.value = ''; draft.focus(); }};
              panel.addEventListener('keydown', (event) => {{
                event.stopPropagation();
                if (event.key === 'Escape') setOpen(false);
              }});
            }})();
        """)
        return True
    except Exception as error:
        logger.debug("Production drill injection unavailable: %s", error)
        return False


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
        if not language:
            normalized_model = model_name.casefold()
            language = next(
                (name for name in ("japanese", "chinese", "korean", "english")
                 if name in normalized_model),
                "",
            )
        snapshot = {
            "language": language,
            "note_type": model_name,
            "side": side or getattr(reviewer, "_bento_forge_side", "question"),
            "card_id": getattr(card, "id", ""),
            "note_id": getattr(note, "id", "") if note is not None else "",
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
                clean_value = str(value or "").strip()
                key = _AI_CONTEXT_FIELDS.get(str(field_name).strip().casefold())
                if key and clean_value:
                    snapshot[key] = clean_value[:4_000]
            is_grammar = "grammar" in model_name.casefold() or bool(snapshot.get("pattern"))
            target_order = (
                ("pattern", "front", "question", "concept")
                if is_grammar else _TARGET_FIELD_KEYS
            )
            current_target = next(
                (snapshot.get(key) for key in target_order if snapshot.get(key)),
                "",
            )
            if current_target:
                snapshot["current_target"] = current_target
            snapshot["card_kind"] = (
                "grammar" if is_grammar
                else "collocation" if "collocation" in model_name.casefold()
                else "vocabulary"
            )
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


def _example_review_payload(reviewer, snapshot):
    if not snapshot or not snapshot.get("language"):
        return None
    try:
        from utils.example_note_ops import read_example_state
        note = reviewer.card.note()
        slots = {}
        for slot in range(1, 5):
            state = read_example_state(note, snapshot["language"], slot)
            record = (
                state["versions"][state["active"]]
                if 0 <= state["active"] < len(state["versions"]) else {}
            )
            slots[str(slot)] = {
                "current": state["active"] + 1 if state["active"] >= 0 else 0,
                "total": len(state["versions"]),
                "reading": str(record.get("reading") or ""),
            }
        return {"slots": slots}
    except Exception as error:
        logger.debug("Example regeneration payload unavailable: %s", error)
        return None


def _inject_example_regeneration(reviewer, snapshot):
    """Add one opt-in version action to each Example 1–4 block."""
    payload = _example_review_payload(reviewer, snapshot)
    if payload is None:
        return False
    copy = {
        "action": t("example_regen_action", current="{current}", total="{total}"),
        "empty": t("example_regen_empty"),
    }
    try:
        reviewer.web.eval(f"""
            (() => {{
              const data = {json.dumps(payload, ensure_ascii=False)};
              const copy = {json.dumps(copy, ensure_ascii=False)};
              if (!document.getElementById('bento-example-version-style')) {{
                const style = document.createElement('style');
                style.id = 'bento-example-version-style';
                style.textContent = `
                  .bento-example-version-action {{
                    margin-left:auto; border:1px solid rgba(53,111,164,.42);
                    border-radius:8px; padding:3px 7px; background:rgba(53,111,164,.10);
                    color:inherit; font:inherit; font-size:10px; cursor:pointer;
                  }}
                  .bento-example-version-action:hover {{ border-color:currentColor; }}
                  .bento-example-placeholder .ej {{ opacity:.58; font-style:italic; }}
                  .bento-example-reading {{ opacity:.76; font-size:.88em; margin-top:3px; }}
                  .ec > .en {{ display:flex; align-items:center; gap:8px; }}
                `;
                document.head.appendChild(style);
              }}
              const headers = Array.from(document.querySelectorAll('.ec > .en'));
              const blocks = {{}};
              headers.forEach(header => {{
                const match = String(header.textContent || '').match(/(?:VÍ DỤ|EXAMPLE)\\s*([1-4])/i);
                if (match) blocks[match[1]] = header.closest('.ec');
              }});
              let section = Array.from(document.querySelectorAll('.es')).find(node => {{
                const label = node.querySelector('.esl');
                return label && /ví dụ|example/i.test(String(label.textContent || ''));
              }});
              if (!section) return;
              for (let slot = 1; slot <= 4; slot++) {{
                const key = String(slot);
                const state = data.slots[key] || {{current:0,total:0,reading:''}};
                let block = blocks[key];
                if (!block) {{
                  block = document.createElement('div');
                  block.className = 'ec bento-example-placeholder';
                  block.innerHTML = `<div class="en">VÍ DỤ ${{slot}}</div><div class="ej"></div>`;
                  block.querySelector('.ej').textContent = copy.empty;
                  section.appendChild(block);
                }}
                const header = block.querySelector('.en');
                if (!header || header.querySelector('.bento-example-version-action')) continue;
                if (state.reading && !block.querySelector('.ep,.bento-example-reading')) {{
                  const reading = document.createElement('div');
                  reading.className = 'bento-example-reading';
                  reading.textContent = state.reading;
                  const sentence = block.querySelector('.ej');
                  if (sentence) sentence.insertAdjacentElement('afterend', reading);
                }}
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'bento-example-version-action';
                button.textContent = copy.action
                  .replace('{{current}}', String(state.current || 0))
                  .replace('{{total}}', String(state.total || 0));
                button.onclick = event => {{
                  event.preventDefault(); event.stopPropagation();
                  pycmd(`bento_example:open:${{slot}}`);
                }};
                header.appendChild(button);
              }}
            }})();
        """)
        return True
    except Exception as error:
        logger.debug("Example regeneration injection unavailable: %s", error)
        return False


def open_example_regenerator_from_reviewer(context, slot):
    reviewer = _resolve_reviewer(getattr(context, "reviewer", None) or context)
    if reviewer is None:
        return None
    snapshot = get_current_card_snapshot(reviewer, side="answer")
    if not snapshot or not snapshot.get("note_id"):
        return None
    from utils.example_note_ops import read_example_state
    from ui.example_regenerator import show_example_regenerator
    note = reviewer.card.note()
    state = read_example_state(note, snapshot["language"], int(slot))
    return show_example_regenerator(reviewer, snapshot, int(slot), state)

# Import an toàn module overview_mode (tránh circular import ở mức module load)
try:
    from hooks.overview_mode import get_study_mode
except Exception:
    def get_study_mode(_deck_id=None):
        return "qa"


def _on_reviewer_question(reviewer):
    """Inject Letter Gap JS khi hiện mặt trước thẻ + sync mode combo."""
    try:
        reviewer = _resolve_reviewer(reviewer)
        if reviewer is None:
            return
        reviewer._bento_forge_side = "question"
        card = reviewer.card
        if card is None:
            return
        snapshot = get_current_card_snapshot(reviewer, side="question")
        _refresh_companion_context(snapshot)
        q = card.q() or ""
        _inject_ai_action(reviewer)
        _inject_production_drill(reviewer, snapshot)
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
    reviewer = _resolve_reviewer(reviewer)
    if reviewer is None:
        return
    _inject_ai_action(reviewer)
    # Bước 1: Xác định tốc độ mặc định
    default_spd = 1.0
    snapshot = None
    try:
        reviewer._bento_forge_side = "answer"
        card = reviewer.card
        if card is not None:
            snapshot = get_current_card_snapshot(reviewer, side="answer")
            _refresh_companion_context(snapshot)
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
    _inject_example_regeneration(reviewer, snapshot)


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
