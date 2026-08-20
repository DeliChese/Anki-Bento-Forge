"""Shared measurable constraints for Language Card Quality V2 prompts."""


VOCAB_QUALITY_V2_VI = """

QUALITY V2 (bắt buộc):
- 1 entry = 1 lemma/fixed expression + 1 từ loại + 1 sense có bằng chứng; Meaning chỉ là semantic core. Tách sense thật sự khác, không tự bịa.
- Ba field Usage Guide là CHUỖI, ngăn mục bằng \\n: 1–3 pattern khác frame; 0–3 micro-note có nhãn Constraint/Contrast/Register/Nuance/Error; 0–3 "collocation — nghĩa" khác lexical slot. Không lặp Meaning, fixed phrase hoặc sinh đủ quota.
- Ex1=Canonical, Ex2=Transfer; Ex3=Contrast/Constraint và Ex4=Productive/Advanced chỉ khi cùng sense và có information gain mới. Chỉ đổi chủ ngữ/danh từ/bối cảnh → "".
- Field đi kèm ví dụ trống cũng "". Empty > fabricated. Chỉ xuất mảng JSON đúng key MẪU; không prose/markdown.
"""


VOCAB_QUALITY_V2_EN = """

QUALITY V2 (mandatory):
- 1 entry = 1 lemma/fixed expression + 1 POS + 1 evidenced sense; Meaning is only its semantic core. Split genuinely distinct senses; never invent one.
- The three Usage Guide fields are STRINGS with \\n-separated items: 1–3 different-frame patterns; 0–3 Constraint/Contrast/Register/Nuance/Error micro-notes; 0–3 "collocation — meaning" items with different lexical slots. Never repeat Meaning/a fixed phrase or fill a quota.
- Ex1=Canonical, Ex2=Transfer; use Ex3=Contrast/Constraint and Ex4=Productive/Advanced only when they keep the sense and add information. A changed subject/noun/setting alone → "".
- Companion fields of an empty example are also "". Empty > fabricated. Output only the TEMPLATE-key JSON array; no prose/Markdown.
"""


GRAMMAR_QUALITY_V2_VI = """

QUALITY V2 (bắt buộc):
- 1 entry = 1 form–meaning pair có bằng chứng, theo Function → Form → Constraint → Contrast/Error → Variants.
- Ex1/2 khác nhiệm vụ; Ex3/4 chỉ cho negative/question/tense/subject/register/contrast/variant có information gain. Tất cả cùng function/level, bọc pattern bằng <b>; ví dụ trống → metadata trống.
- Không fake pattern/error. Chỉ xuất mảng JSON đúng key MẪU.
"""


GRAMMAR_QUALITY_V2_EN = """

QUALITY V2 (mandatory):
- 1 entry = 1 evidenced form–meaning pair, ordered Function → Form → Constraint → Contrast/Error → Variants.
- Ex1/2 have different roles; Ex3/4 only add a useful negative/question/tense/subject/register/contrast/variant. All keep function/level and wrap the pattern in <b>; empty example → empty metadata.
- Never fake a pattern/error. Output only the TEMPLATE-key JSON array.
"""


__all__ = [
    "VOCAB_QUALITY_V2_VI", "VOCAB_QUALITY_V2_EN",
    "GRAMMAR_QUALITY_V2_VI", "GRAMMAR_QUALITY_V2_EN",
]
