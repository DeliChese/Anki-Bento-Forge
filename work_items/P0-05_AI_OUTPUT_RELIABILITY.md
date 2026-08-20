# Task: P0-05 — AI Output Reliability

## Mục tiêu

Biến output model/provider không đáng tin thành card chỉ khi extraction, schema identity,
minimum semantics và completeness đều có bằng chứng deterministic; giữ partial result hợp
lệ và retry riêng phần chưa hoàn tất trước release 18.0.0.

## Không làm

- Không thêm card type, field ngôn ngữ, AI chat, OCR/image hoặc model routing.
- Không tự điền field, viết tiếp JSON bị cắt hoặc suy đoán candidate mapping.
- Không bump 18.0.0; smoke Anki thật vẫn do chủ dự án chạy trên profile backup.

## Nguồn đã đọc

- `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/context/current-state.md`
- `.claude/skills/01-project-map/SKILL.md`
- `docs/architecture.md`, `work_items/PERSONAL_ROADMAP.md`
- `utils/ai_extractor.py:extract_vocabulary_with_ai`, `extract_vocabulary_long_text`,
  `extract_grammar_with_ai`, `extract_grammar_long_text`
- `utils/ai_response_parser.py`, `utils/ai_response_guard.py`,
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
- Provider transient retry vẫn thuộc HTTP transport; semantic/output recovery tối đa hai tầng.

## Kế hoạch tối thiểu

1. Adapter response và safe JSON extraction/partial-prefix.
2. Language/mode/minimum validator và cache boundary.
3. Candidate reconciliation, partial retry, adaptive split, partial-success UI.
4. Regression matrix, provider-free benchmark, isolated suite và smoke handoff.

## Acceptance criteria

- [x] Raw/fenced/prose/known-wrapper/structured payload recover deterministic.
- [x] Truncated tail không được bịa; valid prefix được giữ.
- [x] Wrong-language level và vocab/grammar mismatch bị chặn.
- [x] Batch biết requested/valid/invalid/duplicate/missing và retry phần thiếu.
- [x] Adaptive split/cap/cancel có regression tests.
- [x] Quality V2 optional/multiline fields không bị reject.
- [x] Cache schema boundary được version hóa.
- [x] Hai vòng full isolated suite xanh trên trạng thái cuối.
- [ ] Smoke Anki profile backup và manual large-batch provider run do chủ dự án xác nhận.

## Handoff / kết quả

- Quyết định: batch mặc định Quality V2 là 8–12 card tùy language/mode; UI mặc định 10,
  policy runtime có thể hạ thấp hơn cấu hình người dùng.
- Files đã đổi: parser/adapter/validator/reliability/cache/batch domain; worker/UI partial
  summary; i18n; tests; simulated benchmark; roadmap/changelog.
- Kiểm chứng đã chạy và kết quả: targeted reliability gate `101 passed`; hai vòng
  isolated suite `592 passed` mỗi vòng; compile toàn bộ Python và benchmark artifact xanh.
- Còn lại / blocker: smoke Anki thật và real-provider 30-card metrics trên profile backup.
