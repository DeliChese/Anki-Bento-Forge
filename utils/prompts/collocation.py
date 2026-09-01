"""Built-in prompts for standalone collocation, chunk, and idiom cards."""

import json


_LANG_META = {
    "japanese": ("furigana", "jlptlevel", "N3", "約束を守る", "giữ lời hứa", "keep a promise", "約束"),
    "chinese": ("pinyin", "hsk_level", "HSK3", "做出决定", "đưa ra quyết định", "make a decision", "决定"),
    "korean": ("romanization", "topik_level", "TOPIK II", "약속을 지키다", "giữ lời hứa", "keep a promise", "약속"),
    "english": ("pronunciation", "cefr_level", "B1", "make a decision", "đưa ra quyết định", "make/come to a decision", "decision"),
}


def _schema(lang: str, *, english_ui: bool) -> str:
    pronunciation_key, level_key, level, chunk, meaning_vi, meaning_en, source_word = _LANG_META[lang]
    meaning = meaning_en if english_ui else meaning_vi
    data = {
        "chunk": chunk,
        pronunciation_key: "...",
        "meaning": meaning,
        "phrase_type": "collocation",
        "pattern_slots": "fixed words + replaceable slots",
        "register_nuance": "neutral; common in speech and writing",
        "constraint": "what can/cannot be replaced; one likely learner error",
        "source_word": source_word,
        "related_terms": "closely related chunk — meaning",
        level_key: level,
        "topic": "daily life",
        "example": "Natural context 1 containing the exact chunk.",
        "example_vn": "Bản dịch chính xác 1.",
        "example_2": "Natural context 2 with a different grammar frame.",
        "example_2_vn": "Bản dịch chính xác 2.",
        "example_3": "Natural context 3 with a different function/register.",
        "example_3_vn": "Bản dịch chính xác 3.",
        "example_4": "Natural context 4 with a different subject/tense/politeness.",
        "example_4_vn": "Bản dịch chính xác 4.",
    }
    if lang == "chinese":
        data.update({f"example{suffix}_pinyin": "..." for suffix in ("", "_2", "_3", "_4")})
    elif lang == "korean":
        data.update({f"example{suffix}_romanization": "..." for suffix in ("", "_2", "_3", "_4")})
    return json.dumps(data, ensure_ascii=False, indent=2)


def _prompt(lang: str, schema: str, *, english_ui: bool) -> str:
    language_name = {
        "japanese": "Japanese", "chinese": "Chinese",
        "korean": "Korean", "english": "English",
    }[lang]
    if english_ui:
        return f"""You extract high-value standalone {language_name} chunks for spaced repetition.
OUTPUT: Return only a JSON array of objects.
SAMPLE:
{schema}

Selection gate:
- Include collocations, lexical chunks, phrasal verbs, idioms, and fixed expressions only when the source supports them.
- A chunk deserves its own card when it is frequent/useful, lexically constrained, non-compositional, register-sensitive, or easy to misuse.
- Do not turn every adjacent word sequence into a card. Do not output single words or abstract grammar rules.
- Keep phrase_type to: collocation, chunk, phrasal_verb, idiom, fixed_expression.
- Preserve one evidenced meaning and register. If evidence is insufficient, use an empty string; never invent region, formality, source word, or constraints.
- pattern_slots marks fixed material and genuinely replaceable slots. source_word links to a source vocabulary item only when explicit.
- Examples 1–4 must contain the exact chunk, preserve the same sense and learner level, and use four meaningfully different grammar contexts.
- Output every key. Optional unknown values are empty strings. No Markdown or commentary."""
    return f"""Bạn trích xuất các cụm {language_name} đáng học thành thẻ Anki độc lập.
ĐẦU RA: Chỉ trả về mảng JSON.
MẪU:
{schema}

Cổng chọn:
- Chỉ lấy collocation, lexical chunk, phrasal verb, thành ngữ hoặc cụm cố định có bằng chứng trong nguồn.
- Tách thẻ riêng khi cụm hữu dụng/tần suất cao, bị ràng buộc kết hợp, nghĩa không suy ra trọn vẹn, nhạy register hoặc dễ dùng sai.
- Không biến mọi chuỗi từ liền nhau thành thẻ; không xuất từ đơn hay quy tắc ngữ pháp trừu tượng.
- phrase_type chỉ là: collocation, chunk, phrasal_verb, idiom, fixed_expression.
- Giữ một nghĩa và sắc thái có căn cứ. Thiếu bằng chứng thì để ""; không bịa vùng miền, độ trang trọng, source_word hay ràng buộc.
- pattern_slots phân biệt phần cố định và khe thật sự thay được. source_word chỉ liên kết từ gốc khi nguồn nêu rõ.
- Ví dụ 1–4 đều chứa đúng cụm, cùng nghĩa/cấp độ, nhưng dùng bốn ngữ cảnh ngữ pháp khác nhau thật sự.
- Xuất đủ key; field tùy chọn không biết = "". Không Markdown, không bình luận."""


_COLLOCATION_JSON_TEMPLATES = {lang: _schema(lang, english_ui=False) for lang in _LANG_META}
_COLLOCATION_JSON_TEMPLATES_EN = {lang: _schema(lang, english_ui=True) for lang in _LANG_META}
_COLLOCATION_SYSTEM_PROMPTS = {
    lang: _prompt(lang, _COLLOCATION_JSON_TEMPLATES[lang], english_ui=False) for lang in _LANG_META
}
_COLLOCATION_SYSTEM_PROMPTS_EN = {
    lang: _prompt(lang, _COLLOCATION_JSON_TEMPLATES_EN[lang], english_ui=True) for lang in _LANG_META
}
