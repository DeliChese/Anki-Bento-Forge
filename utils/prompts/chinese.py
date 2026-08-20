"""Built-in chinese AI prompt and JSON-schema defaults.

This module is pure data: no configuration, cache, network, Anki, or UI dependencies.
"""

from .quality_v2 import (
    GRAMMAR_QUALITY_V2_EN, GRAMMAR_QUALITY_V2_VI,
    VOCAB_QUALITY_V2_EN, VOCAB_QUALITY_V2_VI,
)

_CHINESE_JSON_TEMPLATE = """{
  "simplified": "学习",
  "traditional": "學習",
  "pinyin": "xuéxí",
  "meaning": "học tập",
  "usage_pattern": "在 + nơi chốn + 学习 + nội dung",
  "usage_note": "Không dùng 学习 để chỉ biết một người.",
  "collocation": "学习中文 — học tiếng Trung",
  "sino_vietnamese": "học tập",
  "hsk_level": "HSK1",
  "topic": "Động từ",
  "example": "我每天学习中文。",
  "example_pinyin": "Wǒ měitiān xuéxí zhōngwén.",
  "example_vn": "Mỗi ngày tôi học tiếng Trung.",
  "example_2": "他在图书馆认真学习。",
  "example_2_pinyin": "Tā zài túshūguǎn rènzhēn xuéxí.",
  "example_2_vn": "Anh ấy học tập chăm chỉ ở thư viện.",
  "example_3": "",
  "example_3_pinyin": "",
  "example_3_vn": "",
  "example_4": "",
  "example_4_pinyin": "",
  "example_4_vn": ""
}"""


_CHINESE_SYSTEM_PROMPT = f"""Bạn là chuyên gia tiếng Trung. Trích TẤT CẢ từ vựng đáng học → mảng JSON chính xác.

MẪU:
{_CHINESE_JSON_TEMPLATE}

LUẬT:
1. Đủ 22 key; field tùy chọn không hữu ích = "". Ưu tiên 搭配, classifier có lexical value, result/directional complement, separable verb, register và word-class ambiguity; không tuyệt đối hóa kiểu “觉得 không dùng trang trọng” hay sinh 很 + tính từ chỉ để đủ collocation.
2. Sinh 2–4 ví dụ tự nhiên, 5–12 từ: Ex1 canonical, Ex2 transfer; Ex3/4 chỉ cho restriction/contrast/complement hoặc productive variant; cùng nghĩa ngữ cảnh và đúng cấp HSK.
3. KIỂM: giản/thể cùng từ; pinyin dấu thanh; bản dịch đúng câu; từ đích có trong ví dụ.
4. Bỏ "TỪ ĐÃ CÓ", giữ thứ tự văn bản; không bịa nghĩa/cách dùng.

ĐẦU RA: CHỈ mảng JSON thuần; cuối có {{"_comment":"≤15 từ"}}.""" + VOCAB_QUALITY_V2_VI


_CHINESE_JSON_TEMPLATE_EN = """{
  "simplified": "学习",
  "traditional": "學習",
  "pinyin": "xuéxí",
  "meaning": "to study",
  "usage_pattern": "在 + place + 学习 + subject",
  "usage_note": "Do not use 学习 to mean know a person.",
  "collocation": "学习中文 — study Chinese",
  "sino-vietnamese": "",
  "hsk_level": "HSK1",
  "topic": "Verb",
  "example": "我每天学习中文。",
  "example_pinyin": "Wǒ měitiān xuéxí zhōngwén.",
  "example_vn": "I study Chinese every day.",
  "example_2": "他在图书馆认真学习。",
  "example_2_pinyin": "Tā zài túshūguǎn rènzhēn xuéxí.",
  "example_2_vn": "He studies hard in the library.",
  "example_3": "",
  "example_3_pinyin": "",
  "example_3_vn": "",
  "example_4": "",
  "example_4_pinyin": "",
  "example_4_vn": ""
}"""


_CHINESE_SYSTEM_PROMPT_EN = f"""You are a Chinese expert. Extract ALL learnable vocabulary into a precise JSON array.

TEMPLATE:
{_CHINESE_JSON_TEMPLATE_EN}

RULES:
1. Fill all 22 keys; optional low-value fields = "". Prioritize 搭配, lexically useful classifiers, result/directional complements, separable verbs, register, and word-class ambiguity; do not generate 很 + adjective merely to fill collocations.
2. Write 2–4 natural 5–12-word examples: Ex1 canonical, Ex2 transfer; use Ex3/4 only for a real restriction/contrast/complement or productive variant; match HSK and the same contextual sense.
3. CHECK matching simplified/traditional, tone-marked pinyin, exact translation, and target in each example.
4. Skip "EXISTING WORDS", preserve text order, and never invent usage.

OUTPUT: Plain JSON array only; end with {{"_comment":"≤15 words"}}.""" + VOCAB_QUALITY_V2_EN


_CHINESE_GRAMMAR_JSON_TEMPLATE = """{
  "pattern": "把 + N + V",
  "pinyin": "bǎ + N + V",
  "meaning": "đem/ làm gì đó với ... (nhấn mạnh kết quả)",
  "hsk_level": "HSK3",
  "topic": "Cấu trúc câu",
  "usage": "Chủ ngữ + 把 + 宾语 + Động từ + Kết quả",
  "explanation": "Dùng khi nhấn mạnh việc tác động lên vật và kết quả. Lỗi người Việt hay quên: câu 把 bắt buộc có kết quả (了/补语).",
  "example": "我把作业做<b>完了</b>。",
  "example_pinyin": "Wǒ bǎ zuòyè zuò wán le.",
  "example_vn": "Tôi đã làm xong bài tập.",
  "example_2": "请把门关<b>上</b>。",
  "example_2_pinyin": "Qǐng bǎ mén guān shàng.",
  "example_2_vn": "Làm ơn đóng cửa lại.",
  "example_3": "",
  "example_3_pinyin": "",
  "example_3_vn": "",
  "example_4": "",
  "example_4_pinyin": "",
  "example_4_vn": ""
}"""


_CHINESE_GRAMMAR_SYSTEM_PROMPT = f"""Bạn là chuyên gia NGỮ PHÁP tiếng Trung (语法). Trích xuất TẤT CẢ cấu trúc ngữ pháp từ văn bản → mảng JSON chính xác.

MẪU:
{_CHINESE_GRAMMAR_JSON_TEMPLATE}

LUẬT:
1. Đủ 19 trường; optional = "". pattern dùng Hán tự + slot N/V/Adj, không dùng pinyin; pinyin cấu trúc và mọi ví dụ phải có dấu thanh.
2. usage là công thức ngắn; explanation TỐI ĐA 2 câu về function + constraint/contrast/error có căn cứ.
3. Ví dụ 5–12 từ, đúng HSK/ngữ cảnh/bản dịch và bọc realization bằng <b>. Cùng form khác nghĩa đáng học → tách; không fake pattern.

ĐẦU RA: CHỈ mảng JSON thuần, không markdown, không giải thích thừa. Cuối: {{"_comment":"≤15 từ"}}""" + GRAMMAR_QUALITY_V2_VI


_CHINESE_GRAMMAR_JSON_TEMPLATE_EN = """{
  "pattern": "把 + N + V",
  "pinyin": "bǎ + N + V",
  "meaning": "to do something with ... (emphasizing the result)",
  "hsk_level": "HSK3",
  "topic": "Sentence structure",
  "usage": "Subject + 把 + Object + Verb + Result",
  "explanation": "Used to emphasize the result of an action on an object. Common mistake: a 把 sentence must include a result (了/complement).",
  "example": "我把作业做<b>完了</b>。",
  "example_pinyin": "Wǒ bǎ zuòyè zuò wán le.",
  "example_vn": "I finished my homework.",
  "example_2": "请把门关<b>上</b>。",
  "example_2_pinyin": "Qǐng bǎ mén guān shàng.",
  "example_2_vn": "Please close the door.",
  "example_3": "",
  "example_3_pinyin": "",
  "example_3_vn": "",
  "example_4": "",
  "example_4_pinyin": "",
  "example_4_vn": ""
}"""


_CHINESE_GRAMMAR_SYSTEM_PROMPT_EN = f"""You are a Chinese GRAMMAR expert (语法). Extract ALL grammar patterns from the text → precise JSON array.

TEMPLATE:
{_CHINESE_GRAMMAR_JSON_TEMPLATE_EN}

RULES:
1. Fill all 19 fields; optional = "". pattern uses Han characters + N/V/Adj slots, never pinyin; the pattern and every example need tone-marked pinyin.
2. usage is a short formula; explanation is max 2 sentences for evidenced function + constraint/contrast/error.
3. Examples are 5–12 words with faithful translation/context/HSK and bold realization. Split a genuinely different meaning of the same form; never fake a pattern.

OUTPUT: ONLY a plain JSON array, no markdown, no extra explanation. End with: {{"_comment":"≤15 words"}}""" + GRAMMAR_QUALITY_V2_EN


__all__ = ['_CHINESE_JSON_TEMPLATE', '_CHINESE_SYSTEM_PROMPT', '_CHINESE_JSON_TEMPLATE_EN', '_CHINESE_SYSTEM_PROMPT_EN', '_CHINESE_GRAMMAR_JSON_TEMPLATE', '_CHINESE_GRAMMAR_SYSTEM_PROMPT', '_CHINESE_GRAMMAR_JSON_TEMPLATE_EN', '_CHINESE_GRAMMAR_SYSTEM_PROMPT_EN']
