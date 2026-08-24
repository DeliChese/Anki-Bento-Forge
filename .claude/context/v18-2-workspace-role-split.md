# Task: V18.2A — Workspace Role Split

## Mục tiêu
Tách rõ Study Coach trong Reviewer khỏi dây chuyền sản xuất học liệu: Reviewer chỉ chat với context thẻ hiện tại; Forge là workspace duy nhất có Card Mode, artifact và đường vào Xưởng.

## Không làm
Không xây candidate pipeline, web/OCR/video mining, analytics, collection scan mới, auto-import hoặc mutation SRS.

## Nguồn đã đọc
- `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/context/current-state.md`
- `.claude/skills/06-ui-layer/SKILL.md`
- `utils/ai_workspace.py`, `utils/ai_study_prompts.py`, `ui/ai_companion.py`
- `tests/test_ai_workspaces.py`, `tests/test_ai_study_sessions.py`

## Bất biến và rủi ro
- Reviewer không nhận source; Forge không nhận current-card context.
- Artifact hiện hành/stale vẫn được lưu và Forge vẫn mở snapshot zero-AI.
- Không tự gọi AI, quét collection, import thẻ hay đổi SRS.
- Mọi chuỗi UI mới/đổi phải có VI/EN qua `t()`.

## Kế hoạch tối thiểu
1. Thêm capability `allows_card_mode` và fail-closed validation.
2. Ẩn Card Mode/artifact UI và artifact transcript trong Reviewer.
3. Cập nhật prompt ownership, i18n, roadmap/changelog và regression tests.
4. Chạy targeted tests, compile, isolated suite và xem diff.

## Acceptance criteria
- [x] Reviewer không hiển thị Card Mode/artifact controls và không tạo artifact.
- [x] Domain/prompt boundary từ chối `card_mode` khi workspace là Reviewer.
- [x] Forge vẫn có Vocab/Grammar artifact và artifact → Xưởng zero-AI.
- [x] Targeted/full automated tests xanh; GUI smoke trên profile backup còn là release gate của chủ dự án.

## Handoff / kết quả
- Quyết định: Local implementation hoàn tất; Reviewer coaching-only, Forge sở hữu Card Mode/artifact.
- Files đã đổi: workspace/prompt/cache boundary, companion UI, i18n, regression tests, README, roadmap/current-state và changelog.
- Kiểm chứng đã chạy và kết quả: targeted `130 passed`; release/docs `9 passed`; compile tracked Python xanh; isolated suite hai vòng, mỗi vòng `731 passed`; diff check xanh.
- Còn lại / blocker: GUI smoke Anki trên profile đã backup.
