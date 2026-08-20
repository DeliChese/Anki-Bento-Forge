# Task: P0-05 — AI Output Reliability

## Mục tiêu

Biến output model/provider không đáng tin thành card chỉ khi extraction, schema identity,
minimum semantics và completeness đều có bằng chứng deterministic; giữ partial result hợp
lệ và retry riêng phần chưa hoàn tất trước release 18.0.0. Mọi card payload từ Chat cũng
phải đi qua contract này trong khi prose-only vẫn là phản hồi chat hợp lệ.

## Không làm

- Không thêm card type, field ngôn ngữ, AI Study Sessions/history mới, OCR/image hoặc model routing.
- Không tự điền field, viết tiếp JSON bị cắt hoặc suy đoán candidate mapping.
- Không bump 18.0.0; smoke Anki thật vẫn do chủ dự án chạy trên profile backup.

## Nguồn đã đọc

- `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/context/current-state.md`
- `.claude/skills/01-project-map/SKILL.md`
- `docs/architecture.md`, `work_items/PERSONAL_ROADMAP.md`
- `utils/ai_extractor.py:extract_vocabulary_with_ai`, `extract_vocabulary_long_text`,
  `extract_grammar_with_ai`, `extract_grammar_long_text`
- `utils/ai_response_parser.py`, `utils/ai_response_guard.py`,
  `utils/ai_reliability.py`, `utils/ai_text_recovery.py`,
  `utils/ai_output_repairs.py`, `utils/ai_http_client.py`, `utils/ai_providers.py`,
  `utils/ai_session_policy.py`, `utils/ai_result_cache.py`, `utils/ai_workflow.py`
- `utils/batch_processor.py:_call_ai_for_batch`, `process_large_word_list`
- `workers/ai_workers.py`, `workers/batch_workers.py`, `ui/ai_preview.py`,
  `ui/batch_dialog.py`, `ui/factory_dialog.py:_open_batch_dialog`
- `Language/*.py`, `utils/prompts/*.py`, tests và benchmark liên quan.

## Bất biến và rủi ro

- Domain AI không import `aqt`; UI string đi qua `t()`; log chỉ aggregate metadata.
- Không cache partial/wrong-schema; cache key/version giữ language, kind và prompt signature.
- Dedupe theo identity + meaning để không làm mất sense hợp lệ.
- Text extraction không có candidate list one-to-one: chỉ retry source span nhỏ hơn, không giả mapping.
- Khi một source phải split, kết quả hai child span là authoritative; không cộng provisional
  prefix của parent vào lại. Merge child theo identity + meaning để giữ distinct senses.
- Provider transient retry vẫn thuộc HTTP transport; semantic/output recovery tối đa hai tầng.

## Kế hoạch tối thiểu

1. Adapter response và safe JSON extraction/partial-prefix.
2. Language/mode/minimum validator và cache boundary.
3. Candidate reconciliation, partial retry, adaptive split, partial-success UI.
4. Regression matrix, provider-free benchmark, isolated suite và smoke handoff.
5. Hợp nhất optional Chat card parsing vào adapter/parser/validator hiện có; loại parser regex riêng.

## Acceptance criteria

- [x] Raw/fenced/prose/known-wrapper/structured payload recover deterministic.
- [x] Truncated tail không được bịa; valid prefix được giữ.
- [x] Wrong-language level và vocab/grammar mismatch bị chặn.
- [x] Batch biết requested/valid/invalid/duplicate/missing và retry phần thiếu.
- [x] Adaptive split/cap/cancel có regression tests.
- [x] Quality V2 optional/multiline fields không bị reject.
- [x] Cache schema boundary được version hóa.
- [x] Hai vòng full isolated suite xanh trên trạng thái cuối.
- [x] Chat prose/card/structured/schema/ambiguity/truncation cùng dùng reliability contract.
- [x] Split text recovery không cộng lại provisional prefix và merge deterministic.
- [ ] Smoke Anki profile backup và manual large-batch provider run do chủ dự án xác nhận.

## Handoff / kết quả

- Quyết định: batch mặc định Quality V2 là 8–12 card tùy language/mode; UI mặc định 10,
  policy runtime có thể hạ thấp hơn cấu hình người dùng. Chat giữ scope vocab và optional
  card payload phải qua adapter → parser → validator → normalization; split child là
  authoritative khi text recovery phải chia source. Card payload bị reject có warning
  không-fatal trong dialog để prose hữu ích vẫn hiển thị.
- Files đã đổi: parser/adapter/validator/reliability/cache/batch domain; worker/UI partial
  summary; i18n; Chat integration; text recovery; tests; simulated benchmark; roadmap/changelog.
- Kiểm chứng đã chạy và kết quả: Chat/reliability regression `50 passed`; targeted AI gate
  `129 passed`; hai vòng isolated suite `608 passed` mỗi vòng; compile toàn bộ Python và
  critical Ruff lint (`E9,F63,F7,F82`) xanh; benchmark artifact xanh.
- Còn lại / blocker: smoke Anki thật và real-provider 30-card metrics trên profile backup.
