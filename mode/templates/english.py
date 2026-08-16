"""English card templates."""

from ..shared import _WB_JS_BODY, WB_POOLS, _COMBO_MODE_JS
from .common import _grammar_ai_panel, _srs_scope_banner, _usage_guide_block


def _head(topic="{{Topic}}"):
    return f'<div class="ch"><span class="badge">{{{{CEFR Level}}}}</span><span class="topic">{topic}</span></div>'


def _word():
    return '<div class="vb"><div class="pinyin">{{Pronunciation}}</div><div class="hanzi">{{Front}}</div></div>'


def _mode_bar():
    return (
        '<div class="mode-bar" id="combo-mode-bar">'
        '<button class="mode-btn active" data-mode="qa">1. Anh→Việt</button>'
        '<button class="mode-btn" data-mode="vn">2. Việt→Anh</button>'
        '<button class="mode-btn" data-mode="wb">3. Ghép chữ</button>'
        '<button class="mode-btn" data-mode="pron">4. IPA</button>'
        '<button class="mode-btn" data-mode="lg">5. Ẩn chữ</button></div>'
    )


def _combo_data():
    return (
        '<div id="combo-data" style="display:none">'
        '<span id="combo-front">{{Front}}</span><span id="combo-meaning">{{Meaning}}</span>'
        '<span id="combo-pron">{{Pronunciation}}</span></div>'
    )


def _answer():
    return (
        '<div class="ir"><span class="mn">{{Meaning}}</span>'
        '<span class="au">{{Vocab Audio}}</span></div>'
        + _usage_guide_block()
        + '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div><div class="ej">{{Example}}</div>'
        '<div class="ea">{{Example Audio}}</div><div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div><div class="ej">{{Example2}}</div>'
        '<div class="ea">{{Example2 Audio}}</div><div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div>'
    )


def _wb_game():
    return (
        '<div class="wb-wrap"><div class="wb-meaning">{{Meaning}}</div>'
        '<div class="wb-label">✍️ Ghép chữ thành từ/cụm từ tiếng Anh</div>'
        '<div class="wb-ans-area" id="wb-ans"></div><div class="wb-bank-area" id="wb-bank"></div>'
        '<div class="wb-actions"><button class="wb-btn-clear" onclick="wbClear()">✕ Xóa</button>'
        '<button class="wb-btn-check" onclick="wbCheck()">✓ Kiểm tra</button></div>'
        '<div class="wb-result" id="wb-result"></div></div>'
    )


def tmpl_en_combo_q():
    return (
        '<div class="cw">' + _head() + _srs_scope_banner() + _mode_bar() + _combo_data()
        + '<div class="mode-panel" id="mode-panel-qa">' + _word()
        + '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div></div>'
        + '<div class="mode-panel" id="mode-panel-vn" style="display:none">'
        '<div class="fqw"><div class="fql">Từ/cụm từ tiếng Anh là gì?</div><div class="fqm">{{Meaning}}</div></div>'
        '<div class="combo-check"><input id="vn-input" type="text" placeholder="Gõ tiếng Anh..."/>'
        '<button id="vn-check" type="button">✓ Kiểm tra</button></div><div class="combo-res" id="vn-result"></div></div>'
        + '<div class="mode-panel" id="mode-panel-wb" style="display:none">' + _wb_game() + '</div>'
        + '<div class="mode-panel" id="mode-panel-pron" style="display:none">' + _word()
        + '<div class="combo-check"><input id="pron-input" type="text" placeholder="Nhập IPA..."/>'
        '<button id="pron-check" type="button">✓ Kiểm tra</button></div><div class="combo-res" id="pron-result"></div></div>'
        + '<div class="mode-panel" id="mode-panel-lg" style="display:none">'
        '<div id="lg-word-src" style="display:none">{{Front}}</div><div class="lg-wrap">'
        '<span class="lg-diff-badge" id="lg-diff"></span><div class="pinyin">{{Pronunciation}}</div>'
        '<div class="lg-display" id="lg-display"></div><div class="lg-hint" id="lg-hint"></div>'
        '<div class="lg-clue">💡 Nghĩa: <b>{{Meaning}}</b></div></div></div>'
        + '<script>var _wbWord="{{Front}}",_wbPool=' + WB_POOLS["english"] + ';' + _WB_JS_BODY + '</script>'
        + '<script>' + _COMBO_MODE_JS + '</script></div>'
    )


def tmpl_en_combo_a():
    return (
        '<div class="cw">' + _head() + _srs_scope_banner() + _mode_bar() + _combo_data()
        + '<div class="mode-panel" id="mode-panel-qa">' + _word()
        + '<div class="az">{{type:Meaning}}</div>' + _answer() + '</div>'
        + '<div class="mode-panel" id="mode-panel-vn" style="display:none">' + _word() + _answer() + '</div>'
        + '<div class="mode-panel" id="mode-panel-wb" style="display:none">' + _word() + _answer() + '</div>'
        + '<div class="mode-panel" id="mode-panel-pron" style="display:none">' + _word()
        + '<div class="ir"><span class="mn">{{Pronunciation}}</span><span class="au">{{Vocab Audio}}</span></div></div>'
        + '<div class="mode-panel" id="mode-panel-lg" style="display:none">' + _word() + _answer() + '</div>'
        + '<script>' + _COMBO_MODE_JS + '</script></div>'
    )


def tmpl_en_vn_q():
    return (
        '<div class="fqw"><div class="fql">Từ/cụm từ tiếng Anh là gì?</div><div class="fqm">{{Meaning}}</div>'
        '<div style="margin-top:24px"><div class="typewrite">{{type:Front}}</div></div></div>'
    )


def tmpl_en_vn_a():
    return '<div class="cw">' + _head() + _word() + '<div class="az">{{type:Front}}</div>' + _answer() + '</div>'


def tmpl_en_wb_q():
    return (
        '<div class="cw">' + _head() + _wb_game() + '</div>'
        '<script>var _wbWord="{{Front}}",_wbPool=' + WB_POOLS["english"] + ';' + _WB_JS_BODY + '</script>'
    )


def tmpl_en_wb_a():
    return '<div class="cw">' + _head() + _word() + _answer() + '</div>'


def tmpl_en_pron_q():
    return (
        '<div class="cw">' + _head() + _word()
        + '<div class="pron-wrap"><div class="pron-lbl">Nhập IPA</div>'
        '<div class="az"><div class="typewrite">{{type:Pronunciation}}</div></div></div></div>'
    )


def tmpl_en_pron_a():
    return (
        '<div class="cw">' + _head() + _word()
        + '<div class="az">{{type:Pronunciation}}</div><div class="ir"><span class="mn">{{Meaning}}</span>'
        '<span class="au">{{Vocab Audio}}</span></div></div>'
    )


def tmpl_en_lg_q():
    return (
        '<div id="lg-word-src" style="display:none">{{Front}}</div><div class="cw">' + _head()
        + '<div class="lg-wrap"><span class="lg-diff-badge" id="lg-diff"></span>'
        '<div class="pinyin">{{Pronunciation}}</div><div class="lg-display" id="lg-display"></div>'
        '<div class="lg-hint" id="lg-hint"></div><div class="lg-clue">💡 Nghĩa: <b>{{Meaning}}</b></div></div>'
        '<div class="az"><div class="typewrite">{{type:Front}}</div></div></div>'
    )


def tmpl_en_lg_a():
    return '<div class="cw">' + _head() + _word() + '<div class="az">{{type:Front}}</div>' + _answer() + '</div>'


def _grammar_answer():
    return (
        '<div class="ir"><span class="mn">{{Meaning}}</span>{{#Usage}}<span class="sv">{{Usage}}</span>{{/Usage}}</div>'
        '{{#Explanation}}<div class="es"><div class="esl">Cách dùng</div><div class="ec">'
        '<div class="ev" style="font-style:normal;color:var(--text)">{{Explanation}}</div></div></div>{{/Explanation}}'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div><div class="ej">{{Example}}</div>'
        '<div class="ea">{{Example Audio}}</div><div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div><div class="ej">{{Example2}}</div>'
        '<div class="ea">{{Example2 Audio}}</div><div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}</div>'
    )


def _pattern():
    return '<div class="vb"><div class="pinyin">{{Pronunciation}}</div><div class="hanzi">{{Pattern}}</div></div>'


def tmpl_en_g_q():
    return (
        '<div class="cw">' + _head("Ngữ pháp") + _pattern()
        + '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        + _grammar_ai_panel("english") + '</div>'
    )


def tmpl_en_g_a():
    return (
        '<div class="cw">' + _head("Ngữ pháp") + _pattern()
        + '<div class="az">{{type:Meaning}}</div>' + _grammar_answer() + '</div>'
    )


def tmpl_en_g_rev_q():
    return (
        '<div class="fqw"><div class="fql">Cấu trúc ngữ pháp nào?</div><div class="fqm">{{Meaning}}</div>'
        '{{#Usage}}<div class="wb-sub" style="margin-top:8px">{{Usage}}</div>{{/Usage}}'
        '<div style="margin-top:24px"><div class="typewrite">{{type:Pattern}}</div></div></div>'
    )


def tmpl_en_g_rev_a():
    return (
        '<div class="cw">' + _head("Ngữ pháp") + _pattern()
        + '<div class="az">{{type:Pattern}}</div>' + _grammar_answer() + '</div>'
    )
