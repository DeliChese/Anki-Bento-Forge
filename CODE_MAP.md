# 🗺️ CODE_MAP — (DEPRECATED)

> ⚠️ **Tài liệu này ĐÃ LỖI THỜI** — mô tả cấu trúc monolith cũ (trước khi tách `workers/`, `ui/`, `hooks/`) với số dòng và tên cũ đã hết giá trị.
> **Đừng dùng nội dung bên dưới.** Dùng hệ thống skill làm nguồn chính thức (đọc theo progressive disclosure):

| Cần gì | Đọc |
|---|---|
| Điểm vào cho AI | [`AGENTS.md`](AGENTS.md) |
| Luật vàng + index skills | [`.claude/CLAUDE.md`](.claude/CLAUDE.md) |
| Bản đồ dự án chi tiết | [`.claude/skills/01-project-map/SKILL.md`](.claude/skills/01-project-map/SKILL.md) |

## Cấu trúc hiện tại (tóm tắt 3 dòng)

`Bento Forge/` — Xưởng chế tạo thẻ (Nhật–Trung–Hàn), **444 test (36 file)**:
- `__init__.py` (~26 dòng) — compatibility facade; re-export API công khai.
- `ui/factory_dialog.py` (~2.8k dòng) — `AnkiSmartFactory` main dialog, entry `start_smart_factory()`.
- `Language/` · `mode/` · `audio/` · `utils/` · `workers/` · `ui/` · `hooks/` — xem `.claude/skills/01-project-map`.
- Tích hợp vào **Bento Station AIOS** qua `bento_forge_bridge.py` (1 chiều, lazy import).
