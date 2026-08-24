# Task: V18.2B — Forge Candidate Manifest

## Mục tiêu
Thêm bước `SOURCE → CANDIDATE → ARTIFACT`: Forge phân tích source thành manifest có provenance, người dùng chọn candidate, sau đó mới chủ động gửi request Card Mode cho đúng các mục đã chọn.

## Không làm
Không web/OCR/video mining, không auto-call AI lần hai, không auto-import, không semantic repair, không tự xóa candidate chỉ vì trùng mặt chữ trong deck.

## Nguồn đã đọc
- `AGENTS.md`, `.claude/CLAUDE.md`, `.claude/context/current-state.md`
- `.claude/skills/02-ai-extraction/SKILL.md`
- `utils/ai_extractor.py`, `utils/ai_response_parser.py`, `utils/ai_reliability.py`
- `utils/ai_workspace.py`, `ui/ai_companion.py`, `workers/ai_workers.py`

## Bất biến và rủi ro
- Candidate mode chỉ thuộc Forge language workflow và bắt buộc có source.
- `surface` và `source_excerpt` phải có trong source; output truncated/mơ hồ/prose bị từ chối.
- Deck surface match chỉ advisory vì cùng mặt chữ có thể khác nghĩa.
- Reviewer không nhận candidate mode; artifact/Xưởng/SRS giữ contract hiện hành.

## Kế hoạch tối thiểu
1. Pure candidate schema/prompt/parser/provenance tests.
2. AI orchestration + worker candidate mode với cancellation/usage hiện hành.
3. Forge selection table; selected rows → explicit Card Mode draft.
4. Deck surface advisory, docs/changelog, targeted/full verification.

## Acceptance criteria
- [x] Candidate JSON bám source và fail-closed khi malformed/truncated.
- [x] Chỉ candidate đã chọn đi vào Card Mode request.
- [x] Deck match hiển thị advisory, không tự loại nghĩa khác.
- [x] Reviewer/Forge role split và artifact zero-AI không regression.
- [x] Targeted/full tests và compile xanh; GUI smoke profile backup còn là release gate.

## Handoff / kết quả
- Quyết định: Local implementation xanh; chưa đánh dấu verified/released cho đến khi có GUI smoke trên profile backup và CI.
- Files đã đổi: candidate schema/parser/orchestrator, AI worker/workflow, Forge selection UI, Factory current-deck advisory, i18n, tests và tài liệu trạng thái.
- Kiểm chứng đã chạy và kết quả: targeted `150 passed`; gate line budget `ai_extractor.py=1599`; isolated suite hai vòng `751 passed`; release docs `9 passed`; compile toàn bộ Python và `git diff --check` xanh.
- Còn lại / blocker: GUI smoke Anki trên profile đã backup.
