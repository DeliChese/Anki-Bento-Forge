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

    def test_css_has_responsive_reading_guards(self):
        from mode.css import css_japanese, css_chinese, css_english, css_korean
        for css in (css_japanese(), css_chinese(), css_korean(), css_english()):
            assert "max-width:680px" in css
            assert "overflow-wrap:anywhere" in css
            assert "@media (max-width:520px)" in css
            assert ".typeGood" in css


class TestComboJs:
    def test_combo_mode_js_exists(self):
        from mode.shared import _COMBO_MODE_JS
        assert "ai_factory_set_mode" in _COMBO_MODE_JS
        assert "localStorage" in _COMBO_MODE_JS
        assert "mode-panel-qa" in _COMBO_MODE_JS
        assert "if(independent) m='qa'" in _COMBO_MODE_JS
        assert "if(independent) return" in _COMBO_MODE_JS

    def test_reading_toggle_is_added_to_every_review_template_without_new_fields(self):
        from mode import LANG_COLLOCATION_TEMPLATES, LANG_GRAMMAR_TEMPLATES, LANG_TEMPLATES
        from mode.shared import _EXAMPLE_READING_TOGGLE_JS

        assert "ai_factory_example_readings_hidden" in _EXAMPLE_READING_TOGGLE_JS
        assert "Ẩn cách đọc" in _EXAMPLE_READING_TOGGLE_JS
        for registry in (LANG_TEMPLATES, LANG_GRAMMAR_TEMPLATES, LANG_COLLOCATION_TEMPLATES):
            for templates in registry.values():
                assert all("ai_factory_example_readings_hidden" in template() for template in templates)

    def test_independent_templates_keep_toggle_inside_srs_conditional(self):
        from mode import LANG_TEMPLATES

        for templates in LANG_TEMPLATES.values():
            for template in templates[2:]:
                html = template()
                assert html.startswith("{{#SRS Independent}}")
                assert html.rfind("ai_factory_example_readings_hidden") < html.rfind("{{/SRS Independent}}")


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

    def test_on_js_message_opens_ai_only_after_explicit_reviewer_action(self):
        from unittest.mock import patch
        from hooks.overview_mode import _on_js_message
        with patch("hooks.reviewer.open_companion_from_reviewer") as open_ai:
            context = MagicMock()
            assert _on_js_message((False, None), "bento_forge_ai:open", context) == (True, None)
            open_ai.assert_called_once_with(context)

    def test_on_js_message_opens_requested_example_slot(self):
        from unittest.mock import patch
        from hooks.overview_mode import _on_js_message
        with patch("hooks.reviewer.open_example_regenerator_from_reviewer") as open_example:
            context = MagicMock()
            assert _on_js_message(
                (False, None), "bento_example:open:3", context,
            ) == (True, None)
            open_example.assert_called_once_with(context, 3)

        assert _on_js_message(
            (False, None), "bento_example:open:9", context,
        ) == (False, None)

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
    def test_native_card_hook_resolves_active_reviewer_for_example_actions(self):
        from unittest.mock import patch
        import hooks.reviewer as reviewer

        review = MagicMock()
        review.card.id = 9
        hook_card = types.SimpleNamespace(id=9)
        snapshot = {"language": "english", "note_id": 42}
        with patch("aqt.mw", MagicMock(reviewer=review)), patch.object(
            reviewer, "_inject_ai_action"
        ) as inject_ai, patch.object(
            reviewer, "get_current_card_snapshot", return_value=snapshot
        ), patch.object(
            reviewer, "_inject_example_regeneration"
        ) as inject_examples:
            reviewer._on_reviewer_answer(hook_card)

        inject_ai.assert_called_once_with(review)
        inject_examples.assert_called_once_with(review, snapshot)
        review.web.eval.assert_not_called()

    def test_example_actions_retry_after_answer_render_and_survive_missing_history(self):
        from unittest.mock import patch
        import hooks.reviewer as reviewer

        review = MagicMock()
        with patch.object(reviewer, "_example_review_payload", return_value=None):
            assert reviewer._inject_example_regeneration(
                review, {"language": "japanese"},
            ) is True

        script = review.web.eval.call_args.args[0]
        assert "const render = ()" in script
        assert "setTimeout(render, 80)" in script
        assert "setTimeout(render, 240)" in script
        assert "match(/([1-4])" in script
        assert "bento-example-placeholder" not in script

    def test_production_drill_is_opt_in_local_and_hides_guidance(self):
        import hooks.reviewer as reviewer

        review = MagicMock()
        snapshot = {
            "current_target": "affect",
            "usage_pattern": "affect + object",
            "collocation": "directly affect",
            "example": "Weather directly affects demand.",
        }

        assert reviewer._inject_production_drill(review, snapshot) is True

        script = review.web.eval.call_args[0][0]
        assert "bento-production-drill-action" in script
        assert "panel.hidden = true" in script
        assert "guide.hidden = true" in script
        assert "draft.focus()" in script
        assert "affect + object" in script
        assert "directly affect" in script
        assert "pycmd(" not in script
        assert "showAnswer" not in script
        assert "mw.col" not in script

    def test_production_drill_requires_target_and_usage_guide(self):
        import hooks.reviewer as reviewer

        review = MagicMock()
        assert reviewer._inject_production_drill(
            review, {"current_target": "affect"},
        ) is False
        assert reviewer._inject_production_drill(
            review, {"usage_pattern": "affect + object"},
        ) is False
        review.web.eval.assert_not_called()

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
        assert not any(
            "_aiFactoryMode" in call.args[0]
            for call in review.web.eval.call_args_list
        )

    def test_reviewer_snapshot_is_minimal_side_aware_and_read_only(self):
        import hooks.reviewer as reviewer

        review = MagicMock()
        review._bento_forge_side = "question"
        review.card.id = 9
        review.card.did = 42
        note = MagicMock()
        note.model.return_value = {"name": "AnkiTool English V17.0 (Add-on)"}
        note.items.return_value = [
            ("Front", "affect"), ("Meaning", "ảnh hưởng"),
            ("Usage Pattern", "affect + object"), ("Private Field", "omit me"),
        ]
        review.card.note.return_value = note

        snapshot = reviewer.get_current_card_snapshot(review)
        assert snapshot["language"] == "english"
        assert snapshot["side"] == "question"
        assert snapshot["front"] == "affect"
        assert snapshot["current_target"] == "affect"
        assert snapshot["card_kind"] == "vocabulary"
        assert snapshot["meaning"] == "ảnh hưởng"
        assert snapshot["usage_pattern"] == "affect + object"
        assert "private_field" not in snapshot

    def test_reviewer_snapshot_maps_custom_chinese_vocabulary_target(self):
        import hooks.reviewer as reviewer

        review = MagicMock()
        review.card.id = 10
        review.card.did = 43
        note = MagicMock()
        note.model.return_value = {"name": "AnkiTool Chinese V18.3 (Add-on)"}
        note.items.return_value = [
            ("Hanzi", "水果"), ("Pinyin", "shuǐguǒ"),
            ("Meaning", "hoa quả"), ("Private Field", "omit me"),
        ]
        review.card.note.return_value = note

        snapshot = reviewer.get_current_card_snapshot(review, side="question")

        assert snapshot["language"] == "chinese"
        assert snapshot["front"] == "水果"
        assert snapshot["current_target"] == "水果"
        assert snapshot["card_kind"] == "vocabulary"
        assert snapshot["pinyin"] == "shuǐguǒ"
        assert snapshot["meaning"] == "hoa quả"
        assert "private_field" not in snapshot

    def test_reviewer_snapshot_maps_collocation_target_for_quality_upgrade(self):
        import hooks.reviewer as reviewer

        review = MagicMock()
        note = MagicMock()
        note.model.return_value = {"name": "AnkiTool English Collocation V18.3 (Add-on)"}
        note.items.return_value = [("Chunk", "take responsibility"), ("Meaning", "chịu trách nhiệm")]
        review.card.note.return_value = note

        snapshot = reviewer.get_current_card_snapshot(review, side="question")

        assert snapshot["card_kind"] == "collocation"
        assert snapshot["current_target"] == "take responsibility"

    def test_reviewer_snapshot_maps_grammar_target_and_supporting_fields(self):
        import hooks.reviewer as reviewer

        review = MagicMock()
        review.card.id = 11
        review.card.did = 44
        note = MagicMock()
        note.model.return_value = {"name": "AnkiTool Japanese Grammar V18.3 (Add-on)"}
        note.items.return_value = [
            ("Pattern", "～わけではない"), ("Furigana", "～わけではない"),
            ("Meaning", "không hẳn là"), ("JLPT Level", "N3"),
            ("Topic", "phủ định một phần"), ("Usage", "V + わけではない"),
            ("Explanation", "Phủ định một kết luận tuyệt đối."),
            ("Example", "嫌いなわけではない。"),
            ("Example Romanization", "kirai na wake dewa nai"),
            ("Example in Vietnamese", "Không phải là tôi ghét."),
        ]
        review.card.note.return_value = note

        snapshot = reviewer.get_current_card_snapshot(review, side="answer")

        assert snapshot["language"] == "japanese"
        assert snapshot["pattern"] == "～わけではない"
        assert snapshot["current_target"] == "～わけではない"
        assert snapshot["card_kind"] == "grammar"
        assert snapshot["level"] == "N3"
        assert snapshot["topic"] == "phủ định một phần"
        assert snapshot["usage"] == "V + わけではない"
        assert snapshot["example_romanization"] == "kirai na wake dewa nai"

    def test_reviewer_snapshot_maps_explicit_custom_target_alias_only(self):
        import hooks.reviewer as reviewer

        review = MagicMock()
        note = MagicMock()
        note.model.return_value = {"name": "My Chinese Custom Notes"}
        note.items.return_value = [("Expression Text", "方向词"), ("Internal", "omit")]
        review.card.note.return_value = note

        snapshot = reviewer.get_current_card_snapshot(review, side="question")

        assert snapshot["language"] == "chinese"
        assert snapshot["current_target"] == "方向词"
        assert snapshot["card_kind"] == "vocabulary"
        assert snapshot["front"] == "方向词"
        assert "internal" not in snapshot

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


