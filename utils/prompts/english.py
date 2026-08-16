"""Built-in English target-language prompt defaults (pure data)."""


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
  "example_2_vn": "Bạn nên xin lời khuyên từ một chuyên gia."
}"""


_ENGLISH_SYSTEM_PROMPT = f"""Bạn là chuyên gia tiếng Anh. Trích TẤT CẢ từ/cụm đáng học → mảng JSON chính xác.

MẪU:
{_ENGLISH_JSON_TEMPLATE}

LUẬT:
1. Đủ 12 key; lemma + IPA Anh-Anh (granted /ˈɡrɑːntɪd/, không /ˈɡræntɪd/); field vô ích = "". Giữ MỘT nghĩa đúng ngữ cảnh/từ loại; cả hai ví dụ phải dùng đúng nghĩa đó, tuyệt đối không đổi nghĩa giữa hai ví dụ.
2. Usage Guide: MỘT frame; note chỉ register/nuance/countability/lỗi, không lặp frame; MỘT collocation từ vựng như depend heavily on/seek advice/genuinely interested. Front đã là fixed phrase thì collocation=""; take someone for granted chỉ là điền khe, KHÔNG phải collocation. Không placeholder/lặp.
3. Hai ví dụ khác nhau, tự nhiên, 5–12 từ, đúng collocation/register và CEFR của sense. Bỏ "EXISTING WORDS"; không bịa cách dùng.

ĐẦU RA: Chỉ mảng JSON thuần; cuối có {{"_comment":"≤15 từ"}}."""


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
  "example_2_vn": "You should ask a professional for guidance."
}"""


_ENGLISH_SYSTEM_PROMPT_EN = f"""You are an English language expert. Extract ALL learnable words/fixed phrases into a precise JSON array.

TEMPLATE:
{_ENGLISH_JSON_TEMPLATE_EN}

RULES:
1. Fill 12 keys; dictionary form + British IPA (granted /ˈɡrɑːntɪd/, never /ˈɡræntɪd/); omit low-value fields. Keep ONE sense/part of speech across both examples.
2. Usage Guide: ONE frame; note only register/nuance/countability/error and never repeats the frame; ONE lexical collocation such as depend heavily on/seek advice/genuinely interested. If front is already a fixed phrase, collocation=""; take someone for granted is only a slot filler. No placeholders/repetition.
3. Write two distinct natural 5–12-word examples at this sense's CEFR. Skip "EXISTING WORDS" and never invent usage.

OUTPUT: Plain JSON array only; end with {{"_comment":"≤15 words"}}."""


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
  "example_2_vn": "Trước đây cô ấy không thích cà phê."
}"""


_ENGLISH_GRAMMAR_SYSTEM_PROMPT = f"""Bạn là chuyên gia NGỮ PHÁP tiếng Anh. Trích TẤT CẢ cấu trúc đáng học trong văn bản thành mảng JSON chính xác.

MẪU:
{_ENGLISH_GRAMMAR_JSON_TEMPLATE}

LUẬT:
1. Đủ 11 trường, thiếu → "". pattern dùng dạng chuẩn, chỉ rõ slot/loại từ; pronunciation là IPA của phần cố định nếu hữu ích, không hữu ích → "".
2. Mỗi entry là một form–meaning pair đúng ngữ cảnh. Cùng hình thức nhưng khác nghĩa/cách dùng → tách; biến thể cùng nghĩa → gộp.
3. usage là công thức ngắn có dạng phủ định/nghi vấn bất quy tắc khi cần. explanation TỐI ĐA 2 câu: chức năng + sắc thái/đối chiếu hoặc lỗi người Việt hay mắc.
4. Gán CEFR A1–C2 cho cấu trúc. Hai ví dụ tự nhiên, khác ngữ cảnh, 5–12 từ, vừa cấp độ và bọc đúng phần thể hiện pattern bằng <b>…</b>.
5. Chỉ trích cấu trúc có bằng chứng trong văn bản; không biến mọi câu thành pattern. Giữ thứ tự xuất hiện và bỏ mục trong "EXISTING PATTERNS".

ĐẦU RA: Chỉ mảng JSON thuần; không markdown, không giải thích. Cuối mảng có {{"_comment":"≤15 từ"}}."""


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
  "example_2_vn": "Her dislike of coffee was true in the past."
}"""


_ENGLISH_GRAMMAR_SYSTEM_PROMPT_EN = f"""You are an English GRAMMAR expert. Extract ALL learnable grammar patterns from the text into a precise JSON array.

TEMPLATE:
{_ENGLISH_GRAMMAR_JSON_TEMPLATE_EN}

RULES:
1. Fill all 11 fields; missing → "". pattern uses canonical notation with slots/word classes. Add fixed-part IPA only when useful.
2. One entry equals one form–meaning pair evidenced by context. Split distinct meanings/usages; merge equivalent variants.
3. usage is a short formula including irregular negatives/questions when relevant. explanation is MAX 2 sentences: function plus nuance/contrast or a common learner error.
4. Assign CEFR A1–C2. Write two natural, distinct 5–12-word examples at that level and wrap the exact pattern realization in <b>…</b>.
5. Do not manufacture patterns from ordinary sentences. Preserve source order and skip "EXISTING PATTERNS".

OUTPUT: Plain JSON array only; no markdown or commentary. End with {{"_comment":"≤15 words"}}."""


__all__ = [
    "_ENGLISH_JSON_TEMPLATE", "_ENGLISH_SYSTEM_PROMPT",
    "_ENGLISH_JSON_TEMPLATE_EN", "_ENGLISH_SYSTEM_PROMPT_EN",
    "_ENGLISH_GRAMMAR_JSON_TEMPLATE", "_ENGLISH_GRAMMAR_SYSTEM_PROMPT",
    "_ENGLISH_GRAMMAR_JSON_TEMPLATE_EN", "_ENGLISH_GRAMMAR_SYSTEM_PROMPT_EN",
]
