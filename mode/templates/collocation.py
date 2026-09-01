"""Compact two-direction templates for standalone chunks and idioms."""


def _front(direction: str) -> str:
    prompt = "Nhớ cụm tự nhiên" if direction == "recognition" else "Tạo lại cụm tự nhiên"
    value = "{{Front}}" if direction == "recognition" else "{{Meaning}}"
    return (
        '<div class="cw collocation-card"><div class="ch">'
        '<span class="badge">CHUNK</span><span class="topic">{{Phrase Type}} · {{Topic}}</span>'
        '</div><div class="vb"><div class="fql">' + prompt + '</div>'
        '<div class="hanzi">' + value + '</div></div></div>'
    )


def _back(direction: str, lang: str) -> str:
    answer = "{{Meaning}}" if direction == "recognition" else "{{Front}}"
    pronunciation_field = {
        "japanese": "Furigana", "chinese": "Pinyin",
        "korean": "Romanization", "english": "Pronunciation",
    }[lang]
    example_pronunciation = {
        "japanese": "", "chinese": " Pinyin",
        "korean": " Romanization", "english": "",
    }[lang]
    pronunciation = (
        f'{{{{#{pronunciation_field}}}}}<span class="sv">'
        f'{{{{{pronunciation_field}}}}}</span>{{{{/{pronunciation_field}}}}}'
    )
    example_1_pronunciation = (
        f'{{{{#Example{example_pronunciation}}}}}<div class="ep">'
        f'{{{{Example{example_pronunciation}}}}}</div>'
        f'{{{{/Example{example_pronunciation}}}}}'
        if example_pronunciation else ""
    )
    example_2_pronunciation = (
        f'{{{{#Example2{example_pronunciation}}}}}<div class="ep">'
        f'{{{{Example2{example_pronunciation}}}}}</div>'
        f'{{{{/Example2{example_pronunciation}}}}}'
        if example_pronunciation else ""
    )
    return (
        "{{FrontSide}}"
        '<div class="cw collocation-card"><div class="ir"><span class="mn">' + answer + '</span>'
        + pronunciation +
        '<span class="au">{{Vocab Audio}}</span></div>'
        '{{#Pattern / Slots}}<div class="es"><div class="esl">Khung / khe thay thế</div><div class="ec">{{Pattern / Slots}}</div></div>{{/Pattern / Slots}}'
        '{{#Register / Nuance}}<div class="es"><div class="esl">Sắc thái / mức độ</div><div class="ec">{{Register / Nuance}}</div></div>{{/Register / Nuance}}'
        '{{#Constraint}}<div class="es"><div class="esl">Ràng buộc / lỗi dễ mắc</div><div class="ec">{{Constraint}}</div></div>{{/Constraint}}'
        '{{#Source Word}}<div class="es"><div class="esl">Liên kết từ vựng</div><div class="ec">{{Source Word}}</div></div>{{/Source Word}}'
        '<div class="es"><div class="esl">Ngữ cảnh</div>'
        '{{#Example}}<div class="ec"><div class="en">VÍ DỤ 1</div><div class="ej">{{Example}}</div>'
        + example_1_pronunciation +
        '<div class="ev">{{Example in Vietnamese}}</div></div>{{/Example}}'
        '{{#Example2}}<div class="ec"><div class="en">VÍ DỤ 2</div><div class="ej">{{Example2}}</div>'
        + example_2_pronunciation +
        '<div class="ev">{{Example2 in Vietnamese}}</div></div>{{/Example2}}'
        '</div></div>'
    )


def collocation_templates_for(lang: str):
    """Return zero-argument Anki template callables for one target language."""
    return (
        lambda: _front("recognition"),
        lambda: _back("recognition", lang),
        lambda: _front("production"),
        lambda: _back("production", lang),
    )


COLLOCATION_TEMPLATES = collocation_templates_for("english")
