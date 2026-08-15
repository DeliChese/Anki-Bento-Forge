"""Korean card templates.

This module owns the language-specific Anki Mustache/HTML templates.
"""

from ..shared import _WB_JS_BODY, WB_POOLS, _COMBO_MODE_JS
from .common import _grammar_ai_panel, _srs_scope_banner
def _combo_mode_bar_korean():
    return (
        '<div class="mode-bar" id="combo-mode-bar">'
        '<button class="mode-btn active" data-mode="qa">1. Hàn→Việt</button>'
        '<button class="mode-btn" data-mode="vn">2. Việt→Hàn</button>'
        '<button class="mode-btn" data-mode="wb">3. Ghép chữ</button>'
        '<button class="mode-btn" data-mode="pron">4. Romanization</button>'
        '<button class="mode-btn" data-mode="lg">5. Ẩn chữ</button>'
        '</div>'
    )


def _combo_data_block_korean():
    """Dữ liệu ẩn cho JS combo — pron = Romanization."""
    return (
        '<div id="combo-data" style="display:none">'
        '<span id="combo-front">{{Front}}</span>'
        '<span id="combo-meaning">{{Meaning}}</span>'
        '<span id="combo-pron">{{Romanization}}</span>'
        '</div>'
    )


def _combo_answer_common_ko():
    """Đáp án đầy đủ tiếng Hàn (dùng trong back)."""
    return (
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
        '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div>'
        '{{#Example Romanization}}<div class="ep">{{Example Romanization}}</div>{{/Example Romanization}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Romanization}}<div class="ep">{{Example2 Romanization}}</div>{{/Example2 Romanization}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div>'
    )


def tmpl_ko_combo_q():
    """Front gộp 5 mode — Hàn."""
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{TOPIK Level}}</span><span class="topic">{{Topic}}</span></div>'
        + _srs_scope_banner()
        + _combo_mode_bar_korean()
        + _combo_data_block_korean()
        # Mode qa — Hàn→Việt (type answer chuẩn Anki)
        + '<div class="mode-panel" id="mode-panel-qa">'
        '<div class="vb"><div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '</div>'
        # Mode vn — Việt→Hàn (tự kiểm tra bằng JS)
        + '<div class="mode-panel" id="mode-panel-vn" style="display:none">'
        '<div class="fqw"><div class="fql">Từ vựng tiếng Hàn là gì?</div><div class="fqm">{{Meaning}}</div></div>'
        '<div class="combo-check">'
        '<input id="vn-input" type="text" placeholder="Gõ từ tiếng Hàn..."/>'
        '<button id="vn-check" type="button">✓ Kiểm tra</button>'
        '</div>'
        '<div class="combo-res" id="vn-result"></div>'
        '</div>'
        # Mode wb — Ghép chữ
        + '<div class="mode-panel" id="mode-panel-wb" style="display:none">'
        '<div class="wb-wrap">'
        '<div class="wb-meaning">{{Meaning}}</div>'
        '{{#Sino-Vietnamese}}<div class="wb-sub">{{Sino-Vietnamese}}</div>{{/Sino-Vietnamese}}'
        '<div class="wb-label">✍️ Ghép chữ thành từ tiếng Hàn</div>'
        '<div class="wb-ans-area" id="wb-ans"></div>'
        '<div class="wb-bank-area" id="wb-bank"></div>'
        '<div class="wb-actions">'
        '<button class="wb-btn-clear" onclick="wbClear()">✕ Xóa</button>'
        '<button class="wb-btn-check" onclick="wbCheck()">✓ Kiểm tra</button>'
        '</div>'
        '<div class="wb-result" id="wb-result"></div>'
        '</div>'
        '</div>'
        # Mode pron — Romanization (tự kiểm tra bằng JS)
        + '<div class="mode-panel" id="mode-panel-pron" style="display:none">'
        '<div class="vb" style="padding-bottom:4px;">'
        '<div class="hanzi" style="margin-top:12px;">{{Front}}</div>'
        '<div style="font-size:13px;color:var(--muted);margin-top:8px;">{{Meaning}}</div>'
        '</div>'
        '<div class="combo-check">'
        '<input id="pron-input" type="text" placeholder="Nhập Romanization..."/>'
        '<button id="pron-check" type="button">✓ Kiểm tra</button>'
        '</div>'
        '<div class="combo-res" id="pron-result"></div>'
        '</div>'
        # Mode lg — Ẩn chữ
        + '<div class="mode-panel" id="mode-panel-lg" style="display:none">'
        '<div id="lg-word-src" style="display:none">{{Front}}</div>'
        '<div class="lg-wrap">'
        '<span class="lg-diff-badge" id="lg-diff"></span>'
        '{{#Romanization}}<div style="font-size:14px;color:var(--muted);margin-bottom:6px;">{{Romanization}}</div>{{/Romanization}}'
        '<div class="lg-display" id="lg-display"></div>'
        '<div class="lg-hint" id="lg-hint"></div>'
        '<div class="lg-clue">💡 Nghĩa: <b>{{Meaning}}</b></div>'
        '</div>'
        '</div>'
        + '<script>var _wbWord="{{Front}}",_wbPool=' + WB_POOLS["korean"] + ';' + _WB_JS_BODY + '</script>'
        + '<script>' + _COMBO_MODE_JS + '</script>'
        + '</div>'
    )


def tmpl_ko_combo_a():
    """Back gộp 5 mode — Hàn."""
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{TOPIK Level}}</span><span class="topic">{{Topic}}</span></div>'
        + _srs_scope_banner()
        + _combo_mode_bar_korean()
        + _combo_data_block_korean()
        # Mode qa
        + '<div class="mode-panel" id="mode-panel-qa">'
        '<div class="vb"><div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        '<div class="az">{{type:Meaning}}</div>'
        + _combo_answer_common_ko()
        + '</div>'
        # Mode vn
        + '<div class="mode-panel" id="mode-panel-vn" style="display:none">'
        '<div class="vb">'
        '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
        '<div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div>'
        '</div>'
        + _combo_answer_common_ko()
        + '</div>'
        # Mode wb
        + '<div class="mode-panel" id="mode-panel-wb" style="display:none">'
        '<div class="vb"><div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        + _combo_answer_common_ko()
        + '</div>'
        # Mode pron
        + '<div class="mode-panel" id="mode-panel-pron" style="display:none">'
        '<div class="vb"><div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        '<div class="ir"><span class="mn">{{Romanization}}</span><span class="au">{{Vocab Audio}}</span></div>'
        '</div>'
        # Mode lg
        + '<div class="mode-panel" id="mode-panel-lg" style="display:none">'
        '<div class="vb"><div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        + _combo_answer_common_ko()
        + '</div>'
        + '<script>' + _COMBO_MODE_JS + '</script>'
        + '</div>'
    )


def tmpl_ko_vn_q():
    return (
        '<div class="fqw"><div class="fql">Từ vựng tiếng Hàn là gì?</div>'
        '<div class="fqm">{{Meaning}}</div>'
        '<div style="margin-top:24px;font-size:15px;color:var(--muted);">'
        '<div class="typewrite">{{type:Front}}</div></div></div>'
    )


def tmpl_ko_vn_a():
    return (
        '<div class="cw"><div class="ch"><span class="badge">{{TOPIK Level}}</span>'
        '<span class="topic">{{Topic}}</span></div><div class="vb">'
        '<div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        '<div class="az"><div class="typewrite">{{type:Front}}</div></div>'
        + _combo_answer_common_ko() + '</div>'
    )


def tmpl_ko_wb_q():
    return (
        '<div class="cw"><div class="ch"><span class="badge">{{TOPIK Level}}</span>'
        '<span class="topic">{{Topic}}</span></div><div class="wb-wrap">'
        '<div class="wb-meaning">{{Meaning}}</div>'
        '{{#Sino-Vietnamese}}<div class="wb-sub">{{Sino-Vietnamese}}</div>{{/Sino-Vietnamese}}'
        '<div class="wb-label">✍️ Ghép chữ thành từ tiếng Hàn</div>'
        '<div class="wb-ans-area" id="wb-ans"></div><div class="wb-bank-area" id="wb-bank"></div>'
        '<div class="wb-actions"><button class="wb-btn-clear" onclick="wbClear()">✕ Xóa</button>'
        '<button class="wb-btn-check" onclick="wbCheck()">✓ Kiểm tra</button></div>'
        '<div class="wb-result" id="wb-result"></div></div></div>'
        '<script>var _wbWord="{{Front}}",_wbPool=' + WB_POOLS["korean"] + ';' + _WB_JS_BODY + '</script>'
    )


def tmpl_ko_wb_a():
    return (
        '<div class="cw"><div class="ch"><span class="badge">{{TOPIK Level}}</span>'
        '<span class="topic">{{Topic}}</span></div><div class="vb">'
        '<div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        + _combo_answer_common_ko() + '</div>'
    )


def tmpl_ko_pron_q():
    return (
        '<div class="cw"><div class="ch"><span class="badge">{{TOPIK Level}}</span>'
        '<span class="topic">{{Topic}}</span></div><div class="vb" style="padding-bottom:4px;">'
        '<div class="hanzi" style="margin-top:12px;">{{Front}}</div>'
        '<div style="font-size:13px;color:var(--muted);margin-top:8px;">{{Meaning}}</div></div>'
        '<div class="pron-wrap"><div class="pron-lbl">Nhập Romanization</div>'
        '<div class="az"><div class="typewrite">{{type:Romanization}}</div></div></div></div>'
    )


def tmpl_ko_pron_a():
    return (
        '<div class="cw"><div class="ch"><span class="badge">{{TOPIK Level}}</span>'
        '<span class="topic">{{Topic}}</span></div><div class="vb">'
        '<div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        '<div class="az"><div class="typewrite">{{type:Romanization}}</div></div>'
        '<div class="ir"><span class="mn">{{Meaning}}</span>'
        '<span class="au">{{Vocab Audio}}</span></div></div>'
    )


def tmpl_ko_lg_q():
    return (
        '<div id="lg-word-src" style="display:none">{{Front}}</div><div class="cw">'
        '<div class="ch"><span class="badge">{{TOPIK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="lg-wrap"><span class="lg-diff-badge" id="lg-diff"></span>'
        '{{#Romanization}}<div style="font-size:14px;color:var(--muted);margin-bottom:6px;">'
        '{{Romanization}}</div>{{/Romanization}}<div class="lg-display" id="lg-display"></div>'
        '<div class="lg-hint" id="lg-hint"></div><div class="lg-clue">💡 Nghĩa: <b>{{Meaning}}</b></div></div>'
        '<div class="az"><div class="typewrite">{{type:Front}}</div></div></div>'
    )


def tmpl_ko_lg_a():
    return (
        '<div id="lg-word-src" style="display:none">{{Front}}</div><div class="cw">'
        '<div class="ch"><span class="badge">{{TOPIK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="pinyin">{{Romanization}}</div><div class="hanzi">{{Front}}</div></div>'
        '<div class="az">{{type:Front}}</div>' + _combo_answer_common_ko() + '</div>'
    )


def tmpl_ko_g_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{TOPIK Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '{{#Romanization}}<div class="pinyin">{{Romanization}}</div>{{/Romanization}}'
        '<div class="hanzi">{{Pattern}}</div>'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        + _grammar_ai_panel("korean")
        + '</div>'
    )


def tmpl_ko_g_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{TOPIK Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '{{#Romanization}}<div class="pinyin">{{Romanization}}</div>{{/Romanization}}'
        '<div class="hanzi">{{Pattern}}</div>'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Usage}}<span class="sv">{{Usage}}</span>{{/Usage}}'
        '</div>'
        '{{#Explanation}}<div class="es"><div class="esl">Cách dùng</div>'
        '<div class="ec"><div class="ev" style="font-style:normal;color:var(--text);">{{Explanation}}</div></div>'
        '</div>{{/Explanation}}'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div>'
        '{{#Example Romanization}}<div class="ep">{{Example Romanization}}</div>{{/Example Romanization}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Romanization}}<div class="ep">{{Example2 Romanization}}</div>{{/Example2 Romanization}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )


def tmpl_ko_g_rev_q():
    return (
        '<div class="fqw">'
        '<div class="fql">Cấu trúc ngữ pháp nào?</div>'
        '<div class="fqm">{{Meaning}}</div>'
        '{{#Usage}}<div class="wb-sub" style="margin-top:8px;">{{Usage}}</div>{{/Usage}}'
        '<div style="margin-top:24px;font-size:15px;color:var(--muted);">'
        '<div class="typewrite">{{type:Romanization}}</div>'
        '</div></div>'
    )


def tmpl_ko_g_rev_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{TOPIK Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
        '{{#Romanization}}<div class="pinyin">{{Romanization}}</div>{{/Romanization}}'
        '<div class="hanzi">{{Pattern}}</div>'
        '</div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Usage}}<span class="sv">{{Usage}}</span>{{/Usage}}'
        '</div>'
        '{{#Explanation}}<div class="es"><div class="esl">Cách dùng</div>'
        '<div class="ec"><div class="ev" style="font-style:normal;color:var(--text);">{{Explanation}}</div></div>'
        '</div>{{/Explanation}}'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div>'
        '{{#Example Romanization}}<div class="ep">{{Example Romanization}}</div>{{/Example Romanization}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Romanization}}<div class="ep">{{Example2 Romanization}}</div>{{/Example2 Romanization}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )
