# Task: V18.2C — Reviewer Learning Checkpoint

## Mục tiêu
Tạo vòng kết thúc rõ ràng cho Study Coach trong Reviewer: người học đánh dấu `đã rõ` để quay lại ôn hoặc `cần luyện thêm` để chuẩn bị micro-quiz. Checkpoint thuộc đúng card + study mode và chỉ lưu cục bộ trong Study Session.

## Không làm
Không tự gọi AI, không chấm câu trả lời, không tạo candidate/thẻ/artifact, không quét collection, không sửa note, ease, due hay lịch SRS; không thêm checkpoint vào Forge.

## Nguồn đã đọc
- `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/context/current-state.md`
- `.claude/skills/01-project-map/SKILL.md`
- `utils/ai_session_store.py`, `utils/ai_context_manager.py`, `utils/ai_study_prompts.py`
- `ui/ai_companion.py`, `hooks/reviewer.py`, tests Study Sessions/Workspaces

## Bất biến và rủi ro
- Identity checkpoint là `card_id + study_mode`; không suy đoán khi thiếu card context.
- Message checkpoint dùng `system_internal`, bị loại khỏi model context và rolling summary.
- Nút `cần luyện thêm` chỉ điền prompt; AI chưa được gọi cho đến khi người dùng bấm Gửi.
- Nút `đã rõ` chỉ quay focus về Reviewer; Anki vẫn là owner duy nhất của rating/SRS.
- Forge không hiển thị control, không đọc checkpoint và giữ nguyên dây chuyền candidate/artifact.

## Kế hoạch tối thiểu
1. Domain thuần để tạo/đọc checkpoint fail-closed.
2. Reviewer-only controls, trạng thái theo card/mode và transcript checkpoint riêng.
3. Regression cho persistence, prompt exclusion, zero-AI ownership và cross-workspace.
4. Docs/changelog, targeted tests, compile và hai vòng isolated suite.

## Acceptance criteria
- [x] Checkpoint reload đúng theo card + study mode; malformed/khác card bị bỏ qua.
- [x] Checkpoint không xuất hiện trong request AI hoặc summary.
- [x] `cần luyện thêm` chỉ soạn micro-quiz; `đã rõ` không đổi SRS và quay về Reviewer.
- [x] Controls chỉ có ở Reviewer; Forge/candidate/artifact không regression.
- [x] Targeted/full tests, compile và diff check xanh; GUI smoke profile backup còn là release gate.

## Handoff / kết quả
- Quyết định: Local implementation xanh; chưa đánh dấu verified/released cho đến khi có GUI smoke trên profile backup và CI.
- Files đã đổi: `utils/ai_coaching_loop.py`, context history filter, Reviewer-only controls/render trong `ui/ai_companion.py`, i18n, tests và tài liệu trạng thái.
- Kiểm chứng đã chạy và kết quả: targeted `170 passed`; isolated suite hai vòng `762 passed`; compile toàn bộ Python và `git diff --check` xanh.
- Còn lại / blocker: GUI smoke Anki trên profile đã backup.
