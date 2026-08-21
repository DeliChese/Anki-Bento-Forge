# 🤖 CLAUDE.md — Bento Forge

> Add-on Anki (Python/PyQt5) tạo thẻ từ vựng Nhật, Trung & Hàn với AI + TTS + interactive templates.

## 🎯 CÁCH DÙNG HỆ THỐNG NÀY (TIẾT KIỆM TOKEN)

Nguyên tắc **progressive disclosure**: KHÔNG đọc toàn bộ source. Chỉ đọc 1 skill liên quan + nhảy thẳng tới dòng cần sửa (line number trong skill).

```
Bước 1: Đọc file này và `.claude/context/current-state.md`
Bước 2: Chọn ĐÚNG 1 skill dưới đây theo việc cần làm
Bước 3: Trong skill, dùng `rg` và `file:line` để đọc ĐÚNG đoạn code cần
Bước 4: Chạy tests liên quan (xem skill 10)
```

## 🧩 INDEX SKILLS

| # | Skill | Dùng khi | Token |
|---|-------|----------|-------|
| 01 | project-map | Mới vào dự án, cần hiểu cấu trúc/dependency | ~1.2k |
| 02 | ai-extraction | Sửa AI extract/chat/prompt/cache/cost | ~1.5k |
| 03 | batch-processing | Sửa batch/xử lý danh sách lớn/tổ chức deck | ~1.2k |
| 04 | audio-tts | Sửa giọng đọc/audio/speed | ~1.0k |
| 05 | workers | Sửa thread/signal/tương tác nền | ~1.0k |
| 06 | ui-layer | Sửa dialog/theme/i18n UI | ~1.2k |
| 07 | language-config | Thêm/sửa ngôn ngữ, field, model name | ~1.0k |
| 08 | card-templates | Sửa HTML/CSS/JS của thẻ | ~1.3k |
| 09 | utils | Sửa json_parser/logger/i18n/deck_cache | ~1.0k |
| 10 | testing | Chạy/viết test, verify sau khi sửa | ~1.0k |
| 11 | upgrade-playbook | Nâng cấp version, bảo trì, release | ~1.2k |
| 12 | debugging | 🐞 Tìm/sửa BUG: đọc log, root cause, catalogue lỗi | ~0.5k |
| 13 | learning-modes | V18: tách/chuyển Language ↔ Knowledge, schema, model, UI và workflow an toàn | ~1.5k |

## 🧭 SƠ ĐỒ TỔNG QUAN (TỐI GIẢN)

```
__init__.py (26 dòng)         ← compatibility facade (public re-export)
├── ui/factory_dialog.py      ← AnkiSmartFactory QDialog + Qt/Anki orchestration (MAIN)
├── Language/    LANG_CONFIG, LANG_GRAMMAR_CONFIG, LANG_SELECTOR_INFO  (japanese, chinese, korean, english)
├── mode/        LANG_TEMPLATES, LANG_CSS, LANG_GRAMMAR_*, card_render.py, shared.py (JS)
├── audio/       engine.py (router) + tts.py (Edge/gTTS/VoiceVox)
├── utils/       ai_extractor, ai_workspace, ai_prompt_defaults, ai_response_parser, ai_result_cache, import_history, batch_processor, prompt_config, deck_cache, json_parser, logger, i18n, deck_manager
├── workers/     ImportWorker, PreviewThread, AiExtractThread, AiChatThread, DeckScanWorker, BatchProcessThread, DeckOrganizerThread
├── ui/          AiChatDialog, ai_settings, ai_preview, batch_dialog, verify_dialog, history_dialog, prompt_editor, theme
├── hooks/       reviewer.py (register_hooks) + overview_mode.py (mode selector)
└── tests/       regression suite; số liệu đã kiểm chứng nằm trong `context/current-state.md`
```

## 🔒 QUY TẮC VÀNG (BẮT BUỘC)

1. **Đọc skill trước, đọc source sau** — không mở file 2000 dòng vô tội vạ.
2. **`file:line` là chân lý** — mọi line number trong skill đã được xác minh; nếu code thay đổi, cập nhật line number trong skill.
3. **Không import Anki modules (aqt) trong domain module thuần** — direct integration chỉ thuộc `ui/`, `workers/`, `hooks/` hoặc adapter Anki có chủ đích.
4. **Mọi UI đều qua i18n `t()`** — không hardcode string tiếng Việt trong UI.
5. **Mọi log qua `get_logger()`** — không dùng `print()`.
6. **Bare `except:` cấm** — luôn `except Exception:` + log.
7. **Thread-safe cho mọi state chia sẻ** — dùng `threading.Lock` (xem audio/engine.py làm mẫu).
8. **Không commit `utils/ai_config.json`** (API key mã hóa) — chỉ commit `.example`.
9. **Sửa prompt → Bump `_PROMPT_VERSION`** trong `utils/ai_extractor.py:503` để invalidate cache.
10. **Thay đổi có thể phát hành phải cập nhật `CHANGELOG.md` trong cùng thay đổi** — ghi vào mục ngày hiện tại trong `[Unreleased]` theo `CHANGELOG_POLICY.md`, kèm snapshot version đầu/cuối ngày; không ghi roadmap hoặc kết quả chưa được kiểm chứng như tính năng đã hoàn tất.
11. **Sau khi sửa → chạy pytest** (skill 10) trước khi báo xong.

## 🏷️ NGÔN NGỮ & THUẬT NGỮ

- `vocab` = chế độ Từ vựng; `grammar` = chế độ Ngữ pháp (Note Type riêng).
- `lang` = `"japanese"` | `"chinese"` | `"korean"` | `"english"`.
- Model names: `"AnkiTool Japanese/Chinese/Korean/English [Grammar] V18.1 (Add-on)"`; V17.0 được giữ trong `old_model_names` để migration không mất note/SRS.
- Entry: `start_smart_factory()` (`ui/factory_dialog.py:2801`, re-export tại `__init__.py`), shortcut `Ctrl+Shift+I`. Menu Tools hiển thị **"🧪 Bento Forge"**.
- Version, compatibility, test gate và trạng thái V18: xem `.claude/context/current-state.md` và `work_items/PERSONAL_ROADMAP.md`; không sao chép số liệu động vào file này.
- **Combo mode**: mỗi từ = 1 card duy nhất, 5 chế độ (qa/vn/wb/pron/lg) chuyển đổi trong card qua `_COMBO_MODE_JS`; mode lưu `mw.col.conf["ai_factory_study_mode"]`; Overview patch qua `hooks/overview_mode.py`.
- **Prompt/Schema/Field Map/Card Render có thể GHI ĐÈ ngoài**: `utils/ai_prompts.json` (gitignored) qua `utils/prompt_config.py` + `mode/card_render.py` — xem skill 02 (ai-extraction) và 08 (card-templates).

---

*Hệ thống skill này thay thế CODE_MAP.md/UPGRADE_GUIDE.md cũ (đã lỗi thời). Chi tiết từng module nằm trong `.claude/skills/`.*
