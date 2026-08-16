# AGENTS.md — Bento Forge

> Điểm vào duy nhất cho mọi AI agent. Không dùng `CODE_MAP.md` hoặc `UPGRADE_GUIDE.md` để ra quyết định kỹ thuật.

## Quy trình bắt buộc

1. Đọc [`.claude/CLAUDE.md`](.claude/CLAUDE.md) để biết luật vàng và routing.
2. Đọc [`.claude/context/current-state.md`](.claude/context/current-state.md) để biết trạng thái đã kiểm chứng và task đang mở.
3. Chọn **đúng một** skill trong `.claude/skills/` theo phạm vi task.
4. Dùng `rg` để định vị symbol, rồi chỉ đọc đoạn `file:line` mà skill hoặc kết quả tìm kiếm xác nhận.
5. Trước khi sửa, nêu phạm vi, bất biến và tiêu chí hoàn tất. Sau khi sửa, xem diff và chạy kiểm chứng theo skill 10.

Không nạp toàn bộ repo, roadmap lịch sử, benchmark hay chat history vào context mặc định. Dùng [task contract template](.claude/context/task-contract-template.md) để chuyển giao giữa các lượt agent.

## Routing nhanh

| Việc cần làm | Skill |
|---|---|
| Hiểu cấu trúc hoặc tìm ownership | `.claude/skills/01-project-map/SKILL.md` |
| AI, prompt, cache, cost | `.claude/skills/02-ai-extraction/SKILL.md` |
| Batch hoặc tổ chức deck | `.claude/skills/03-batch-processing/SKILL.md` |
| Audio/TTS | `.claude/skills/04-audio-tts/SKILL.md` |
| Worker hoặc luồng nền | `.claude/skills/05-workers/SKILL.md` |
| UI, theme, i18n | `.claude/skills/06-ui-layer/SKILL.md` |
| Ngôn ngữ hoặc cấu hình field | `.claude/skills/07-language-config/SKILL.md` |
| Template thẻ, CSS hoặc JS | `.claude/skills/08-card-templates/SKILL.md` |
| Parser, logger, cache utility | `.claude/skills/09-utils/SKILL.md` |
| Viết hoặc chạy test | `.claude/skills/10-testing/SKILL.md` |
| Version, build hoặc release | `.claude/skills/11-upgrade-playbook/SKILL.md` |
| Debug từ log hoặc tái hiện lỗi | `.claude/skills/12-debugging/SKILL.md` |
| Learning Modes / Knowledge beta | `.claude/skills/13-learning-modes/SKILL.md` |

## Nguồn chuẩn

- Trạng thái, version, gate và backlog đang hoạt động: [`work_items/PERSONAL_ROADMAP.md`](work_items/PERSONAL_ROADMAP.md).
- Bằng chứng benchmark: [`benchmarks/`](benchmarks/).
- Quyết định/lịch sử đã đóng: [`work_items/history/`](work_items/history/) và tài liệu có `Authority: historical`.
- Bản đồ kỹ thuật cho agent: skill 01; overview cho người đọc: [`docs/architecture.md`](docs/architecture.md).
