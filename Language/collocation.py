"""Standalone collocation/idiom note configurations for four languages."""

from copy import deepcopy

from .chinese import LANG_CONFIG as _ZH
from .english import LANG_CONFIG as _EN
from .japanese import LANG_CONFIG as _JA
from .korean import LANG_CONFIG as _KO


_MODEL_LABELS = {
    "japanese": ("Japanese", "🇯🇵 Cụm từ / thành ngữ Tiếng Nhật"),
    "chinese": ("Chinese", "🇨🇳 Cụm từ / thành ngữ Tiếng Trung"),
    "korean": ("Korean", "🇰🇷 Cụm từ / thành ngữ Tiếng Hàn"),
    "english": ("English", "🇬🇧 Collocation / thành ngữ Tiếng Anh"),
}

_BASE = {
    "japanese": _JA,
    "chinese": _ZH,
    "korean": _KO,
    "english": _EN,
}


def _build(lang: str) -> dict:
    cfg = deepcopy(_BASE[lang])
    model_token, label = _MODEL_LABELS[lang]
    cfg["label"] = label
    cfg["model_name"] = f"AnkiTool {model_token} Collocation V18.3 (Add-on)"
    cfg["old_model_names"] = []
    cfg["detect_key"] = "chunk"
    cfg["template_names"] = (
        "1. Cụm từ → Nghĩa", "2. Nghĩa → Cụm từ",
    )
    cfg["all_fields"] = list(cfg["all_fields"])
    unused_vocab_fields = {
        "Usage Pattern", "Usage Note", "Collocation", "Semantic Group",
        "Relationship Note", "SRS Independent",
    }
    cfg["all_fields"] = [
        field for field in cfg["all_fields"] if field not in unused_vocab_fields
    ]
    anchor = cfg["all_fields"].index("Meaning") + 1
    for field in reversed(("Phrase Type", "Pattern / Slots", "Constraint", "Source Word")):
        if field not in cfg["all_fields"]:
            cfg["all_fields"].insert(anchor, field)
    field_map = {
        key: field for key, field in cfg["json_field_map"].items()
        if field not in unused_vocab_fields
    }
    field_map.update({
        "chunk": "Front",
        "phrase_type": "Phrase Type",
        "pattern_slots": "Pattern / Slots",
        "constraint": "Constraint",
        "source_word": "Source Word",
    })
    cfg["json_field_map"] = field_map
    return cfg


LANG_COLLOCATION_CONFIG = {lang: _build(lang) for lang in _BASE}
