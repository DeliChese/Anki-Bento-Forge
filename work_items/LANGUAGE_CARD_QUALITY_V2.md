# Task: P1-02/P1-06 — Language Card Quality V2

> Status: local verification complete; owner smoke pending  
> Authority: supporting; `PERSONAL_ROADMAP.md` remains canonical

## Mục tiêu

Nâng vocab/grammar prompts cho EN/JA/ZH/KO theo nguyên tắc rich note, selective retrieval; hỗ trợ 1–3 mục Usage Guide, 2–4 ví dụ có nhiệm vụ khác nhau và Confusion Guard advisory-only.

## Không làm

Không đổi SRS, không tạo card type mới, không mở Knowledge beta, không thêm TTS cho Example3/4, không semantic cache/model routing hoặc refactor kiến trúc lớn.

## Nguồn đã đọc

- `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/context/current-state.md`
- `.claude/skills/01-project-map/SKILL.md`
- `docs/architecture.md`, `work_items/PERSONAL_ROADMAP.md`
- `Language/*.py`, `utils/prompts/*.py`, `utils/usage_guide.py`
- `utils/ai_response_parser.py`, `utils/ai_result_cache.py`, `utils/ai_benchmark.py`
- `mode/card_render.py`, `mode/templates/common.py`, `utils/model_lifecycle.py`
- các test prompt/parser/config/template/import quality/migration liên quan

## Bất biến và rủi ro

- Field mới chỉ additive và được thêm idempotent; note cũ để trống vẫn render an toàn.
- Example3/4 chỉ ở mặt sau, không thêm audio và không đổi số template/card hay lịch SRS.
- Prompt mặc định đổi phải bump cache version; override của người dùng vẫn có signature riêng.
- Confusion Guard chỉ dựa vào exact curated pair trong cùng deck, chỉ cảnh báo và không chặn import.
- Heuristic không được tuyên bố xác minh nghĩa, naturalness, information gain hoặc hallucination.

## Kế hoạch tối thiểu

1. Mở rộng prompt/schema và normalizer theo contract V2.
2. Render progressive disclosure, preview/edit và migration additive.
3. Thêm Confusion Guard curated exact-match.
4. Thêm benchmark/rubric fixtures và regression tests.
5. Chạy compile, related suite, full isolated suite và review diff.

## Acceptance criteria

- [x] Vocab + grammar của cả bốn ngôn ngữ có Example3/4 tùy chọn.
- [x] Usage Pattern/Note/Collocation hỗ trợ tối đa ba mục không trùng.
- [x] Old two-example cards và empty optional fields tương thích.
- [x] Confusion Guard có positive/negative fixtures bốn ngôn ngữ và advisory-only.
- [x] Prompt/cache version, changelog và benchmark V2 cập nhật.
- [x] Compile và test suite xanh.

## Handoff / kết quả

- Quyết định: serialize Usage Guide bằng newline trong field cũ; chỉ thêm field cho Example3/4, không thêm audio.
- Files đã đổi: `Language/`, `utils/prompts/`, quality/parser/cache/benchmark, preview/i18n, card render, benchmark fixture, tests và docs trạng thái/changelog.
- Kiểm chứng đã chạy và kết quả: baseline liên quan trước sửa `111 passed`; compile toàn bộ Python tracked xanh; related suite `129 passed`; full isolated suite `557 passed` × 2; `git diff --check` sạch.
- Benchmark offline: schema mẫu bốn ngôn ngữ đều valid, trung bình `2.0` examples và `1.0/1.0/1.0` pattern/note/collocation, `0` over-generation; không có provider/key cấu hình trong môi trường nên chưa chạy model thật.
- Cost/size ước tính: vocab system prompt tăng trung bình khoảng `191` input tokens/request; grammar prompt giảm khoảng `75` tokens/request sau khi cô đọng; các key Example3/4 rỗng thêm khoảng `22` output tokens/card. Ví dụ bổ sung thực sinh chưa có số model thật.
- Còn lại / blocker: smoke trên profile Anki backup vẫn do chủ dự án thực hiện trước release.
