"""
Tests cho COMBO MODE (card gộp 5 chế độ → 1 card).

Kiểm tra:
- LANG_TEMPLATES có 1 cặp Combo + 4 hướng có điều kiện SRS Independent
- Template combo chứa thanh chọn mode (combo-mode-bar) + 5 panel (qa/vn/wb/pron/lg)
- CSS chứa style mode-btn / combo-check / combo-res
- Language config có field opt-in; mặc định blank vẫn chỉ sinh 1 card Combo
- _COMBO_MODE_JS tồn tại trong mode/shared.py
- hooks/overview_mode: build selector HTML, inject vào overview, set/get study mode
"""

import os
import sys
import types
from unittest.mock import MagicMock

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)


# ── Mock Anki (aqt) — chỉ cần gui_hooks + mw cho overview_mode ──────────────
aqt_mock = types.ModuleType("aqt")
aqt_mock.mw = MagicMock()
aqt_mock.mw.col = MagicMock()
aqt_mock.mw.col.conf = MagicMock()
aqt_mock.mw.col.conf.get = MagicMock(return_value="qa")
aqt_mock.mw.col.setMod = MagicMock()
aqt_mock.gui_hooks = MagicMock()
sys.modules["aqt"] = aqt_mock
sys.modules["aqt.mw"] = aqt_mock.mw


class TestComboTemplates:
    def test_lang_templates_have_conditional_srs_pairs(self):
        from mode import LANG_TEMPLATES
        # 5 cặp; 4 cặp phụ có Mustache opt-in nên Combo vẫn chỉ 1 card/từ.
        assert len(LANG_TEMPLATES["japanese"]) == 10
        assert len(LANG_TEMPLATES["chinese"]) == 10
        assert len(LANG_TEMPLATES["korean"]) == 10
        assert len(LANG_TEMPLATES["english"]) == 10

    def test_japanese_combo_question_has_mode_bar(self):
        from mode.templates import tmpl_ja_combo_q
        html = tmpl_ja_combo_q()
        assert 'id="combo-mode-bar"' in html
        assert 'id="mode-panel-qa"' in html
        assert 'id="mode-panel-vn"' in html
        assert 'id="mode-panel-wb"' in html
        assert 'id="mode-panel-pron"' in html
        assert 'id="mode-panel-lg"' in html
        assert "{{type:Meaning}}" in html
        assert "{{Front}}" in html
        assert "{{Meaning}}" in html
        assert 'data-srs-layout="combo"' in html
        assert 'data-srs-skill="recognition"' in html
        assert "1 lịch chung" in html

    def test_japanese_combo_answer_has_answer(self):
        from mode.templates import tmpl_ja_combo_a
        html = tmpl_ja_combo_a()
        assert 'id="combo-mode-bar"' in html
        assert "{{Furigana}}" in html
        assert "{{Meaning}}" in html

    def test_chinese_combo_question_has_mode_bar(self):
        from mode.templates import tmpl_zh_combo_q
        html = tmpl_zh_combo_q()
        assert 'id="combo-mode-bar"' in html
        assert 'id="mode-panel-qa"' in html
        assert "{{type:Meaning}}" in html
        assert "{{Pinyin}}" in html

    def test_chinese_combo_answer(self):
        from mode.templates import tmpl_zh_combo_a
        html = tmpl_zh_combo_a()
        assert 'id="combo-mode-bar"' in html
        assert "{{Pinyin}}" in html
        assert "{{Meaning}}" in html

    def test_korean_combo_question_has_mode_bar(self):
        from mode.templates import tmpl_ko_combo_q
        html = tmpl_ko_combo_q()
        assert 'id="combo-mode-bar"' in html
        assert 'id="mode-panel-qa"' in html
        assert 'id="mode-panel-vn"' in html
        assert 'id="mode-panel-wb"' in html
        assert 'id="mode-panel-pron"' in html
        assert 'id="mode-panel-lg"' in html
        assert "{{type:Meaning}}" in html
        assert "{{Romanization}}" in html
        assert "{{Front}}" in html
        assert "{{Meaning}}" in html

    def test_korean_combo_answer(self):
        from mode.templates import tmpl_ko_combo_a
        html = tmpl_ko_combo_a()
        assert 'id="combo-mode-bar"' in html
        assert "{{Romanization}}" in html
        assert "{{Meaning}}" in html

    def test_english_combo_contract(self):
        from mode.templates import tmpl_en_combo_q, tmpl_en_combo_a
        question = tmpl_en_combo_q()
        answer = tmpl_en_combo_a()
        for panel in ("qa", "vn", "wb", "pron", "lg"):
            assert f'id="mode-panel-{panel}"' in question
        assert "{{Pronunciation}}" in question
        assert "{{CEFR Level}}" in answer


class TestComboCss:
    def test_css_has_mode_styles(self):
        from mode.css import css_japanese, css_chinese
        for css in (css_japanese(), css_chinese()):
            assert ".mode-bar" in css
            assert ".mode-btn" in css
            assert ".combo-check" in css
            assert ".combo-res" in css


class TestComboJs:
    def test_combo_mode_js_exists(self):
        from mode.shared import _COMBO_MODE_JS
        assert "ai_factory_set_mode" in _COMBO_MODE_JS
        assert "localStorage" in _COMBO_MODE_JS
        assert "mode-panel-qa" in _COMBO_MODE_JS
        assert "if(independent) m='qa'" in _COMBO_MODE_JS
        assert "if(independent) return" in _COMBO_MODE_JS


class TestComboConfig:
    def test_template_names_and_opt_in_field(self):
        from Language import LANG_CONFIG
        from mode import LANG_TEMPLATES
        for lang in ("japanese", "chinese", "korean", "english"):
            assert len(LANG_CONFIG[lang]["template_names"]) == 5
            assert len(LANG_TEMPLATES[lang]) == 10
            assert "SRS Independent" in LANG_CONFIG[lang]["all_fields"]
            for template in LANG_TEMPLATES[lang][2:]:
                html = template()
                assert html.startswith("{{#SRS Independent}}")
                assert 'data-srs-layout="independent"' in html

    def test_independent_typed_recall_has_matching_answer_filter(self):
        from mode.templates import (
            tmpl_ja_vn_q, tmpl_ja_vn_a, tmpl_zh_vn_q, tmpl_zh_vn_a,
            tmpl_ko_vn_q, tmpl_ko_vn_a,
            tmpl_en_vn_q, tmpl_en_vn_a,
        )
        for question, answer in (
            (tmpl_ja_vn_q, tmpl_ja_vn_a),
            (tmpl_zh_vn_q, tmpl_zh_vn_a),
            (tmpl_ko_vn_q, tmpl_ko_vn_a),
            (tmpl_en_vn_q, tmpl_en_vn_a),
        ):
            assert "{{type:Front}}" in question()
            assert "{{type:Front}}" in answer()


class TestOverviewModeSelector:
    def test_set_and_get_study_mode(self):
        from unittest.mock import patch
        from hooks.overview_mode import get_study_mode, set_study_mode, CONF_KEY, MODES
        conf = {}
        mw_mock = MagicMock()
        mw_mock.col.conf = conf
        # set_study_mode với mode hợp lệ
        with patch("aqt.mw", mw_mock):
            assert set_study_mode("vn") is True
            # set với mode không hợp lệ → fallback qa
            conf[CONF_KEY] = "bad_mode"
            assert get_study_mode() == "qa"
            conf[CONF_KEY] = "pron"
            assert get_study_mode() == "pron"
        # set_study_mode với mode không hợp lệ → fallback qa + vẫn lưu
        with patch("aqt.mw", mw_mock):
            assert set_study_mode("unknown_mode") is True
            conf[CONF_KEY] = "unknown_mode"
            assert get_study_mode() == "qa"
        assert CONF_KEY == "ai_factory_study_mode"
        assert set(MODES) == {"qa", "vn", "wb", "pron", "lg"}

    def test_on_js_message_handles_mode(self):
        from unittest.mock import patch
        from hooks.overview_mode import _on_js_message
        with patch("hooks.overview_mode.set_study_mode") as set_mock:
            handled = _on_js_message((False, None), "ai_factory_set_mode:wb", None)
            set_mock.assert_called_once_with("wb", None)
            assert handled == (True, None)
        # message không phải của add-on → giữ nguyên handled
        result = _on_js_message((False, None), "onigiri_study", None)
        assert result == (False, None)

    def test_mode_and_srs_layout_are_stable_per_deck(self):
        from unittest.mock import patch
        from hooks.overview_mode import (
            get_srs_layout, get_study_mode, set_srs_layout, set_study_mode,
        )
        mw_mock = MagicMock()
        mw_mock.col.conf = {}
        with patch("aqt.mw", mw_mock):
            assert get_srs_layout(10) == "combo"
            assert set_study_mode("pron", 10) is True
            assert set_study_mode("vn", 20) is True
            assert set_srs_layout("independent", 10) is True
            assert get_study_mode(10) == "pron"
            assert get_study_mode(20) == "vn"
            assert get_srs_layout(10) == "independent"
            assert get_srs_layout(20) == "combo"

    def test_register_overview_hook_falls_back_when_api_is_missing(self):
        from unittest.mock import patch
        import hooks.overview_mode as overview_mode

        overview_mode._REGISTERED_HOOKS.clear()
        with patch.object(overview_mode, "gui_hooks", object()):
            assert overview_mode.register_overview_hooks() is False

    def test_register_overview_hook_is_idempotent(self):
        from unittest.mock import patch
        import hooks.overview_mode as overview_mode

        hook = MagicMock()
        hooks = types.SimpleNamespace(webview_did_receive_js_message=hook)
        overview_mode._REGISTERED_HOOKS.clear()
        with patch.object(overview_mode, "gui_hooks", hooks):
            assert overview_mode.register_overview_hooks() is True
            assert overview_mode.register_overview_hooks() is True
        hook.append.assert_called_once_with(overview_mode._on_js_message)


class TestReviewerHookCompatibility:
    def test_combo_uses_deck_default_but_independent_card_is_fixed(self):
        from unittest.mock import patch
        import hooks.reviewer as reviewer

        review = MagicMock()
        review.card.did = 42
        review.card.q.return_value = (
            '<div id="combo-mode-bar"></div><div data-srs-layout="combo"></div>'
        )
        with patch.object(reviewer, "get_study_mode", return_value="pron") as get_mode:
            reviewer._on_reviewer_question(review)
        get_mode.assert_called_once_with(42)
        assert "_aiFactoryMode='pron'" in review.web.eval.call_args[0][0]

        review.web.eval.reset_mock()
        review.card.q.return_value = (
            '<div id="combo-mode-bar"></div><div data-srs-layout="independent"></div>'
        )
        reviewer._on_reviewer_question(review)
        review.web.eval.assert_not_called()

    def test_missing_reviewer_hook_does_not_disable_available_hook(self):
        from unittest.mock import patch
        import hooks.reviewer as reviewer

        question_hook = MagicMock()
        hooks = types.SimpleNamespace(reviewer_did_show_question=question_hook)
        reviewer._REGISTERED_HOOKS.clear()
        with patch.object(reviewer, "gui_hooks", hooks):
            assert reviewer.register_hooks() is True
            assert reviewer.register_hooks() is True
        question_hook.append.assert_called_once_with(reviewer._on_reviewer_question)


