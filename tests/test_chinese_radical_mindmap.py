"""Regression contract for the Chinese radical mind-map review aid."""

import json

from Language.chinese import LANG_CONFIG
from mode.css import css_chinese
from mode.templates import LANG_TEMPLATES, tmpl_zh_combo_a, tmpl_zh_combo_q
from utils.i18n import t
from utils.prompts.chinese import _CHINESE_JSON_TEMPLATE, _CHINESE_JSON_TEMPLATE_EN


def test_chinese_ai_schema_and_field_map_include_structured_radicals():
    assert "Radical Mindmap" in LANG_CONFIG["all_fields"]
    assert LANG_CONFIG["json_field_map"]["radical_mindmap"] == "Radical Mindmap"
    for template in (_CHINESE_JSON_TEMPLATE, _CHINESE_JSON_TEMPLATE_EN):
        payload = json.loads(template)
        mindmap = payload["radical_mindmap"]
        assert isinstance(mindmap, dict)
        assert len(mindmap["characters"]) == 2
        assert all(item["components"] for item in mindmap["characters"])
        assert all(
            set(component) == {"glyph", "name"}
            for item in mindmap["characters"]
            for component in item["components"]
        )


def test_combo_card_has_toggle_clickable_characters_and_horizontal_three_slot_track():
    for html in (tmpl_zh_combo_q(), tmpl_zh_combo_a()):
        assert "{{#Radical Mindmap}}" in html
        assert t("radical_show") in html
        assert "radical-character" in html
        assert "scrollIntoView" in html
        assert "component.role" not in html
        assert "component.pinyin" not in html
        assert "data-radical-tooltip" in html
        assert "_bentoRadicalReady" in html
        assert "setTimeout(init,80)" in html
        assert "setTimeout(init,240)" in html
        assert "track.textContent=''" in html
        assert "data-radical-ready" not in html

    css = css_chinese()
    assert "grid-auto-flow:column" in css
    assert "grid-auto-columns:calc((100% - 24px)/3)" in css
    assert "overflow-x:auto" in css
    assert ".radical-component:hover .radical-tip" in css
    assert "text-decoration-style:dotted" in css
    assert ".radical-character:hover::after" in css


def test_every_chinese_vocab_template_references_the_optional_mindmap_field():
    assert all("{{#Radical Mindmap}}" in render() for render in LANG_TEMPLATES["chinese"])
