# Task: V18.2D — Workspace-Scoped Session Memory

## Mục tiêu
Một Study Session vẫn là nhật ký chung có thể mở từ Reviewer hoặc Forge, nhưng AI chỉ nhận lịch sử hội thoại và rolling summary thuộc workspace hiện tại.

## Không làm
- Không thay đổi collection, scheduler, note type hoặc Card Factory artifact contract.
- Không tự động gọi AI và không chuyển nội dung giữa Reviewer/Forge.
- Không xóa transcript hoặc summary cũ khi nâng schema; summary cũ chỉ không được đưa vào request đã có workspace vì không xác định được owner.

## Nguồn đã đọc
- `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/context/current-state.md`
- `.claude/skills/01-project-map/SKILL.md`
- `utils/ai_session_store.py:_session, StudySessionStore.update_summary`
- `utils/ai_context_manager.py:prepare_study_context`
- `ui/ai_companion.py:_on_finished, _render_session`
- `tests/test_ai_workspaces.py`

## Bất biến và rủi ro
- Reviewer checkpoint (`system_internal`) không bao giờ đi vào model history.
- Request Reviewer không chứa lịch sử/summary Forge và ngược lại.
- Assistant message cũ chưa gắn workspace chỉ được suy ra owner từ user message có provenance ngay trước nó; turn hoàn toàn legacy bị loại khỏi request scoped.
- API không truyền workspace vẫn dùng summary/history legacy để tương thích.
- Mọi thao tác sửa/xóa transcript phải vô hiệu hóa cả global và workspace summaries.

## Kế hoạch tối thiểu
1. Nâng schema session, thêm hai summary slot được sanitize và persist.
2. Lọc history + chọn summary theo workspace trong context manager.
3. Gắn provenance cho mọi assistant-side message mới và ghi summary đúng workspace.
4. Thêm test migration, isolation hai chiều, invalidation và UI wiring.

## Acceptance criteria
- [x] Mixed session không làm rò marker Reviewer sang Forge hoặc Forge sang Reviewer.
- [x] Rolling summaries của hai workspace tồn tại độc lập qua reload.
- [x] Phiên schema cũ vẫn đọc được; global summary không bị đưa vào request scoped.
- [x] Sửa/xóa turn xóa mọi summary có thể đã lỗi thời và từ chối mutation từ workspace còn lại.
- [x] Targeted tests, compile, diff check và full isolated suite đều xanh.

## Handoff / kết quả
- Quyết định: Local implementation xanh; transcript tiếp tục dùng chung để truy vết, còn model memory là per-workspace và legacy provenance không rõ owner bị fail-closed.
- Files đã đổi: session schema/store, context manager, AI companion, i18n, workspace regression tests và tài liệu trạng thái/release.
- Kiểm chứng đã chạy và kết quả: targeted `173 passed`; isolated suite hai vòng `768 passed`; compile toàn bộ Python và `git diff --check` xanh.
- Còn lại / blocker: GUI smoke Reviewer + Forge trên profile Anki đã backup và CI trước merge/release.
