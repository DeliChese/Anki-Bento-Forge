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


def test_combo_card_has_whole_word_trigger_and_side_panel_with_three_slot_track():
    for html in (tmpl_zh_combo_q(), tmpl_zh_combo_a()):
        assert "{{#Radical Mindmap}}" in html
        assert t("radical_show") not in html
        assert "radical-toggle" not in html
        assert "classList.add('radical-word')" in html
        assert "hanzi[h].textContent=''" not in html
        assert "aria-haspopup','dialog" in html
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
    assert ".radical-word{position:relative;cursor:pointer;user-select:none" in css
    assert ".radical-word:hover::after" in css
    assert ".radical-panel{position:fixed" in css
    assert ".cw.bento-radical-host-right" in css


def test_every_chinese_vocab_template_references_the_optional_mindmap_field():
    assert all("{{#Radical Mindmap}}" in render() for render in LANG_TEMPLATES["chinese"])
