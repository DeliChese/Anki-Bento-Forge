"""Shared template helpers card templates.

This module owns the language-specific Anki Mustache/HTML templates.
"""

from ..shared import _GRAMMAR_AI_JS


def _usage_guide_block() -> str:
    """Optional Usage Guide V1 content, visible on answer sides only."""
    return (
        '{{#Usage Pattern}}<div class="es usage-guide"><div class="esl">Mẫu dùng</div>'
        '<div class="ec"><div class="ev" style="font-style:normal;color:var(--text);">'
        '{{Usage Pattern}}</div></div></div>{{/Usage Pattern}}'
        '{{#Usage Note}}<div class="es usage-guide"><div class="esl">Lưu ý dùng</div>'
        '<div class="ec"><div class="ev" style="font-style:normal;color:var(--text);">'
        '{{Usage Note}}</div></div></div>{{/Usage Note}}'
        '{{#Collocation}}<div class="es usage-guide"><div class="esl">Cụm đi kèm</div>'
        '<div class="ec"><div class="ev" style="font-style:normal;color:var(--text);">'
        '{{Collocation}}</div></div></div>{{/Collocation}}'
    )


def _grammar_ai_panel(lang: str) -> str:
    """Panel 'Luyện dịch AI' cho thẻ ngữ pháp — AI sinh câu (streaming) + tự chấm điểm."""
    return (
        '<div class="ga-box" id="ga-box" '
        'data-pattern="{{Pattern}}" data-meaning="{{Meaning}}" data-lang="' + lang + '">'
        '<div class="ga-head">🤖 Luyện dịch AI (ngữ pháp)</div>'
        '<div class="ga-status" id="ga-status">Bấm nút để AI sinh câu áp dụng cấu trúc</div>'
        '<div class="ga-sentence" id="ga-sentence"></div>'
        '<button class="ga-btn" id="ga-ask">✨ AI sinh câu</button>'
        '<input class="ga-input" id="ga-input" placeholder="Gõ bản dịch tiếng Việt..." style="display:none;">'
        '<button class="ga-btn" id="ga-check" style="display:none;">✓ Chấm điểm</button>'
        '<div class="combo-res" id="ga-result" style="display:none;"></div>'
        '</div>'
        + _GRAMMAR_AI_JS
    )


def _srs_scope_banner():
    """Explain exactly which memory signal the current card updates."""
    return (
        '{{^SRS Independent}}'
        '<div class="srs-scope" data-srs-layout="combo">'
        'Luyện Combo · 1 lịch chung — đổi bài tập không tạo lịch SRS riêng.'
        '</div>{{/SRS Independent}}'
        '{{#SRS Independent}}'
        '<div class="srs-scope srs-independent" data-srs-layout="independent" '
        'data-srs-skill="recognition">'
        'SRS độc lập · Nhận diện — lần chấm này chỉ cập nhật lịch Nhận diện.'
        '</div>{{/SRS Independent}}'
    )


def _independent_template(template, skill, label):
    """Wrap a legacy direction so it only generates for independent notes."""
    def render():
        return (
            '{{#SRS Independent}}'
            f'<div class="srs-scope srs-independent" data-srs-layout="independent" '
            f'data-srs-skill="{skill}">SRS độc lập · {label} — '
            f'lần chấm này chỉ cập nhật lịch {label}.</div>'
            + template()
            + '{{/SRS Independent}}'
        )
    return render


def _combo_mode_bar_japanese():
    return (
        '<div class="mode-bar" id="combo-mode-bar">'
        '<button class="mode-btn active" data-mode="qa">1. Nhật→Việt</button>'
        '<button class="mode-btn" data-mode="vn">2. Việt→Nhật</button>'
        '<button class="mode-btn" data-mode="wb">3. Ghép chữ</button>'
        '<button class="mode-btn" data-mode="pron">4. Furigana</button>'
        '<button class="mode-btn" data-mode="lg">5. Ẩn chữ</button>'
        '</div>'
    )


def _combo_mode_bar_chinese():
    return (
        '<div class="mode-bar" id="combo-mode-bar">'
        '<button class="mode-btn active" data-mode="qa">1. Trung→Việt</button>'
        '<button class="mode-btn" data-mode="vn">2. Việt→Trung</button>'
        '<button class="mode-btn" data-mode="wb">3. Ghép chữ</button>'
        '<button class="mode-btn" data-mode="pron">4. Pinyin</button>'
        '<button class="mode-btn" data-mode="lg">5. Ẩn chữ</button>'
        '</div>'
    )


def _combo_data_block(japanese=True):
    if japanese:
        return (
            '<div id="combo-data" style="display:none">'
            '<span id="combo-front">{{Front}}</span>'
            '<span id="combo-meaning">{{Meaning}}</span>'
            '<span id="combo-pron">{{Furigana}}</span>'
            '</div>'
        )
    return (
        '<div id="combo-data" style="display:none">'
        '<span id="combo-front">{{Front}}</span>'
        '<span id="combo-meaning">{{Meaning}}</span>'
        '<span id="combo-pron">{{Pinyin}}</span>'
        '</div>'
    )


def _combo_answer_common():
    """Đáp án đầy đủ dùng chung (hiển thị trong back)."""
    return (
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
        '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        + _usage_guide_block()
        + '<div class="es"><div class="esl">Ví dụ</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div>'
        '<div class="ej">{{Example}}</div><div class="ea">{{Example Audio}}</div>'
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div>'
        '<div class="ej">{{Example2}}</div><div class="ea">{{Example2 Audio}}</div>'
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div>'
    )


def _combo_answer_common_zh():
    """Đáp án đầy đủ tiếng Trung (dùng trong back)."""
    return (
        '<div class="ir">'
        '<span class="mn">{{Meaning}}</span>'
        '{{#Sino-Vietnamese}}<span class="sv">{{Sino-Vietnamese}}</span>{{/Sino-Vietnamese}}'
        '<span class="au">{{Vocab Audio}}</span>'
        '</div>'
        + _usage_guide_block()
        + '<div class="es"><div class="esl">Ví dụ</div>'
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
        '</div>'
    )
