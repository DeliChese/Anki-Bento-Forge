# Task: V18.3 — Language-scoped Study Library plan

## Mục tiêu

Định nghĩa Study Library cục bộ theo `profile + language`: tài liệu lớn được dùng lại qua mọi Reviewer session của đúng ngôn ngữ, kèm bài tập ngắn từ thẻ hiện tại; chưa kích hoạt thay đổi hành vi AI.

## Không làm

Không fine-tune mô hình nền, không gửi dữ liệu học sang dịch vụ mới, không OCR, không thu thập analytics, không tự gọi AI, không quét collection, không tạo/sửa note hay thay đổi rating/ease/due/SRS.

## Nguồn đã đọc

- `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/context/current-state.md`
- `.claude/skills/02-ai-extraction/SKILL.md`
- `.claude/context/ai-study-sessions-18.1.md`
- `.claude/context/v18-2-reviewer-learning-checkpoint.md`
- `work_items/PERSONAL_ROADMAP.md`, `utils/document_extractors.py`, `utils/ai_context_manager.py`, `utils/ai_session_store.py`, `utils/ai_study_prompts.py`

## Bất biến và rủi ro

- Library thuộc `profile + canonical_language`, không thuộc session; session chỉ tham chiếu pack opt-in cùng ngôn ngữ.
- Context lớn dùng source/index local và catalog + chunk bounded trong request; không hứa mô hình nhớ file mà không gửi context.
- Scope Resolver hiểu prompt linh hoạt bằng intent/alias/heading, tạo Scope Manifest có provenance; link nội bộ chỉ được mở rộng theo opt-in “ưu tiên học đầy đủ”, không theo web/URL.
- Library/response cache/transcript là ba ownership riêng; không qua Forge và không suy ra từ SRS hay thao tác review.
- Micro-quiz chỉ được soạn sẵn, không auto-send hay auto-grade.

## Kế hoạch tối thiểu

1. Ingest pack theo ngôn ngữ bằng document extractor hiện có; lưu copy text/hash/index local, quota và delete rõ ràng.
2. Scope Resolver suy ra intent rồi chọn pack/chunk theo alias/heading; chỉ khi opt-in mới mở rộng link nội bộ trong cap token và có provenance.
3. Context assembler inject Scope Manifest + catalog/chunk relevant/bounded vào Reviewer-only prompt.
4. Soạn giải thích/ví dụ theo source và micro-quiz draft từ thẻ hiện tại; kiểm tra bốn ngôn ngữ và boundary token/SRS/workspace.
5. Chỉ mở implementation sau khi chốt scope V1 cho file format, quota, UX xóa và UX opt-in link expansion.

## Acceptance criteria

- [x] Có Study Library theo ngôn ngữ, ý tưởng thay thế, mốc quyết định và kế hoạch rollback trong work item.
- [x] Version 18.3.0, model migration, tài liệu phát hành và changelog đồng bộ.
- [ ] Chốt scope ingest V1 (format file, quota, UX xóa) trước khi mở code feature.

## Handoff / kết quả

- Quyết định: Study Library theo ngôn ngữ là hướng chính; feedback response style là bổ sung sau; chưa có implementation AI training.
- Files đã đổi: version metadata, Note Type migration, release/changelog và `work_items/V18.3_AI_STUDY_COACH_TRAINING_PLAN.md`.
- Kiểm chứng đã chạy và kết quả: targeted metadata/grammar/audio `61 passed`; `py_compile` các module đổi xanh; harness cô lập chạy được `773 passed`, nhưng dừng ở 2 lỗi baseline không liên quan trong `tests/test_import_history.py` (thiếu import `Path`).
- Còn lại / blocker: lựa chọn của chủ profile; baseline test cần được sửa ở task riêng; smoke Anki và CI vẫn là gate phát hành.
