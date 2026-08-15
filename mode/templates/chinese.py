"""Chinese card templates.

This module owns the language-specific Anki Mustache/HTML templates.
"""

from ..shared import _WB_JS_BODY, WB_POOLS, _COMBO_MODE_JS
from .common import (
    _combo_answer_common_zh, _combo_data_block, _combo_mode_bar_chinese,
    _grammar_ai_panel, _srs_scope_banner,
)
def tmpl_zh_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '</div>'
    )


def tmpl_zh_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '<div class="ir">'
          '<span class="mn">{{Meaning}}</span>'
          '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
          '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
          '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
            '<div class="ej">{{Example}}</div>'
            '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
            '<div class="ea">{{Example Audio}}</div>'
            '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
          '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
            '<div class="ej">{{Example2}}</div>'
            '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
            '<div class="ea">{{Example2 Audio}}</div>'
            '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )


def tmpl_zh_vn_q():
    return (
        '<div class="fqw">'
        '<div class="fql">Từ vựng tiếng Trung là gì?</div>'
        '<div class="fqm">{{Meaning}}</div>'
        '<div style="margin-top:24px;font-size:15px;color:var(--muted);">'
          '<div class="typewrite">{{type:Front}}</div>'
        '</div></div>'
    )


def tmpl_zh_vn_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb">'
          '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
          '<div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
          '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Front}}</div></div>'
        '<div class="ir">'
          '<span class="mn">{{Meaning}}</span>'
          '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
          '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
          '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
            '<div class="ej">{{Example}}</div>'
            '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
            '<div class="ea">{{Example Audio}}</div>'
            '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
          '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
            '<div class="ej">{{Example2}}</div>'
            '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
            '<div class="ea">{{Example2 Audio}}</div>'
            '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )


def tmpl_zh_wb_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="wb-wrap">'
        '<div class="wb-meaning">{{Meaning}}</div>'
        '{{#Sino-Vietnamese}}<div class="wb-sub">{{Sino-Vietnamese}}</div>{{/Sino-Vietnamese}}'
        '<div class="wb-label">✍️ Ghép chữ thành từ tiếng Trung</div>'
        '<div class="wb-ans-area" id="wb-ans"></div>'
        '<div class="wb-bank-area" id="wb-bank"></div>'
        '<div class="wb-actions">'
        '<button class="wb-btn-clear" onclick="wbClear()">✕ Xóa</button>'
        '<button class="wb-btn-check" onclick="wbCheck()">✓ Kiểm tra</button>'
        '</div>'
        '<div class="wb-result" id="wb-result"></div>'
        '</div></div>'
        '<script>var _wbWord="{{Front}}",_wbPool=' + WB_POOLS["chinese"] + ';' + _WB_JS_BODY + '</script>'
    )


def tmpl_zh_wb_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
        '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div>'
        '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )


def tmpl_zh_pron_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb" style="padding-bottom:4px;">'
        '<div class="hanzi" style="margin-top:12px;">{{Front}}</div>'
        '<div style="font-size:13px;color:var(--muted);margin-top:8px;">{{Meaning}}</div>'
        '</div>'
        '<div class="pron-wrap">'
        '<div class="pron-lbl">Nhập Pinyin</div>'
        '<div class="az"><div class="typewrite">{{type:Pinyin}}</div></div>'
        '</div>'
        '</div>'
    )


def tmpl_zh_pron_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Pinyin}}</div></div>'
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
        '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '</div>'
    )


def tmpl_zh_lg_q():
    return (
        '<div id="lg-word-src" style="display:none">{{Front}}</div>'
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="lg-wrap">'
          '<span class="lg-diff-badge" id="lg-diff"></span>'
          '{{#Pinyin}}<div style="font-size:14px;color:var(--muted);margin-bottom:6px;">{{Pinyin}}</div>{{/Pinyin}}'
          '<div class="lg-display" id="lg-display"></div>'
          '<div class="lg-hint" id="lg-hint"></div>'
          '<div class="lg-clue">💡 Nghĩa: <b>{{Meaning}}</b></div>'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Front}}</div></div>'
        '</div>'
    )


def tmpl_zh_lg_a():
    return (
        '<div id="lg-word-src" style="display:none">{{Front}}</div>'
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az">{{type:Front}}</div>'
        '<div class="ir">'
          '<span class="mn">{{Meaning}}</span>'
          '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
          '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        '<div class="es"><div class="esl">Ví dụ</div>'
          '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
            '<div class="ej">{{Example}}</div>'
            '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
            '<div class="ea">{{Example Audio}}</div>'
            '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
          '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
            '<div class="ej">{{Example2}}</div>'
            '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
            '<div class="ea">{{Example2 Audio}}</div>'
            '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )


def tmpl_zh_g_q():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '{{#Pinyin}}<div class="pinyin">{{Pinyin}}</div>{{/Pinyin}}'
        '<div class="hanzi">{{Pattern}}</div>'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        + _grammar_ai_panel("chinese")
        + '</div>'
    )


def tmpl_zh_g_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '{{#Pinyin}}<div class="pinyin">{{Pinyin}}</div>{{/Pinyin}}'
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
        '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )


def tmpl_zh_g_rev_q():
    return (
        '<div class="fqw">'
        '<div class="fql">Cấu trúc ngữ pháp nào?</div>'
        '<div class="fqm">{{Meaning}}</div>'
        '{{#Usage}}<div class="wb-sub" style="margin-top:8px;">{{Usage}}</div>{{/Usage}}'
        '<div style="margin-top:24px;font-size:15px;color:var(--muted);">'
        '<div class="typewrite">{{type:Pinyin}}</div>'
        '</div></div>'
    )


def tmpl_zh_g_rev_a():
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">Ngữ pháp</span></div>'
        '<div class="vb">'
        '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
        '{{#Pinyin}}<div class="pinyin">{{Pinyin}}</div>{{/Pinyin}}'
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
        '{{#Example Pinyin}}<div class="ep">{{Example Pinyin}}</div>{{/Example Pinyin}}'
        '<div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div>'
        '{{#Example2 Pinyin}}<div class="ep">{{Example2 Pinyin}}</div>{{/Example2 Pinyin}}'
        '<div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )


def tmpl_zh_combo_q():
    """Front gộp 5 mode — Trung."""
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        + _srs_scope_banner()
        + _combo_mode_bar_chinese()
        + _combo_data_block(japanese=False)
        # Mode qa
        + '<div class="mode-panel" id="mode-panel-qa">'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az"><div class="typewrite">{{type:Meaning}}</div></div>'
        '</div>'
        # Mode vn
        + '<div class="mode-panel" id="mode-panel-vn" style="display:none">'
        '<div class="fqw"><div class="fql">Từ vựng tiếng Trung là gì?</div><div class="fqm">{{Meaning}}</div></div>'
        '<div class="combo-check">'
        '<input id="vn-input" type="text" placeholder="Gõ từ tiếng Trung..."/>'
        '<button id="vn-check" type="button">✓ Kiểm tra</button>'
        '</div>'
        '<div class="combo-res" id="vn-result"></div>'
        '</div>'
        # Mode wb
        + '<div class="mode-panel" id="mode-panel-wb" style="display:none">'
        '<div class="wb-wrap">'
        '<div class="wb-meaning">{{Meaning}}</div>'
        '{{#Sino-Vietnamese}}<div class="wb-sub">{{Sino-Vietnamese}}</div>{{/Sino-Vietnamese}}'
        '<div class="wb-label">✍️ Ghép chữ thành từ tiếng Trung</div>'
        '<div class="wb-ans-area" id="wb-ans"></div>'
        '<div class="wb-bank-area" id="wb-bank"></div>'
        '<div class="wb-actions">'
        '<button class="wb-btn-clear" onclick="wbClear()">✕ Xóa</button>'
        '<button class="wb-btn-check" onclick="wbCheck()">✓ Kiểm tra</button>'
        '</div>'
        '<div class="wb-result" id="wb-result"></div>'
        '</div>'
        '</div>'
        # Mode pron — Pinyin
        + '<div class="mode-panel" id="mode-panel-pron" style="display:none">'
        '<div class="vb" style="padding-bottom:4px;">'
        '<div class="hanzi" style="margin-top:12px;">{{Front}}</div>'
        '<div style="font-size:13px;color:var(--muted);margin-top:8px;">{{Meaning}}</div>'
        '</div>'
        '<div class="combo-check">'
        '<input id="pron-input" type="text" placeholder="Nhập Pinyin..."/>'
        '<button id="pron-check" type="button">✓ Kiểm tra</button>'
        '</div>'
        '<div class="combo-res" id="pron-result"></div>'
        '</div>'
        # Mode lg
        + '<div class="mode-panel" id="mode-panel-lg" style="display:none">'
        '<div id="lg-word-src" style="display:none">{{Front}}</div>'
        '<div class="lg-wrap">'
        '<span class="lg-diff-badge" id="lg-diff"></span>'
        '{{#Pinyin}}<div style="font-size:14px;color:var(--muted);margin-bottom:6px;">{{Pinyin}}</div>{{/Pinyin}}'
        '<div class="lg-display" id="lg-display"></div>'
        '<div class="lg-hint" id="lg-hint"></div>'
        '<div class="lg-clue">💡 Nghĩa: <b>{{Meaning}}</b></div>'
        '</div>'
        '</div>'
        + '<script>var _wbWord="{{Front}}",_wbPool=' + WB_POOLS["chinese"] + ';' + _WB_JS_BODY + '</script>'
        + '<script>' + _COMBO_MODE_JS + '</script>'
        + '</div>'
    )


def tmpl_zh_combo_a():
    """Back gộp 5 mode — Trung."""
    return (
        '<div class="cw">'
        '<div class="ch"><span class="badge">{{HSK Level}}</span><span class="topic">{{Topic}}</span></div>'
        + _srs_scope_banner()
        + _combo_mode_bar_chinese()
        + _combo_data_block(japanese=False)
        # Mode qa
        + '<div class="mode-panel" id="mode-panel-qa">'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        '<div class="az">{{type:Meaning}}</div>'
        + _combo_answer_common_zh()
        + '</div>'
        # Mode vn
        + '<div class="mode-panel" id="mode-panel-vn" style="display:none">'
        '<div class="vb">'
        '<div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Đáp án</div>'
        '<div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        + _combo_answer_common_zh()
        + '</div>'
        # Mode wb
        + '<div class="mode-panel" id="mode-panel-wb" style="display:none">'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        + _combo_answer_common_zh()
        + '</div>'
        # Mode pron
        + '<div class="mode-panel" id="mode-panel-pron" style="display:none">'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div></div>'
        '<div class="ir"><span class="mn">{{Pinyin}}</span><span class="au">{{Vocab Audio}}</span></div>'
        '</div>'
        # Mode lg
        + '<div class="mode-panel" id="mode-panel-lg" style="display:none">'
        '<div class="vb"><div class="pinyin">{{Pinyin}}</div><div class="hanzi">{{Front}}</div>'
        '{{#Traditional}}<div class="trad">Phồn thể: {{Traditional}}</div>{{/Traditional}}'
        '</div>'
        + _combo_answer_common_zh()
        + '</div>'
        + '<script>' + _COMBO_MODE_JS + '</script>'
        + '</div>'
    )
