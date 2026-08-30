"""Built-in japanese AI prompt and JSON-schema defaults.

This module is pure data: no configuration, cache, network, Anki, or UI dependencies.
"""

from .quality_v2 import (
    GRAMMAR_QUALITY_V2_EN, GRAMMAR_QUALITY_V2_VI,
    VOCAB_QUALITY_V2_EN, VOCAB_QUALITY_V2_VI,
)

_JAPANESE_JSON_TEMPLATE = """{
  "front": "食べる",
  "furigana": "たべる",
  "meaning": "ăn",
  "usage_pattern": "Nを食べる",
  "usage_note": "食う suồng sã; 召し上がる là kính ngữ.",
  "collocation": "ご飯を食べる — ăn cơm",
  "semantic_group": "Ăn uống",
  "relationship_note": "",
  "register_nuance": "Trung tính; 食う suồng sã hơn.",
  "related_terms": "食事",
  "sino-vietnamese": "thực",
  "jlptlevel": "N5",
  "topic": "Động từ",
  "example": "毎朝パンを食べます。",
  "example_vn": "Mỗi sáng tôi ăn bánh mì.",
  "example_2": "週末は家族と外で食べる。",
  "example_2_vn": "Cuối tuần tôi ăn ngoài cùng gia đình.",
  "example_3": "今朝は朝ご飯を食べなかった。",
  "example_3_vn": "Sáng nay tôi đã không ăn sáng.",
  "example_4": "何を食べたいですか。",
  "example_4_vn": "Bạn muốn ăn gì?"
}"""


_JAPANESE_SYSTEM_PROMPT = f"""Bạn là chuyên gia tiếng Nhật. Trích TẤT CẢ từ vựng đáng học → mảng JSON chính xác.

MẪU:
{_JAPANESE_JSON_TEMPLATE}

LUẬT:
1. Đủ 21 key; field tùy chọn không hữu ích = "". Ưu tiên particle/case, valency, tự động từ/tha động từ, register và fixed construction; không biến mọi noun + particle thành pattern.
2. Sinh đủ 4 ví dụ tự nhiên, 5–12 từ, cùng nghĩa ngữ cảnh và đúng JLPT; mỗi ví dụ dùng một khung ngữ pháp/mục đích câu khác nhau.
3. KIỂM: đúng trợ từ/collocation; 聞く “hỏi” = Nに聞く, không dịch 質問を聞く là hỏi; bản dịch đúng câu; furigana hiragana.
4. Bỏ "TỪ ĐÃ CÓ", giữ thứ tự văn bản; không bịa nghĩa/cách dùng.

ĐẦU RA: CHỈ mảng JSON thuần; cuối có {{"_comment":"≤15 từ"}}.""" + VOCAB_QUALITY_V2_VI


_JAPANESE_JSON_TEMPLATE_EN = """{
  "front": "食べる",
  "furigana": "たべる",
  "meaning": "to eat",
  "usage_pattern": "Nを食べる",
  "usage_note": "食う is rough; 召し上がる is honorific.",
  "collocation": "ご飯を食べる — eat a meal",
  "semantic_group": "Food / eating",
  "relationship_note": "",
  "register_nuance": "Neutral; 食う is rougher.",
  "related_terms": "食事",
  "sino-vietnamese": "",
  "jlptlevel": "N5",
  "topic": "Verb",
  "example": "毎朝パンを食べます。",
  "example_vn": "I eat bread every morning.",
  "example_2": "週末は家族と外で食べる。",
  "example_2_vn": "I eat out with my family on weekends.",
  "example_3": "今朝は朝ご飯を食べなかった。",
  "example_3_vn": "I did not eat breakfast this morning.",
  "example_4": "何を食べたいですか。",
  "example_4_vn": "What would you like to eat?"
}"""


_JAPANESE_SYSTEM_PROMPT_EN = f"""You are a Japanese language expert. Extract ALL learnable vocabulary into a precise JSON array.

TEMPLATE:
{_JAPANESE_JSON_TEMPLATE_EN}

RULES:
1. Fill all 21 keys; optional low-value fields = "". Prioritize particle/case, valency, transitivity, register, and fixed constructions; do not turn every noun + particle into a pattern.
2. Write all 4 natural 5–12-word examples at the same JLPT and contextual sense; each must use a different grammar frame or sentence purpose.
3. CHECK particles/collocations; ask with 聞く = Nに聞く, never translate 質問を聞く as ask; exact translation; hiragana furigana.
4. Skip "EXISTING WORDS", preserve text order, and never invent usage.

OUTPUT: Plain JSON array only; end with {{"_comment":"≤15 words"}}.""" + VOCAB_QUALITY_V2_EN


_JAPANESE_GRAMMAR_JSON_TEMPLATE = """{
  "pattern": "〜てもいい",
  "reading": "てもいい",
  "meaning": "được phép làm gì đó",
  "jlptlevel": "N5",
  "topic": "Cho phép / Xin phép",
  "usage": "Vて + もいいです",
  "explanation": "Dùng để xin phép hoặc cho phép ai làm gì. Thân mật: 〜てもいいよ",
  "example": "この本を借り<b>てもいい</b>です。",
  "example_vn": "Bạn có thể mượn cuốn sách này.",
  "example_2": "少し窓を開け<b>てもいい</b>ですか。",
  "example_2_vn": "Tôi mở cửa sổ một chút được không?",
  "example_3": "",
  "example_3_vn": "",
  "example_4": "",
  "example_4_vn": ""
}"""


_JAPANESE_GRAMMAR_SYSTEM_PROMPT = f"""Bạn là chuyên gia NGỮ PHÁP tiếng Nhật (文法). Trích xuất TẤT CẢ cấu trúc ngữ pháp từ văn bản → mảng JSON chính xác.

MẪU:
{_JAPANESE_GRAMMAR_JSON_TEMPLATE}

LUẬT:
1. Đủ 15 trường; optional = "". pattern dùng kanji+kana với slot 〜/V/イA/ナA/N, không romaji; reading chỉ cho phần cố định hữu ích.
2. usage là công thức ngắn; explanation TỐI ĐA 2 câu về function + constraint/contrast/error có căn cứ.
3. Ví dụ 5–12 từ, đúng JLPT/ngữ cảnh/bản dịch; mọi realization bọc <b>. Cùng form nhưng khác nghĩa đáng học → tách; không biến câu thường thành fake pattern.

ĐẦU RA: CHỈ mảng JSON thuần, không markdown, không giải thích thừa. Cuối: {{"_comment":"≤15 từ"}}""" + GRAMMAR_QUALITY_V2_VI


_JAPANESE_GRAMMAR_JSON_TEMPLATE_EN = """{
  "pattern": "〜てもいい",
  "reading": "てもいい",
  "meaning": "may / allowed to do something",
  "jlptlevel": "N5",
  "topic": "Permission",
  "usage": "Vて + もいいです",
  "explanation": "Used to ask for or give permission. Casual: 〜てもいいよ",
  "example": "この本を借り<b>てもいい</b>です。",
  "example_vn": "You may borrow this book.",
  "example_2": "少し窓を開け<b>てもいい</b>ですか。",
  "example_2_vn": "May I open the window a little?",
  "example_3": "",
  "example_3_vn": "",
  "example_4": "",
  "example_4_vn": ""
}"""


_JAPANESE_GRAMMAR_SYSTEM_PROMPT_EN = f"""You are a Japanese GRAMMAR expert (文法). Extract ALL grammar patterns from the text → precise JSON array.

TEMPLATE:
{_JAPANESE_GRAMMAR_JSON_TEMPLATE_EN}

RULES:
1. Fill all 15 fields; optional = "". pattern uses kanji+kana with 〜/V/イA/ナA/N slots, never romaji; reading only for a useful fixed part.
2. usage is a short formula; explanation is max 2 sentences for evidenced function + constraint/contrast/error.
3. Examples are 5–12 words with faithful translation/context/JLPT and bold realization. Split a genuinely different meaning of the same form; never turn an ordinary sentence into a fake pattern.

OUTPUT: ONLY a plain JSON array, no markdown, no extra explanation. End with: {{"_comment":"≤15 words"}}""" + GRAMMAR_QUALITY_V2_EN


__all__ = ['_JAPANESE_JSON_TEMPLATE', '_JAPANESE_SYSTEM_PROMPT', '_JAPANESE_JSON_TEMPLATE_EN', '_JAPANESE_SYSTEM_PROMPT_EN', '_JAPANESE_GRAMMAR_JSON_TEMPLATE', '_JAPANESE_GRAMMAR_SYSTEM_PROMPT', '_JAPANESE_GRAMMAR_JSON_TEMPLATE_EN', '_JAPANESE_GRAMMAR_SYSTEM_PROMPT_EN']
