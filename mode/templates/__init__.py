"""Language-scoped card-template registry and compatibility exports.

The public ``mode.templates`` API remains stable while template markup lives
in one module per target language.
"""

from .japanese import *  # noqa: F403
from .chinese import *  # noqa: F403
from .korean import *  # noqa: F403
from .english import *  # noqa: F403
from .japanese import (
    tmpl_ja_combo_q, tmpl_ja_combo_a, tmpl_ja_g_q, tmpl_ja_g_a,
    tmpl_ja_g_rev_q, tmpl_ja_g_rev_a, tmpl_ja_vn_q, tmpl_ja_vn_a,
    tmpl_ja_wb_q, tmpl_ja_wb_a, tmpl_ja_pron_q, tmpl_ja_pron_a,
    tmpl_ja_lg_q, tmpl_ja_lg_a,
)
from .chinese import (
    tmpl_zh_combo_q, tmpl_zh_combo_a, tmpl_zh_g_q, tmpl_zh_g_a,
    tmpl_zh_g_rev_q, tmpl_zh_g_rev_a, tmpl_zh_vn_q, tmpl_zh_vn_a,
    tmpl_zh_wb_q, tmpl_zh_wb_a, tmpl_zh_pron_q, tmpl_zh_pron_a,
    tmpl_zh_lg_q, tmpl_zh_lg_a,
)
from .korean import (
    tmpl_ko_combo_q, tmpl_ko_combo_a, tmpl_ko_g_q, tmpl_ko_g_a,
    tmpl_ko_g_rev_q, tmpl_ko_g_rev_a, tmpl_ko_vn_q, tmpl_ko_vn_a,
    tmpl_ko_wb_q, tmpl_ko_wb_a, tmpl_ko_pron_q, tmpl_ko_pron_a,
    tmpl_ko_lg_q, tmpl_ko_lg_a,
)
from .english import (
    tmpl_en_combo_q, tmpl_en_combo_a, tmpl_en_g_q, tmpl_en_g_a,
    tmpl_en_g_rev_q, tmpl_en_g_rev_a, tmpl_en_vn_q, tmpl_en_vn_a,
    tmpl_en_wb_q, tmpl_en_wb_a, tmpl_en_pron_q, tmpl_en_pron_a,
    tmpl_en_lg_q, tmpl_en_lg_a,
)
from .common import _independent_template
from .collocation import collocation_templates_for
from ..shared import _EXAMPLE_READING_TOGGLE_JS


def _with_reading_toggle(template):
    """Append the Review-only reading toggle without adding Anki fields."""
    def render():
        return template() + _EXAMPLE_READING_TOGGLE_JS
    return render


def _independent_pair(question, answer, skill, label):
    return (
        _independent_template(_with_reading_toggle(question), skill, label),
        _independent_template(_with_reading_toggle(answer), skill, label),
    )


LANG_TEMPLATES = {
    "japanese": (
        _with_reading_toggle(tmpl_ja_combo_q), _with_reading_toggle(tmpl_ja_combo_a),
        *_independent_pair(tmpl_ja_vn_q, tmpl_ja_vn_a, "production", "S?n xu?t"),
        *_independent_pair(tmpl_ja_wb_q, tmpl_ja_wb_a, "spelling", "Ch?nh t?"),
        *_independent_pair(tmpl_ja_pron_q, tmpl_ja_pron_a, "pronunciation", "Ph?t ?m"),
        *_independent_pair(tmpl_ja_lg_q, tmpl_ja_lg_a, "letter-gap", "Nh? m?t ch?"),
    ),
    "chinese": (
        _with_reading_toggle(tmpl_zh_combo_q), _with_reading_toggle(tmpl_zh_combo_a),
        *_independent_pair(tmpl_zh_vn_q, tmpl_zh_vn_a, "production", "S?n xu?t"),
        *_independent_pair(tmpl_zh_wb_q, tmpl_zh_wb_a, "spelling", "Ch?nh t?"),
        *_independent_pair(tmpl_zh_pron_q, tmpl_zh_pron_a, "pronunciation", "Ph?t ?m"),
        *_independent_pair(tmpl_zh_lg_q, tmpl_zh_lg_a, "letter-gap", "Nh? m?t ch?"),
    ),
    "korean": (
        _with_reading_toggle(tmpl_ko_combo_q), _with_reading_toggle(tmpl_ko_combo_a),
        *_independent_pair(tmpl_ko_vn_q, tmpl_ko_vn_a, "production", "S?n xu?t"),
        *_independent_pair(tmpl_ko_wb_q, tmpl_ko_wb_a, "spelling", "Ch?nh t?"),
        *_independent_pair(tmpl_ko_pron_q, tmpl_ko_pron_a, "pronunciation", "Ph?t ?m"),
        *_independent_pair(tmpl_ko_lg_q, tmpl_ko_lg_a, "letter-gap", "Nh? m?t ch?"),
    ),
    "english": (
        _with_reading_toggle(tmpl_en_combo_q), _with_reading_toggle(tmpl_en_combo_a),
        *_independent_pair(tmpl_en_vn_q, tmpl_en_vn_a, "production", "Sản xuất"),
        *_independent_pair(tmpl_en_wb_q, tmpl_en_wb_a, "spelling", "Chính tả"),
        *_independent_pair(tmpl_en_pron_q, tmpl_en_pron_a, "pronunciation", "Phát âm"),
        *_independent_pair(tmpl_en_lg_q, tmpl_en_lg_a, "letter-gap", "Nhớ mặt chữ"),
    ),
}


LANG_GRAMMAR_TEMPLATES = {
    "japanese": tuple(_with_reading_toggle(template) for template in (
        tmpl_ja_g_q, tmpl_ja_g_a, tmpl_ja_g_rev_q, tmpl_ja_g_rev_a,
    )),
    "chinese": tuple(_with_reading_toggle(template) for template in (
        tmpl_zh_g_q, tmpl_zh_g_a, tmpl_zh_g_rev_q, tmpl_zh_g_rev_a,
    )),
    "korean": tuple(_with_reading_toggle(template) for template in (
        tmpl_ko_g_q, tmpl_ko_g_a, tmpl_ko_g_rev_q, tmpl_ko_g_rev_a,
    )),
    "english": tuple(_with_reading_toggle(template) for template in (
        tmpl_en_g_q, tmpl_en_g_a, tmpl_en_g_rev_q, tmpl_en_g_rev_a,
    )),
}

LANG_COLLOCATION_TEMPLATES = {
    lang: tuple(_with_reading_toggle(template) for template in collocation_templates_for(lang))
    for lang in LANG_TEMPLATES
}


__all__ = [
    "LANG_TEMPLATES", "LANG_GRAMMAR_TEMPLATES", "LANG_COLLOCATION_TEMPLATES",
    *[name for name in globals() if name.startswith("tmpl_")],
]
