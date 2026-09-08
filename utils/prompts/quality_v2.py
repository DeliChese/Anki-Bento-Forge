"""Shared measurable constraints for Language Card Quality V2 prompts."""


VOCAB_QUALITY_V2_VI = """

QUALITY V2.1 (bắt buộc):
- 1 entry = 1 lemma/fixed expression + 1 từ loại + 1 sense có bằng chứng; không tự bịa.
- usage_pattern: 1–2 khung dùng được ngay, mỗi khung một dòng `\\n`; ghi rõ slot + tiểu từ/giới từ/biến đổi/bổ ngữ cần thiết, không chỉ lặp lại từ.
- usage_note: 1–2 câu hoàn chỉnh, tối đa 45 từ; nói khi nào/cách nào dùng và ràng buộc, đối chiếu hoặc lỗi quan trọng nhất. Không chép lại meaning, pattern, ví dụ hay ghi chung chung kiểu “thường được dùng”.
- collocation: 1–3 dòng "cụm — nghĩa" thật sự cố định/tự nhiên. Các field cách dùng được phép dùng SOURCE + kiến thức ngôn ngữ chuẩn, ổn định và chắc chắn; không chắc → "".
- relationship_note tối đa 1 câu chỉ khi giúp phân biệt từ gần nghĩa/biến thể; register_nuance tối đa 1 mệnh đề. semantic_group và related_terms chỉ lấy fact có căn cứ; không tự gán vùng miền/trang trọng.
- Bắt buộc đủ Ex1–Ex4 + bản dịch/phiên âm: cùng sense/cấp độ, khung/mục đích câu khác nhau (khẳng định, phủ định, nghi vấn, thì/thể/điều kiện) nếu tự nhiên.
- Chỉ đổi chủ ngữ/danh từ/bối cảnh → viết lại. Chỉ JSON đúng key MẪU.
"""


VOCAB_QUALITY_V2_EN = """

QUALITY V2.1 (mandatory):
- 1 entry = 1 lemma/fixed expression + 1 POS + 1 evidenced sense; never invent one.
- usage_pattern: 1–2 immediately usable frames, one per `\\n`; include required slots plus particles/prepositions/inflection/complements, not merely the headword.
- usage_note: 1–2 complete sentences, at most 45 words; explain when/how to use it and the most useful constraint, contrast, or learner error. Never repeat the meaning, pattern, examples, or a generic “commonly used” summary.
- collocation: 1–3 natural fixed "phrase — meaning" lines. Usage fields may use SOURCE plus high-confidence, stable standard-language knowledge; if uncertain, use "".
- relationship_note is at most one sentence only for a useful near-synonym/variant distinction; register_nuance is at most one clause. Ground semantic_group and related_terms; never invent regional use or formality.
- Ex1–Ex4 + translations/pronunciation: one sense/level, different natural grammar frames or purposes (affirmative, negative, question, tense/aspect/conditional).
- A changed subject/noun/setting alone → rewrite. Output only TEMPLATE-key JSON.
"""


GRAMMAR_QUALITY_V2_VI = """

QUALITY V2.1 (bắt buộc):
- 1 entry = 1 form–meaning pair có bằng chứng, theo Function → Form → Constraint → Contrast/Error → Variants.
- usage: 1–2 dòng, tối đa 35 từ; cho công thức đầy đủ với loại từ/slot và tiểu từ, giới từ, chia dạng hay bổ ngữ bắt buộc. Chỉ thêm phủ định/nghi vấn khi có dạng bất quy tắc.
- explanation: 1–2 câu hoàn chỉnh, tối đa 50 từ; nêu tình huống/ý định/sắc thái rồi ràng buộc, đối chiếu hoặc lỗi quan trọng nhất. Không lặp meaning/usage và không dùng mô tả chung chung.
- Ex1/2 khác nhiệm vụ; Ex3/4 chỉ cho negative/question/tense/subject/register/contrast/variant có information gain. Tất cả cùng function/level, bọc pattern bằng <b>; ví dụ trống → metadata trống.
- Dùng SOURCE + kiến thức ngôn ngữ chuẩn có độ tin cậy cao; không chắc thì bỏ chi tiết, không fake pattern/error. Chỉ xuất mảng JSON đúng key MẪU.
"""


GRAMMAR_QUALITY_V2_EN = """

QUALITY V2.1 (mandatory):
- 1 entry = 1 evidenced form–meaning pair, ordered Function → Form → Constraint → Contrast/Error → Variants.
- usage: 1–2 lines, at most 35 words; give the complete formula with word-class slots and required particles, prepositions, inflection, or complements. Add negative/question forms only when irregular.
- explanation: 1–2 complete sentences, at most 50 words; state the situation/intent/register, then the most important constraint, contrast, or learner error. Do not repeat meaning/usage or use a generic summary.
- Ex1/2 have different roles; Ex3/4 only add a useful negative/question/tense/subject/register/contrast/variant. All keep function/level and wrap the pattern in <b>; empty example → empty metadata.
- Use SOURCE plus high-confidence stable language knowledge; omit uncertain detail and never fake a pattern/error. Output only the TEMPLATE-key JSON array.
"""


__all__ = [
    "VOCAB_QUALITY_V2_VI", "VOCAB_QUALITY_V2_EN",
    "GRAMMAR_QUALITY_V2_VI", "GRAMMAR_QUALITY_V2_EN",
]
