# Task: V18.1 — AI Study Sessions

## Mục tiêu
Triển khai learning companion theo session cho Factory và Anki Reviewer: chat ngắn gọn, context thẻ tối thiểu, lịch sử bền vững, Card Mode one-shot tạo artifact qua reliability pipeline rồi đưa vào Xưởng.

## Không làm
Không có memory xuyên session, embeddings/vector DB, web search, cloud sync, auto-create/import/edit card, auto-rate/reschedule SRS, voice/OCR/image AI, analytics dashboard hoặc big-bang refactor.

## Nguồn đã đọc
- `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/context/current-state.md`
- `.claude/skills/11-upgrade-playbook/SKILL.md`, `.claude/skills/01-project-map/SKILL.md`
- `docs/architecture.md`, `work_items/PERSONAL_ROADMAP.md`
- Đặc tả đính kèm “AI Study Sessions · Dockable Learning Companion”
- Các owner/symbol được định vị bằng `rg` trong `ui/factory_dialog.py`, `ui/ai_dialogs.py`, `ui/ai_settings.py`, `hooks/reviewer.py`, `workers/ai_workers.py`, `utils/ai_*`, `utils/user_data.py`, `utils/import_history.py`, `Language/`, `tests/`.

## Bất biến và rủi ro
- Domain mới không import `aqt`/Qt; UI và reviewer integration ở `ui/`, `hooks/`, `workers/`.
- Chat mode không inject schema; Vocab/Grammar chỉ do UI bật, one-shot và đi qua `ai_reliability`.
- Artifact chỉ vào Xưởng, không trực tiếp mutation collection; reviewer/SRS luôn là authority.
- Session-local memory, atomic profile storage, không chứa API key/header; corrupt store không được crash add-on.
- Reviewer phải responsive; network chạy worker, panel lazy-load, hide/collapse trả focus.
- Release 18.1 chỉ được ghi là phát hành sau CI và smoke Anki thật.

## Kế hoạch tối thiểu
1. Persistence/context/artifact domain và tests.
2. Companion UI + worker orchestration + session history.
3. Reviewer context/actions/focus lifecycle.
4. Card Mode reliability → artifact → Xưởng.
5. Version/docs/changelog, targeted/full automated tests và manual smoke checklist.

## Acceptance criteria
- [x] Session create/reload/rename/delete/corrupt/migration/retention/artifact tests xanh.
- [x] Context bounded, model-aware, card opt-in, không leak session.
- [x] Chat prose; Card Mode explicit one-shot; malformed payload không tạo artifact.
- [x] Reviewer ask/hint/back-to-review không mutation SRS hoặc leak answer ngoài contract.
- [x] Dock/floating/hide/collapse và UI/default provider/model state persist.
- [x] Artifact mở lại/đưa lại vào Xưởng không gọi AI.
- [x] Version 18.1 và release metadata/docs đồng bộ; full suite xanh.
- [ ] Smoke Anki thật có checklist riêng và do chủ dự án xác nhận trên profile đã backup.

## Handoff / kết quả
- Quyết định: Local implementation hoàn tất; release candidate chưa publish.
- Files đã đổi: domain `utils/ai_session_store.py`, `utils/ai_context_manager.py`, `utils/ai_card_artifacts.py`, `utils/ai_study_prompts.py`; UI `ui/ai_companion.py`, Factory/Reviewer/worker wiring; version, i18n, docs và regression tests.
- Kiểm chứng đã chạy và kết quả: targeted `91 passed`; compile toàn bộ tracked Python xanh; `scripts/test_isolated.ps1` hai vòng, mỗi vòng `631 passed`, worktree-stability gate xanh.
- Còn lại / blocker: CI và smoke Anki thật theo `RELEASE_CHECKLIST.md`; không phải blocker cho mã cục bộ nhưng là gate bắt buộc trước publish.
