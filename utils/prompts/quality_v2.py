"""Shared measurable constraints for Language Card Quality V2 prompts."""


VOCAB_QUALITY_V2_VI = """

QUALITY V2 (bắt buộc):
- 1 entry = 1 lemma/fixed expression + 1 từ loại + 1 sense có bằng chứng; không tự bịa.
- Guide \n: 1–3 pattern khác frame; 0–3 micro-note Constraint/Contrast/Error; 0–3 "collocation — nghĩa" khác slot. Usage Note = ràng buộc/lỗi; register_nuance = sắc thái/mức độ dùng có căn cứ.
- semantic_group, relationship_note, register_nuance, related_terms chỉ copy fact SOURCE; thiếu → "", không suy ra quan hệ/vùng miền/trang trọng.
- Bắt buộc đủ Ex1–Ex4 + bản dịch/phiên âm: cùng sense/cấp độ, khung/mục đích câu khác nhau (khẳng định, phủ định, nghi vấn, thì/thể/điều kiện) nếu tự nhiên.
- Chỉ đổi chủ ngữ/danh từ/bối cảnh → viết lại. Chỉ JSON đúng key MẪU.
"""


VOCAB_QUALITY_V2_EN = """

QUALITY V2 (mandatory):
- 1 entry = 1 lemma/fixed expression + 1 POS + 1 evidenced sense; never invent one.
- Guide strings use \n: 1–3 different-frame patterns; 0–3 Constraint/Contrast/Error notes; 0–3 "collocation — meaning" slots. Usage Note is a constraint/error; register_nuance is an evidenced register/intensity.
- semantic_group, relationship_note, register_nuance, related_terms copy SOURCE facts only; absent → "", never infer relationships/regional use/formality.
- Ex1–Ex4 + translations/pronunciation: one sense/level, different natural grammar frames or purposes (affirmative, negative, question, tense/aspect/conditional).
- A changed subject/noun/setting alone → rewrite. Output only TEMPLATE-key JSON.
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
