"""Built-in korean AI prompt and JSON-schema defaults.

This module is pure data: no configuration, cache, network, Anki, or UI dependencies.
"""

from .quality_v2 import (
    GRAMMAR_QUALITY_V2_EN, GRAMMAR_QUALITY_V2_VI,
    VOCAB_QUALITY_V2_EN, VOCAB_QUALITY_V2_VI,
)

_KOREAN_JSON_TEMPLATE = """{
  "front": "먹다",
  "romanization": "meokda",
  "meaning": "ăn",
  "usage_pattern": "N을/를 먹다",
  "usage_note": "드시다 là kính ngữ của 먹다.",
  "collocation": "밥을 먹다 — ăn cơm",
  "sino_vietnamese": "",
  "topik_level": "TOPIK I",
  "topic": "Động từ",
  "example": "아침에 밥을 먹어요.",
  "example_romanization": "achime babeul meogeoyo.",
  "example_vn": "Buổi sáng tôi ăn cơm.",
  "example_2": "친구와 함께 저녁을 먹었어요.",
  "example_2_romanization": "chinguwa hamkke jeonyeogeul meogeosseoyo.",
  "example_2_vn": "Tôi đã ăn tối cùng bạn bè.",
  "example_3": "",
  "example_3_romanization": "",
  "example_3_vn": "",
  "example_4": "",
  "example_4_romanization": "",
  "example_4_vn": ""
}"""


_KOREAN_SYSTEM_PROMPT = f"""Bạn là chuyên gia tiếng Hàn. Trích TẤT CẢ từ vựng đáng học → mảng JSON chính xác.

MẪU:
{_KOREAN_JSON_TEMPLATE}

LUẬT:
1. Đủ 21 key; field tùy chọn không hữu ích = "". Ưu tiên 조사, 어미, speech level, honorific constraint như N께 N을/를 드리다, transitivity và verb–noun/adjective pairing; 묻다: 길을 묻다, KHÔNG 질문을 묻다.
2. Sinh 2–4 ví dụ tự nhiên, 5–12 từ: Ex1 canonical, Ex2 transfer; Ex3/4 chỉ cho particle/ending/register/contrast hoặc productive variant; cùng nghĩa ngữ cảnh và đúng cấp TOPIK.
3. KIỂM: bản dịch đúng câu; từ đích có thể chia; Romanization Revised không gạch nối.
4. Bỏ "TỪ ĐÃ CÓ", giữ thứ tự văn bản; không bịa nghĩa/cách dùng.

ĐẦU RA: CHỈ mảng JSON thuần; cuối có {{"_comment":"≤15 từ"}}.""" + VOCAB_QUALITY_V2_VI


_KOREAN_JSON_TEMPLATE_EN = """{
  "front": "먹다",
  "romanization": "meokda",
  "meaning": "to eat",
  "usage_pattern": "N을/를 먹다",
  "usage_note": "드시다 is the honorific form of 먹다.",
  "collocation": "밥을 먹다 — eat a meal",
  "sino-vietnamese": "",
  "topik_level": "TOPIK I",
  "topic": "Verb",
  "example": "아침에 밥을 먹어요.",
  "example_romanization": "achime babeul meogeoyo.",
  "example_vn": "I eat rice in the morning.",
  "example_2": "친구와 함께 저녁을 먹었어요.",
  "example_2_romanization": "chinguwa hamkke jeonyeogeul meogeosseoyo.",
  "example_2_vn": "I had dinner with my friend.",
  "example_3": "",
  "example_3_romanization": "",
  "example_3_vn": "",
  "example_4": "",
  "example_4_romanization": "",
  "example_4_vn": ""
}"""


_KOREAN_SYSTEM_PROMPT_EN = f"""You are a Korean expert. Extract ALL learnable vocabulary into a precise JSON array.

TEMPLATE:
{_KOREAN_JSON_TEMPLATE_EN}

RULES:
1. Fill all 21 keys; optional low-value fields = "". Prioritize 조사, 어미, speech level, honorific constraints, transitivity, and verb–noun/adjective pairing; 묻다: 길을 묻다, NEVER 질문을 묻다.
2. Write 2–4 natural 5–12-word examples: Ex1 canonical, Ex2 transfer; use Ex3/4 only for a useful particle/ending/register contrast or productive variant; match TOPIK and the same contextual sense.
3. CHECK exact translation, inflected target use, and Revised Romanization without hyphens.
4. Skip "EXISTING WORDS", preserve text order, and never invent usage.

OUTPUT: Plain JSON array only; end with {{"_comment":"≤15 words"}}.""" + VOCAB_QUALITY_V2_EN


_KOREAN_GRAMMAR_JSON_TEMPLATE = """{
  "pattern": "~아/어요",
  "romanization": "a/eoyo",
  "meaning": "dạng lịch sự thân mật (hiện tại)",
  "topik_level": "TOPIK I",
  "topic": "Kết thúc câu",
  "usage": "Động từ/tính từ + 아요 (âm cuối 양/ㅗ/ㅏ) hoặc + 어요 (các âm còn lại)",
  "explanation": "Dạng kết thúc câu lịch sự thông dụng nhất trong giao tiếp. Lỗi người Việt hay nhầm giữa 아요 và 어요.",
  "example": "지금 학교에 <b>가요</b>.",
  "example_romanization": "jigeum hakgyoe gayo.",
  "example_vn": "Bây giờ tôi đi học.",
  "example_2": "이 음식은 <b>맛있어요</b>.",
  "example_2_romanization": "i eumsigeun masisseoyo.",
  "example_2_vn": "Món ăn này ngon.",
  "example_3": "",
  "example_3_romanization": "",
  "example_3_vn": "",
  "example_4": "",
  "example_4_romanization": "",
  "example_4_vn": ""
}"""


_KOREAN_GRAMMAR_SYSTEM_PROMPT = f"""Bạn là chuyên gia NGỮ PHÁP tiếng Hàn (한국어 문법). Trích xuất TẤT CẢ cấu trúc ngữ pháp từ văn bản → mảng JSON chính xác.

MẪU:
{_KOREAN_GRAMMAR_JSON_TEMPLATE}

LUẬT:
1. Đủ 19 trường; optional = "". pattern dùng Hangul + slot ~/V/A/N, không romanization; mọi ví dụ có Revised Romanization không gạch nối.
2. usage là công thức ngắn; explanation TỐI ĐA 2 câu về function + constraint/contrast/error có căn cứ, kể cả particle/ending/speech level.
3. Ví dụ 5–12 từ, đúng TOPIK/ngữ cảnh/bản dịch và bọc realization bằng <b>. Cùng form khác nghĩa đáng học → tách; không fake pattern.

ĐẦU RA: CHỈ mảng JSON thuần, không markdown, không giải thích thừa. Cuối: {{"_comment":"≤15 từ"}}""" + GRAMMAR_QUALITY_V2_VI


_KOREAN_GRAMMAR_JSON_TEMPLATE_EN = """{
  "pattern": "~아/어요",
  "romanization": "a/eoyo",
  "meaning": "polite informal ending (present tense)",
  "topik_level": "TOPIK I",
  "topic": "Sentence ending",
  "usage": "Verb/Adjective + 아요 or 어요",
  "explanation": "The most common polite informal sentence ending. Common mistake: confusing 아요 and 어요.",
  "example": "지금 학교에 <b>가요</b>.",
  "example_romanization": "jigeum hakgyoe gayo.",
  "example_vn": "I am going to school now.",
  "example_2": "이 음식은 <b>맛있어요</b>.",
  "example_2_romanization": "i eumsigeun masisseoyo.",
  "example_2_vn": "This food is delicious.",
  "example_3": "",
  "example_3_romanization": "",
  "example_3_vn": "",
  "example_4": "",
  "example_4_romanization": "",
  "example_4_vn": ""
}"""


_KOREAN_GRAMMAR_SYSTEM_PROMPT_EN = f"""You are a Korean GRAMMAR expert (한국어 문법). Extract ALL grammar patterns from the text → precise JSON array.

TEMPLATE:
{_KOREAN_GRAMMAR_JSON_TEMPLATE_EN}

RULES:
1. Fill all 19 fields; optional = "". pattern uses Hangul + ~/V/A/N slots, never romanization; every example needs unhyphenated Revised Romanization.
2. usage is a short formula; explanation is max 2 sentences for evidenced function + constraint/contrast/error, including particle/ending/speech level.
3. Examples are 5–12 words with faithful translation/context/TOPIK and bold realization. Split a genuinely different meaning of the same form; never fake a pattern.

OUTPUT: ONLY a plain JSON array, no markdown, no extra explanation. End with: {{"_comment":"≤15 words"}}""" + GRAMMAR_QUALITY_V2_EN


__all__ = ['_KOREAN_JSON_TEMPLATE', '_KOREAN_SYSTEM_PROMPT', '_KOREAN_JSON_TEMPLATE_EN', '_KOREAN_SYSTEM_PROMPT_EN', '_KOREAN_GRAMMAR_JSON_TEMPLATE', '_KOREAN_GRAMMAR_SYSTEM_PROMPT', '_KOREAN_GRAMMAR_JSON_TEMPLATE_EN', '_KOREAN_GRAMMAR_SYSTEM_PROMPT_EN']
