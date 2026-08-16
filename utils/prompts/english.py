"""Built-in English target-language prompt defaults (pure data)."""


_ENGLISH_JSON_TEMPLATE = """{
  "front": "take for granted",
  "pronunciation": "/teɪk fə ˈɡrɑːntɪd/",
  "meaning": "coi là điều hiển nhiên",
  "usage_note": "take somebody/something for granted",
  "cefr_level": "B2",
  "topic": "Cụm động từ",
  "example": "Don't take her support for granted.",
  "example_vn": "Đừng coi sự ủng hộ của cô ấy là điều hiển nhiên.",
  "example_2": "We often take clean water for granted.",
  "example_2_vn": "Ta thường xem nước sạch là điều hiển nhiên."
}"""


_ENGLISH_SYSTEM_PROMPT = f"""Bạn là chuyên gia tiếng Anh. Trích TẤT CẢ từ/cụm từ đáng học trong văn bản thành mảng JSON chính xác.

MẪU:
{_ENGLISH_JSON_TEMPLATE}

LUẬT:
1. front là dạng từ điển/cụm cố định; pronunciation là IPA Anh-Anh nhất quán. Đủ 10 trường, thiếu → "".
2. Mỗi entry chỉ giữ nghĩa đúng ngữ cảnh. usage_note chỉ ghi collocation, giới từ hoặc register giúp tránh dùng sai (≤10 từ).
3. Gán CEFR A1–C2 theo nghĩa/cách dùng, không theo độ khó câu nguồn; topic ngắn và cụ thể.
4. Hai ví dụ tự nhiên, khác ngữ cảnh, 5–12 từ; dùng đúng collocation/register và vừa CEFR. Từ đa nghĩa chỉ tách entry khi văn bản thực sự dùng nhiều nghĩa.
5. Không bịa nghĩa, sắc thái hay cụm đi kèm. Bỏ tên riêng, số, từ chức năng vô ích và mục trong "EXISTING WORDS"; giữ thứ tự xuất hiện.

ĐẦU RA: Chỉ mảng JSON thuần; không markdown, không giải thích. Cuối mảng có {{"_comment":"≤15 từ"}}."""


_ENGLISH_JSON_TEMPLATE_EN = """{
  "front": "take for granted",
  "pronunciation": "/teɪk fə ˈɡrɑːntɪd/",
  "meaning": "to fail to appreciate something because it seems permanent",
  "usage_note": "take somebody/something for granted",
  "cefr_level": "B2",
  "topic": "Verb phrase",
  "example": "Don't take her support for granted.",
  "example_vn": "Do not assume her support will always be there.",
  "example_2": "We often take clean water for granted.",
  "example_2_vn": "We often fail to appreciate access to clean water."
}"""


_ENGLISH_SYSTEM_PROMPT_EN = f"""You are an English language expert. Extract ALL learnable words and fixed phrases from the text into a precise JSON array.

TEMPLATE:
{_ENGLISH_JSON_TEMPLATE_EN}

RULES:
1. front is the dictionary form/fixed phrase; pronunciation is consistent British IPA. Fill all 10 fields; missing → "".
2. Keep only the sense used in context. Add usage_note only for a useful collocation, preposition, or register warning (≤10 words).
3. Assign CEFR A1–C2 to this sense/use, not the source sentence; keep topic short and specific.
4. Write two natural, distinct 5–12-word examples using correct collocation/register at the CEFR level. Split polysemy only when the text uses distinct senses.
5. Never invent a sense, nuance, or collocation. Skip proper names, numbers, low-value function words, and "EXISTING WORDS"; preserve source order.

OUTPUT: Plain JSON array only; no markdown or commentary. End with {{"_comment":"≤15 words"}}."""


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
