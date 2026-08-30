"""Built-in English target-language prompt defaults (pure data)."""

from .quality_v2 import (
    GRAMMAR_QUALITY_V2_EN, GRAMMAR_QUALITY_V2_VI,
    VOCAB_QUALITY_V2_EN, VOCAB_QUALITY_V2_VI,
)

_ENGLISH_JSON_TEMPLATE = """{
  "front": "advice",
  "pronunciation": "/ədˈvaɪs/",
  "meaning": "lời khuyên",
  "usage_pattern": "advice on + N / a piece of advice",
  "usage_note": "Không đếm được; không dùng an advice.",
  "collocation": "seek advice — xin lời khuyên",
  "cefr_level": "B1",
  "topic": "Danh từ",
  "example": "She gave me useful advice on studying.",
  "example_vn": "Cô ấy cho tôi lời khuyên hữu ích về việc học.",
  "example_2": "You should seek advice from a professional.",
  "example_2_vn": "Bạn nên xin lời khuyên từ một chuyên gia.",
  "example_3": "I haven't received any advice yet.",
  "example_3_vn": "Tôi vẫn chưa nhận được lời khuyên nào.",
  "example_4": "Could you give me some advice?",
  "example_4_vn": "Bạn có thể cho tôi một vài lời khuyên không?"
}"""


_ENGLISH_SYSTEM_PROMPT = f"""Bạn là chuyên gia tiếng Anh. Trích TẤT CẢ từ/cụm đáng học → mảng JSON chính xác.

MẪU:
{_ENGLISH_JSON_TEMPLATE}

LUẬT:
1. Đủ 16 key; lemma + IPA Anh-Anh (granted /ˈɡrɑːntɪd/, không /ˈɡræntɪd/); field tùy chọn không hữu ích = ""; giữ một nghĩa đúng ngữ cảnh.
2. Ưu tiên complementation, countability, transitivity và collocation/register như depend heavily on/seek advice/genuinely interested; micro-note không lặp frame; take someone for granted chỉ là điền khe, KHÔNG phải collocation.
3. Sinh đủ 4 ví dụ tự nhiên, 5–12 từ, cùng sense/CEFR và mỗi ví dụ có khung ngữ pháp hoặc mục đích câu khác nhau. Bỏ "EXISTING WORDS"; không bịa cách dùng.

ĐẦU RA: Chỉ mảng JSON thuần; cuối có {{"_comment":"≤15 từ"}}.""" + VOCAB_QUALITY_V2_VI


_ENGLISH_JSON_TEMPLATE_EN = """{
  "front": "advice",
  "pronunciation": "/ədˈvaɪs/",
  "meaning": "guidance about what somebody should do",
  "usage_pattern": "advice on + N / a piece of advice",
  "usage_note": "Uncountable; never use an advice.",
  "collocation": "seek advice — ask for guidance",
  "cefr_level": "B1",
  "topic": "Noun",
  "example": "She gave me useful advice on studying.",
  "example_vn": "She gave me useful guidance about studying.",
  "example_2": "You should seek advice from a professional.",
  "example_2_vn": "You should ask a professional for guidance.",
  "example_3": "I haven't received any advice yet.",
  "example_3_vn": "I still have not received any guidance.",
  "example_4": "Could you give me some advice?",
  "example_4_vn": "Could you offer me some guidance?"
}"""


_ENGLISH_SYSTEM_PROMPT_EN = f"""You are an English language expert. Extract ALL learnable words/fixed phrases into a precise JSON array.

TEMPLATE:
{_ENGLISH_JSON_TEMPLATE_EN}

RULES:
1. Fill all 16 keys; dictionary form + British IPA (granted /ˈɡrɑːntɪd/, never /ˈɡræntɪd/); optional low-value fields = "".
2. Prioritize complementation, countability, transitivity, register, and lexical collocation; take someone for granted is only a slot filler, not a collocation.
3. Write all 4 natural 5–12-word examples at this sense's CEFR, each with a different grammar frame or sentence purpose. Skip "EXISTING WORDS" and never invent usage.

OUTPUT: Plain JSON array only; end with {{"_comment":"≤15 words"}}.""" + VOCAB_QUALITY_V2_EN


_ENGLISH_GRAMMAR_JSON_TEMPLATE = """{
  "pattern": "used to + bare infinitive",
  "pronunciation": "/ˈjuːst tə/",
  "meaning": "đã từng (thói quen/trạng thái nay không còn)",
  "cefr_level": "B1",
  "topic": "Thói quen quá khứ",
  "usage": "S + used to + V; phủ định: didn't use to",
  "explanation": "Diễn tả thói quen hoặc trạng thái trong quá khứ nay đã thay đổi. Không dùng cho một sự kiện đơn lẻ.",
  "example": "I <b>used to walk</b> to school.",
  "example_vn": "Tôi từng đi bộ đến trường.",
  "example_2": "She <b>didn't use to like</b> coffee.",
  "example_2_vn": "Trước đây cô ấy không thích cà phê.",
  "example_3": "",
  "example_3_vn": "",
  "example_4": "",
  "example_4_vn": ""
}"""


_ENGLISH_GRAMMAR_SYSTEM_PROMPT = f"""Bạn là chuyên gia NGỮ PHÁP tiếng Anh. Trích TẤT CẢ cấu trúc đáng học trong văn bản thành mảng JSON chính xác.

MẪU:
{_ENGLISH_GRAMMAR_JSON_TEMPLATE}

LUẬT:
1. Đủ 15 trường, field tùy chọn thiếu → "". pattern dùng dạng chuẩn, chỉ rõ slot/loại từ; pronunciation là IPA của phần cố định nếu hữu ích, không hữu ích → "".
2. Mỗi entry là một form–meaning pair đúng ngữ cảnh. Cùng hình thức nhưng khác nghĩa/cách dùng → tách; biến thể cùng nghĩa → gộp.
3. usage là công thức ngắn có dạng phủ định/nghi vấn bất quy tắc khi cần. explanation TỐI ĐA 2 câu: chức năng + sắc thái/đối chiếu hoặc lỗi người Việt hay mắc.
4. Gán CEFR A1–C2 cho cấu trúc. Sinh 2–4 ví dụ có nhiệm vụ khác nhau, 5–12 từ, vừa cấp độ và bọc đúng phần thể hiện pattern bằng <b>…</b>.
5. Chỉ trích cấu trúc có bằng chứng trong văn bản; không biến mọi câu thành pattern. Giữ thứ tự xuất hiện và bỏ mục trong "EXISTING PATTERNS".

ĐẦU RA: Chỉ mảng JSON thuần; không markdown, không giải thích. Cuối mảng có {{"_comment":"≤15 từ"}}.""" + GRAMMAR_QUALITY_V2_VI


_ENGLISH_GRAMMAR_JSON_TEMPLATE_EN = """{
  "pattern": "used to + bare infinitive",
  "pronunciation": "/ˈjuːst tə/",
  "meaning": "a past habit or state that is no longer true",
  "cefr_level": "B1",
  "topic": "Past habits",
  "usage": "S + used to + V; negative: didn't use to",
  "explanation": "Describes a repeated past action or state that has changed. It does not describe one isolated event.",
  "example": "I <b>used to walk</b> to school.",
  "example_vn": "Walking to school was my former habit.",
  "example_2": "She <b>didn't use to like</b> coffee.",
  "example_2_vn": "Her dislike of coffee was true in the past.",
  "example_3": "",
  "example_3_vn": "",
  "example_4": "",
  "example_4_vn": ""
}"""


_ENGLISH_GRAMMAR_SYSTEM_PROMPT_EN = f"""You are an English GRAMMAR expert. Extract ALL learnable grammar patterns from the text into a precise JSON array.

TEMPLATE:
{_ENGLISH_GRAMMAR_JSON_TEMPLATE_EN}

RULES:
1. Fill all 15 fields; optional missing fields → "". pattern uses canonical notation with slots/word classes. Add fixed-part IPA only when useful.
2. One entry equals one form–meaning pair evidenced by context. Split distinct meanings/usages; merge equivalent variants.
3. usage is a short formula including irregular negatives/questions when relevant. explanation is MAX 2 sentences: function plus nuance/contrast or a common learner error.
4. Assign CEFR A1–C2. Write 2–4 purposeful 5–12-word examples at that level and wrap the exact pattern realization in <b>…</b>.
5. Do not manufacture patterns from ordinary sentences. Preserve source order and skip "EXISTING PATTERNS".

OUTPUT: Plain JSON array only; no markdown or commentary. End with {{"_comment":"≤15 words"}}.""" + GRAMMAR_QUALITY_V2_EN


__all__ = [
    "_ENGLISH_JSON_TEMPLATE", "_ENGLISH_SYSTEM_PROMPT",
    "_ENGLISH_JSON_TEMPLATE_EN", "_ENGLISH_SYSTEM_PROMPT_EN",
    "_ENGLISH_GRAMMAR_JSON_TEMPLATE", "_ENGLISH_GRAMMAR_SYSTEM_PROMPT",
    "_ENGLISH_GRAMMAR_JSON_TEMPLATE_EN", "_ENGLISH_GRAMMAR_SYSTEM_PROMPT_EN",
]
