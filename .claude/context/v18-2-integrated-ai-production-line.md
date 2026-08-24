# Task: V18.2 — Integrated AI Production Line

## Mục tiêu
Tách AI Study Sessions thành Study Coach chỉ thuộc Reviewer và tích hợp toàn bộ Forge/Xưởng AI vào Factory như một dây chuyền `Nguồn học liệu → Candidate → Artifact → Kiểm định & Import`, trong đó loại thẻ bám chọn Vocab/Grammar phía trên thay vì lộ router riêng.

## Không làm
- Không đổi prompt/schema AI, model note, template thẻ hoặc SRS.
- Không tự gọi AI khi route, chọn candidate, mở artifact hoặc import.
- Không mở lại Knowledge beta.

## Nguồn đã đọc
- `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/context/current-state.md`
- `.claude/skills/06-ui-layer/SKILL.md`
- `ui/factory_dialog.py:_setup_ui`, `_ai_chat`, `load_card_artifact`
- `ui/ai_companion.py:AiCompanionDock`, `AiStudySessionDialog`, `toggle_ai_companion`

## Bất biến và rủi ro
- Reviewer không có Card Mode/candidate/artifact và không sửa SRS.
- Candidate phải bám source, do người dùng chọn; deck match chỉ advisory.
- Artifact vào Factory là snapshot zero-AI và vẫn qua kiểm định/import hiện hành.
- Không tạo hai owner UI cho cùng source/session hoặc stale callback.

## Kế hoạch tối thiểu
1. Tách Reviewer Study Coach khỏi standalone Forge entry.
2. Gắn Forge workspace trực tiếp vào Factory và dùng một `Nguồn học liệu` duy nhất.
3. Bố trí UI theo các trạm dây chuyền, cập nhật i18n/docs/checklist/test.
4. Rà diff, compile và chạy full isolated suite.

## Acceptance criteria
- [x] Ngoài Reviewer, AI Study Sessions không mở Forge surface; Factory sở hữu dây chuyền sản xuất.
- [x] Factory chứa source/candidate/artifact và import trong cùng cửa sổ; composer chứa input, checkbox Tạo thẻ theo loại phía trên và nút Gửi.
- [x] Không còn `AiStudySessionDialog` làm surface Xưởng riêng.
- [x] UI VI/EN và regression suite xanh.
- [x] Checklist giữ GUI smoke trên profile backup trước release.

## Handoff / kết quả
- Quyết định: AI Study Sessions chỉ thuộc Reviewer; Forge dùng `AiCompanionDock` nhúng trong Factory với source editor dùng chung và panel bung/thu tại chỗ.
- Files đã đổi: `ui/factory_dialog.py`, `ui/ai_companion.py`, `ui/theme.py`, `utils/ai_workspace.py`, `utils/i18n.py`, tests và tài liệu trạng thái/release.
- Kiểm chứng đã chạy và kết quả: compile file Python thay đổi; targeted `167 passed`; full isolated suite `774 passed`.
- Còn lại / blocker: GUI smoke Anki thật trên profile backup để xác nhận chiều cao panel, theme light/dark, focus và restart.
